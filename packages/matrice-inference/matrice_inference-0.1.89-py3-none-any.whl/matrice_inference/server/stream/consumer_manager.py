"""
Single async event loop consumer manager for 1000 cameras.

Architecture:
- Single async event loop handles all 1000 camera streams
- Async Redis/Kafka operations (non-blocking)
- Direct frame bytes extraction and forwarding
- No codec-specific processing (simplified)
- No frame caching (moved to producer)
- Backpressure handling (drop frames if queue full)
"""

import asyncio
import base64
import logging
import time
import uuid
from typing import Dict, Any, Optional
from matrice_inference.server.stream.utils import CameraConfig, StreamMessage
from matrice_inference.server.stream.worker_metrics import WorkerMetrics


class AsyncConsumerManager:
    """
    Manages 1000 camera streams with single async event loop.

    Key Features:
    - Single event loop for all cameras (not 1000 threads)
    - Async stream reads (non-blocking)
    - Direct bytes extraction (no codec processing)
    - Backpressure handling (drop frames if queue full)
    - Dynamic camera add/remove support
    - Unique consumer groups per app deployment (multi-app support)
    - Automatic stream recovery on NOGROUP errors with exponential backoff
    """

    # Retry configuration for stream recovery
    STREAM_ERROR_MAX_RETRIES = 5  # Maximum retries before giving up on a camera
    STREAM_ERROR_INITIAL_BACKOFF = 1.0  # Initial backoff in seconds
    STREAM_ERROR_MAX_BACKOFF = 60.0  # Maximum backoff in seconds
    STREAM_ERROR_BACKOFF_MULTIPLIER = 2.0  # Exponential backoff multiplier
    SUCCESS_THRESHOLD = 5  # Reset retry state after this many consecutive successes

    def __init__(
        self,
        camera_configs: Dict[str, CameraConfig],
        stream_config: Dict[str, Any],
        app_deployment_id: str,
        pipeline: Any,
        message_timeout: float = 2.0,
    ):
        self.camera_configs = camera_configs
        self.stream_config = stream_config
        self.pipeline = pipeline
        self.message_timeout = message_timeout
        self.running = False

        # Camera streams (one per camera)
        self.streams: Dict[str, Any] = {}

        # Async tasks (one per camera)
        self.consumer_tasks: Dict[str, asyncio.Task] = {}

        # Initialize metrics (shared across all cameras)
        self.metrics = WorkerMetrics.get_shared("consumer")

        # Generate unique app instance identifier for consumer groups
        # This ensures multiple apps consuming the same camera stream each get ALL frames
        self.app_deployment_id = app_deployment_id

        self.logger = logging.getLogger(f"{__name__}.AsyncConsumerManager")

        # Stream error recovery state tracking (per camera)
        self._stream_retry_counts: Dict[str, int] = {}  # camera_id -> retry count
        self._stream_backoff_times: Dict[str, float] = {}  # camera_id -> current backoff

    async def start(self):
        """Start async consumers for all cameras."""
        self.running = True
        self.metrics.mark_active()

        self.logger.info(
            f"Starting async consumer manager for {len(self.camera_configs)} cameras "
            f"(app_deployment_id={self.app_deployment_id})"
        )

        # Initialize streams for all cameras
        await self._initialize_streams()

        # Create async task for each camera
        for camera_id, config in self.camera_configs.items():
            await self.add_camera(camera_id, config)

        self.logger.info(f"Created {len(self.consumer_tasks)} async camera consumers")

    async def stop(self):
        """Stop all consumers."""
        self.running = False
        self.metrics.mark_inactive()

        # Cancel all consumer tasks
        for task in self.consumer_tasks.values():
            task.cancel()

        # Wait for tasks to complete
        if self.consumer_tasks:
            await asyncio.gather(*self.consumer_tasks.values(), return_exceptions=True)

        # Close all streams
        for stream in self.streams.values():
            try:
                await stream.async_close()
            except Exception:
                pass

        self.logger.info("Stopped async consumer manager")

    async def add_camera(self, camera_id: str, config: CameraConfig):
        """
        Add a new camera dynamically.

        Args:
            camera_id: Unique camera identifier
            config: Camera configuration
        """
        if camera_id in self.consumer_tasks:
            self.logger.warning(f"Camera {camera_id} already exists, skipping add")
            return

        try:
            # Initialize stream if not exists
            if camera_id not in self.streams:
                await self._initialize_camera_stream(camera_id)

            # Create async task for this camera
            task = asyncio.create_task(
                self._consume_camera(camera_id, config),
                name=f"consumer_{camera_id}"
            )
            self.consumer_tasks[camera_id] = task

            self.logger.info(f"Added camera {camera_id} to consumer manager")

        except Exception as e:
            self.logger.error(f"Failed to add camera {camera_id}: {e}")

    async def remove_camera(self, camera_id: str):
        """
        Remove a camera dynamically.

        Args:
            camera_id: Unique camera identifier
        """
        if camera_id not in self.consumer_tasks:
            self.logger.warning(f"Camera {camera_id} not found, skipping remove")
            return

        try:
            # Cancel the task
            task = self.consumer_tasks[camera_id]
            task.cancel()

            # Wait for task to complete
            try:
                await asyncio.wait_for(task, timeout=5.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

            # Remove from tasks dict
            del self.consumer_tasks[camera_id]

            # Close and remove stream
            if camera_id in self.streams:
                try:
                    await self.streams[camera_id].async_close()
                except Exception:
                    pass
                del self.streams[camera_id]

            self.logger.info(f"Removed camera {camera_id} from consumer manager")

        except Exception as e:
            self.logger.error(f"Failed to remove camera {camera_id}: {e}")

    async def _initialize_streams(self):
        """Initialize streams for all cameras."""
        from matrice_common.stream.matrice_stream import MatriceStream, StreamType

        stream_type = self._get_stream_type()
        stream_params = self._build_stream_params(stream_type)

        for camera_id, camera_config in self.camera_configs.items():
            try:
                stream = MatriceStream(stream_type, **stream_params)
                # CRITICAL: Include app instance ID to ensure each app gets ALL frames
                # Without this, multiple apps share a consumer group and split frames
                consumer_group = f"inference_{self.app_deployment_id}_{camera_id}"
                # Use camera-specific input topic (not shared input_topic)
                camera_input_topic = camera_config.input_topic
                await stream.async_setup(camera_input_topic, consumer_group)

                self.streams[camera_id] = stream

                self.logger.info(
                    f"✓ Initialized stream for camera {camera_id} on topic {camera_input_topic} "
                    f"(consumer_group={consumer_group})"
                )

            except Exception as e:
                self.logger.error(f"Failed to initialize stream for camera {camera_id}: {e}")

    async def _initialize_camera_stream(self, camera_id: str):
        """Initialize stream for a single camera."""
        from matrice_common.stream.matrice_stream import MatriceStream, StreamType

        stream_type = self._get_stream_type()
        stream_params = self._build_stream_params(stream_type)

        try:
            # Get camera-specific input topic
            camera_config = self.camera_configs.get(camera_id)
            if not camera_config:
                raise ValueError(f"No config found for camera {camera_id}")

            stream = MatriceStream(stream_type, **stream_params)
            # CRITICAL: Include app instance ID to ensure each app gets ALL frames
            # Without this, multiple apps share a consumer group and split frames
            consumer_group = f"inference_{self.app_deployment_id}_{camera_id}"
            # Use camera-specific input topic (not shared input_topic)
            camera_input_topic = camera_config.input_topic
            await stream.async_setup(camera_input_topic, consumer_group)

            self.streams[camera_id] = stream

            self.logger.info(
                f"✓ Initialized stream for camera {camera_id} on topic {camera_input_topic} "
                f"(consumer_group={consumer_group})"
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize stream for camera {camera_id}: {e}")
            raise

    def _get_stream_type(self):
        """Determine stream type from configuration."""
        from matrice_common.stream.matrice_stream import StreamType
        stream_type_str = self.stream_config.get("stream_type", "kafka").lower()
        return StreamType.KAFKA if stream_type_str == "kafka" else StreamType.REDIS

    def _build_stream_params(self, stream_type) -> Dict[str, Any]:
        """Build stream parameters based on type."""
        from matrice_common.stream.matrice_stream import StreamType

        if stream_type == StreamType.KAFKA:
            return {
                "bootstrap_servers": self.stream_config.get("bootstrap_servers", "localhost:9092"),
                "sasl_username": self.stream_config.get("sasl_username", "matrice-sdk-user"),
                "sasl_password": self.stream_config.get("sasl_password", "matrice-sdk-password"),
                "sasl_mechanism": self.stream_config.get("sasl_mechanism", "SCRAM-SHA-256"),
                "security_protocol": self.stream_config.get("security_protocol", "SASL_PLAINTEXT"),
            }
        else:
            return {
                "host": self.stream_config.get("host") or "localhost",
                "port": self.stream_config.get("port") or 6379,
                "password": self.stream_config.get("password"),
                "username": self.stream_config.get("username"),
                "db": self.stream_config.get("db", 0),
                "connection_timeout": self.stream_config.get("connection_timeout", 120),
            }

    def _is_stream_recoverable_error(self, error: Exception) -> bool:
        """Check if the error is a recoverable stream/consumer group error.

        Args:
            error: The exception to check

        Returns:
            True if this is a recoverable stream error (NOGROUP, no such key, etc.)
        """
        error_str = str(error).lower()

        # Check for Redis stream-specific errors
        recoverable_patterns = [
            "nogroup",          # Consumer group doesn't exist
            "no such key",      # Stream doesn't exist
            "busygroup",        # Consumer group creation conflict (harmless, retry)
            "stream not found", # Alternative error message
            "consumer group",   # Generic consumer group issues
        ]

        for pattern in recoverable_patterns:
            if pattern in error_str:
                return True

        return False

    async def _reinitialize_camera_stream(self, camera_id: str) -> bool:
        """Attempt to re-initialize a camera stream after a recoverable error.

        This closes any existing stream and creates a fresh one.

        Args:
            camera_id: The camera ID to reinitialize

        Returns:
            True if reinitialization succeeded, False otherwise
        """
        self.logger.info(f"Attempting to reinitialize stream for camera {camera_id}")

        try:
            # Close existing stream if present
            if camera_id in self.streams:
                try:
                    old_stream = self.streams[camera_id]
                    await old_stream.async_close()
                    self.logger.debug(f"Closed old stream for camera {camera_id}")
                except Exception as close_error:
                    self.logger.warning(
                        f"Error closing old stream for camera {camera_id}: {close_error}"
                    )
                finally:
                    # Always remove from dict regardless of close success
                    del self.streams[camera_id]

            # Reinitialize the stream
            await self._initialize_camera_stream(camera_id)

            self.logger.info(f"Successfully reinitialized stream for camera {camera_id}")
            return True

        except Exception as e:
            self.logger.error(
                f"Failed to reinitialize stream for camera {camera_id}: {e}"
            )
            return False

    def _get_stream_backoff(self, camera_id: str) -> float:
        """Get the current backoff time for a camera, initializing if needed."""
        if camera_id not in self._stream_backoff_times:
            self._stream_backoff_times[camera_id] = self.STREAM_ERROR_INITIAL_BACKOFF
        return self._stream_backoff_times[camera_id]

    def _increase_stream_backoff(self, camera_id: str) -> float:
        """Increase and return the backoff time for a camera using exponential backoff."""
        current = self._get_stream_backoff(camera_id)
        new_backoff = min(
            current * self.STREAM_ERROR_BACKOFF_MULTIPLIER,
            self.STREAM_ERROR_MAX_BACKOFF
        )
        self._stream_backoff_times[camera_id] = new_backoff
        return new_backoff

    def _reset_stream_recovery_state(self, camera_id: str) -> None:
        """Reset retry count and backoff for a camera after successful operation."""
        if camera_id in self._stream_retry_counts:
            del self._stream_retry_counts[camera_id]
        if camera_id in self._stream_backoff_times:
            del self._stream_backoff_times[camera_id]

    async def _consume_camera(self, camera_id: str, config: CameraConfig):
        """
        Async consumer for single camera with robust error recovery.

        This runs concurrently with all other camera consumers in the same event loop.
        Each camera has its own async while loop for continuous frame processing.

        Features:
        - Detects stream/consumer group errors (NOGROUP, no such key)
        - Automatically reinitializes streams on recoverable errors
        - Uses exponential backoff to avoid hammering Redis
        - Gives up after max retries to prevent infinite loops
        """
        stream = self.streams.get(camera_id)
        if not stream:
            self.logger.error(f"No stream for camera {camera_id}")
            return

        self.logger.info(f"Started consumer for camera {camera_id}")

        # Track consecutive successes to reset retry state
        consecutive_successes = 0

        while self.running and config.enabled:
            try:
                # Non-blocking stream read
                message_data = await stream.async_get_message(self.message_timeout)

                if message_data:
                    # Process message - simplified to just extract bytes and forward
                    await self._process_message(camera_id, config, message_data)

                    # Track success and reset recovery state after stable operation
                    consecutive_successes += 1
                    if consecutive_successes >= self.SUCCESS_THRESHOLD:
                        self._reset_stream_recovery_state(camera_id)
                        consecutive_successes = 0  # Reset counter
                # message_data is None means timeout, which is normal - continue loop

            except asyncio.CancelledError:
                # Task cancellation - exit gracefully
                break

            except Exception as e:
                consecutive_successes = 0  # Reset on any error

                # Check if this is a recoverable stream error
                if self._is_stream_recoverable_error(e):
                    # Get current retry count
                    retry_count = self._stream_retry_counts.get(camera_id, 0)

                    if retry_count >= self.STREAM_ERROR_MAX_RETRIES:
                        self.logger.error(
                            f"Camera {camera_id}: Max retries ({self.STREAM_ERROR_MAX_RETRIES}) "
                            f"exceeded for stream errors. Stopping consumer. "
                            f"Last error: {e}"
                        )
                        # Remove from streams to signal permanent failure
                        if camera_id in self.streams:
                            try:
                                await self.streams[camera_id].async_close()
                            except Exception:
                                pass
                            del self.streams[camera_id]
                        break  # Exit the consumer loop

                    # Increment retry count
                    self._stream_retry_counts[camera_id] = retry_count + 1
                    current_retry = retry_count + 1

                    # Calculate backoff
                    backoff = self._get_stream_backoff(camera_id)

                    self.logger.warning(
                        f"Camera {camera_id}: Recoverable stream error detected "
                        f"(attempt {current_retry}/{self.STREAM_ERROR_MAX_RETRIES}). "
                        f"Error: {e}. "
                        f"Will attempt reinitialize after {backoff:.1f}s backoff."
                    )

                    # Wait with backoff before retry
                    await asyncio.sleep(backoff)

                    # Attempt to reinitialize the stream
                    if await self._reinitialize_camera_stream(camera_id):
                        # Update stream reference for next iteration
                        stream = self.streams.get(camera_id)
                        if stream:
                            self.logger.info(
                                f"Camera {camera_id}: Stream reinitialized successfully. "
                                f"Resuming consumption."
                            )
                            # Increase backoff for next potential failure
                            self._increase_stream_backoff(camera_id)
                        else:
                            self.logger.error(
                                f"Camera {camera_id}: Stream reference lost after reinitialize"
                            )
                            break
                    else:
                        # Reinitialization failed - increase backoff and retry
                        self._increase_stream_backoff(camera_id)
                        self.logger.warning(
                            f"Camera {camera_id}: Stream reinitialize failed. "
                            f"Will retry with increased backoff."
                        )
                else:
                    # Non-recoverable error - log and use standard backoff
                    self.logger.error(f"Error consuming camera {camera_id}: {e}")
                    await asyncio.sleep(1.0)

        self.logger.info(f"Stopped consumer for camera {camera_id}")

    async def _process_message(
        self,
        camera_id: str,
        camera_config: CameraConfig,
        message_data: Dict[str, Any]
    ):
        """
        Process incoming message and enqueue for inference.

        Simply extracts and forwards frame data - no special handling needed.
        Inference worker will check for cached_frame_id in input_stream if present.
        """
        start_time = time.time()
        try:
            # Extract basic metadata
            message_key = self._extract_message_key(message_data)
            data = self._parse_message_data(message_data)

            # Reconstruct input_stream with binary content from flattened Redis fields
            input_stream = self._reconstruct_input_stream_content(data)
            extra_params = self._normalize_extra_params(data)
            frame_id = self._determine_frame_id(data, message_data, camera_id)

            # CRITICAL: Skip frame if frame_id is missing - error already logged
            if frame_id is None:
                return

            # Enrich input_stream with frame_id
            self._enrich_input_stream(input_stream, frame_id)

            # Extract frame bytes (may be empty for cached frames)
            frame_bytes = self._extract_frame_bytes(input_stream)

            # Create stream message
            stream_msg = self._create_stream_message(camera_id, message_key, data)

            # Build task data with simplified structure
            # Frame bytes might be empty for cached frames - that's OK!
            # Inference worker will handle it by checking input_stream["cached_frame_id"]
            task_data = {
                "camera_id": camera_id,
                "frame_bytes": frame_bytes,  # May be None/empty for cached frames
                "frame_id": frame_id,
                "message": stream_msg,
                "input_stream": input_stream,  # Contains cached_frame_id if present
                "stream_key": camera_id,
                "extra_params": extra_params,
                "camera_config": camera_config,
            }

            # Enqueue directly to inference queue
            await self._enqueue_task(camera_id, task_data)

            # Record metrics for successfully processed message
            latency_ms = (time.time() - start_time) * 1000
            self.metrics.record_latency(latency_ms)
            self.metrics.record_throughput(count=1)

        except Exception as e:
            self.logger.error(f"Error processing message for camera {camera_id}: {e}")

    def _extract_frame_bytes(self, input_stream: Dict[str, Any]) -> Optional[bytes]:
        """
        Extract frame bytes from input_stream.

        Handles both raw bytes and base64-encoded strings.
        Also handles Redis flattened format where binary content is in 'input_stream__content'.
        """
        if not isinstance(input_stream, dict):
            return None

        content = input_stream.get("content")

        # Handle raw bytes
        if isinstance(content, bytes) and content:
            return content

        # Handle base64-encoded strings
        elif isinstance(content, str) and content:
            try:
                return base64.b64decode(content)
            except Exception as e:
                self.logger.warning(f"Failed to decode base64 content: {e}")
                return None

        return None

    def _reconstruct_input_stream_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reconstruct input_stream with binary content and stream_info from flattened Redis fields.

        Redis stores binary content separately as 'input_stream__content'.
        Redis may also flatten nested dicts like 'input_stream__stream_info'.
        This method reconstructs them back into 'input_stream.content' and 'input_stream.stream_info'.
        """
        input_stream = data.get("input_stream", {})
        if not isinstance(input_stream, dict):
            input_stream = {}

        # Check for flattened binary content field
        if "input_stream__content" in data:
            binary_content = data["input_stream__content"]
            if isinstance(binary_content, bytes):
                # Reconstruct: put binary content back into input_stream
                input_stream["content"] = binary_content

        # CRITICAL: Reconstruct stream_info from flattened format or top-level data
        # Priority 1: Already in input_stream (nested structure preserved)
        self.logger.debug(f"input_streamii: {input_stream.get("stream_info","EMPTY-STREAM_INFO")}")
        if "stream_info" not in input_stream or not input_stream.get("stream_info"):
            # Priority 2: Flattened Redis format (input_stream__stream_info)
            if "input_stream__stream_info" in data:
                flattened_stream_info = data["input_stream__stream_info"]
                if isinstance(flattened_stream_info, dict):
                    input_stream["stream_info"] = flattened_stream_info
                elif isinstance(flattened_stream_info, str):
                    # May be JSON string - try to parse
                    try:
                        import json
                        input_stream["stream_info"] = json.loads(flattened_stream_info)
                    except Exception:
                        pass

            # Priority 3: stream_info at top level of data dict
            elif "stream_info" in data:
                top_level_stream_info = data["stream_info"]
                if isinstance(top_level_stream_info, dict):
                    input_stream["stream_info"] = top_level_stream_info
                elif isinstance(top_level_stream_info, str):
                    # May be JSON string - try to parse
                    try:
                        import json
                        input_stream["stream_info"] = json.loads(top_level_stream_info)
                    except Exception:
                        pass

        # Ensure stream_info is at least an empty dict
        if "stream_info" not in input_stream:
            input_stream["stream_info"] = {}

        return input_stream

    async def _enqueue_task(self, camera_id: str, task_data: Dict[str, Any]):
        """
        Enqueue task for inference with camera-based routing to specific worker queue.

        Routes frame to worker queue based on hash(camera_id) % num_workers.
        This ensures:
        - Same camera always goes to same worker queue
        - Frames are processed in FIFO order within each queue
        - No re-queuing → No race conditions → Order preserved per camera
        """
        try:
            # Get per-worker inference queues from pipeline
            inference_queues = self.pipeline.inference_queues

            if not inference_queues:
                self.logger.error("No inference queues available")
                return

            # Route to specific worker queue based on camera hash
            worker_id = hash(camera_id) % len(inference_queues)
            target_queue = inference_queues[worker_id]

            # Check shutdown flag before using executor to avoid "cannot schedule new futures" error
            if not self.running:
                self.logger.debug(f"Skipping frame for camera {camera_id}: shutdown in progress")
                return

            # Run blocking mp.Queue.put() in executor to avoid blocking event loop
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,  # Use default executor
                target_queue.put,
                task_data,
                True,  # block=True
                1.0  # timeout (seconds)
            )

            self.logger.debug(
                f"Routed frame for camera {camera_id} to inference worker {worker_id} "
                f"(queue size: {target_queue.qsize()})"
            )

        except Exception as e:
            # Queue full or other error - drop frame with backpressure
            error_msg = str(e)
            if "cannot schedule new futures" in error_msg or "shutdown" in error_msg.lower():
                self.logger.debug(f"Frame skipped for camera {camera_id} during shutdown: {e}")
            else:
                self.logger.warning(f"Dropped frame for camera {camera_id}: {e}")

    # Helper methods
    def _extract_message_key(self, message_data: Dict[str, Any]) -> str:
        """Extract message key."""
        return message_data.get("key", "")

    def _parse_message_data(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse message data."""
        return message_data.get("data", {})

    def _extract_input_stream(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract input_stream from data."""
        input_stream = data.get("input_stream", {})
        if not isinstance(input_stream, dict):
            input_stream = {}
        return input_stream

    def _normalize_extra_params(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize extra_params."""
        extra_params = data.get("extra_params", {})
        if isinstance(extra_params, dict):
            return extra_params
        elif isinstance(extra_params, list):
            merged = {}
            for item in extra_params:
                if isinstance(item, dict):
                    merged.update(item)
            return merged
        return {}

    def _determine_frame_id(
        self,
        data: Dict[str, Any],
        message_data: Dict[str, Any],
        camera_id: str
    ) -> Optional[str]:
        """Extract frame_id from upstream message. Returns None if missing.

        CRITICAL: This method enforces that frame_id MUST come from the streaming gateway.
        No fallback ID generation - if frame_id is missing, the frame will be skipped.
        This ensures frame_id consistency across the entire pipeline (input → output topics).
        """
        frame_id = data.get("frame_id")

        if not frame_id:
            self.logger.error(
                f"[FRAME_ID_MISSING] camera={camera_id} - frame_id not found in message data. "
                f"Available keys: {list(data.keys())}. Skipping frame."
            )
            return None

        if not isinstance(frame_id, str):
            self.logger.error(
                f"[FRAME_ID_INVALID] camera={camera_id} - frame_id is not a string: "
                f"type={type(frame_id)}, value={frame_id}. Skipping frame."
            )
            return None

        return frame_id

    def _enrich_input_stream(self, input_stream: Dict[str, Any], frame_id: str):
        """Enrich input_stream with frame_id."""
        if isinstance(input_stream, dict):
            input_stream["frame_id"] = frame_id

    def _create_stream_message(self, camera_id: str, message_key: str, data: Dict[str, Any]) -> StreamMessage:
        """Create StreamMessage object."""
        from datetime import datetime

        # Get timestamp from data or use current time
        timestamp = data.get("timestamp")
        if not isinstance(timestamp, datetime):
            timestamp = datetime.now()

        return StreamMessage(
            camera_id=camera_id,
            message_key=message_key,
            data=data,
            timestamp=timestamp,
            priority=1,
        )
