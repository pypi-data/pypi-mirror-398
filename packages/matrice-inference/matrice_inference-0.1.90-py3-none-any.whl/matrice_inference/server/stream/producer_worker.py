import asyncio
import json
import logging
import queue
import threading
import time
from typing import Any, Dict, Optional

from matrice_common.stream.matrice_stream import MatriceStream
from matrice_inference.server.stream.utils import CameraConfig

from matrice_inference.server.stream.worker_metrics import WorkerMetrics


class ProducerWorker:
    """Handles message production to streams with per-camera queue handling."""

    DEFAULT_DB = 0

    def __init__(
        self,
        worker_id: int,
        output_queue: Any,  # multiprocessing.Queue
        pipeline: Any,
        camera_configs: Dict[str, CameraConfig],
        message_timeout: float,
        analytics_publisher: Optional[Any] = None,
        frame_cache: Optional[Any] = None,
        use_shared_metrics: Optional[bool] = True,
        app_deployment_id: Optional[str] = None,
    ):
        self.worker_id = worker_id
        self.output_queue = output_queue  # Shared mp.Queue from pipeline
        self.pipeline = pipeline
        self.camera_configs = camera_configs
        self.message_timeout = message_timeout
        self.analytics_publisher = analytics_publisher
        self.frame_cache = frame_cache
        self.app_deployment_id = app_deployment_id
        self.running = False
        self._analytics_warning_logged = False  # Only warn once about missing analytics_publisher
        self.producer_streams: Dict[str, MatriceStream] = {}
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        # self.metrics = WorkerMetrics( # ADD
        #     worker_id=f"producer_worker_{worker_id}",
        #     worker_type="producer"
        # )
        # self.metrics = WorkerMetrics.get_shared("producer")
        if use_shared_metrics:
            self.metrics = WorkerMetrics.get_shared("producer")
        else:
            self.metrics = WorkerMetrics(
                worker_id=f"producer_worker_{worker_id}",
                worker_type="producer"
            )

        self.logger = logging.getLogger(f"{__name__}.producer.{worker_id}")
    
    def start(self) -> threading.Thread:
        """Start the producer worker in a separate thread."""
        self.running = True
        self.metrics.mark_active()  # ADD
        thread = threading.Thread(
            target=self._run,
            name=f"ProducerWorker-{self.worker_id}",
            daemon=False
        )
        thread.start()
        return thread
    
    def stop(self):
        """Stop the producer worker."""
        self.running = False
        self.metrics.mark_inactive()  # ADD

    def remove_camera_stream(self, camera_id: str) -> bool:
        """Remove producer stream for a specific camera (thread-safe).

        This method can be called from any thread. It schedules the stream
        cleanup on the ProducerWorker's event loop using run_coroutine_threadsafe.

        Args:
            camera_id: ID of camera whose stream should be removed

        Returns:
            bool: True if successfully removed, False otherwise
        """
        try:
            if camera_id not in self.producer_streams:
                self.logger.warning(f"No producer stream found for camera {camera_id}")
                return False

            # Check if event loop is available
            if not self._event_loop or not self._event_loop.is_running():
                self.logger.warning(f"ProducerWorker event loop not available, cannot close stream for camera {camera_id}")
                # Still remove from dict to prevent memory leak
                if camera_id in self.producer_streams:
                    del self.producer_streams[camera_id]
                return False

            # Schedule the async close on the worker's event loop
            future = asyncio.run_coroutine_threadsafe(
                self._async_remove_camera_stream(camera_id),
                self._event_loop
            )

            # Wait for completion with timeout
            result = future.result(timeout=5.0)
            return result

        except Exception as e:
            self.logger.error(f"Error removing producer stream for camera {camera_id}: {e}")
            # Clean up dict entry even on error
            if camera_id in self.producer_streams:
                del self.producer_streams[camera_id]
            return False

    async def _async_remove_camera_stream(self, camera_id: str) -> bool:
        """Internal async method to close and remove a camera stream.

        Args:
            camera_id: ID of camera whose stream should be removed

        Returns:
            bool: True if successfully removed, False otherwise
        """
        try:
            if camera_id in self.producer_streams:
                stream = self.producer_streams[camera_id]
                await stream.async_close()
                del self.producer_streams[camera_id]
                self.logger.info(f"Removed producer stream for camera {camera_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error in async close for camera {camera_id}: {e}")
            # Clean up dict entry even on error
            if camera_id in self.producer_streams:
                del self.producer_streams[camera_id]
            return False

    def _run(self) -> None:
        """Main producer loop with proper resource management."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._event_loop = loop  # Store reference for cross-thread operations

        self.logger.info(f"Started producer worker {self.worker_id}")

        try:
            loop.run_until_complete(self._initialize_streams())
            self._process_messages(loop)
        except Exception as e:
            self.logger.error(f"Fatal error in producer worker: {e}")
        finally:
            self._cleanup_resources(loop)
            self._event_loop = None

    def _process_messages(self, loop: asyncio.AbstractEventLoop) -> None:
        """Main message processing loop (runs async tasks on event loop)."""
        loop.run_until_complete(self._async_process_messages())

    async def _async_process_messages(self) -> None:
        """Async message processing loop for handling asyncio queues."""
        while self.running:
            try:
                start_time = time.time()
                task = await self._get_task_from_queue()
                if task:
                    # Process task asynchronously
                    await self._send_message_safely(task)

                    # Record metrics after successful processing
                    latency_ms = (time.time() - start_time) * 1000
                    self.metrics.record_latency(latency_ms)
                    self.metrics.record_throughput(count=1)
                else:
                    # No task available, small sleep
                    await asyncio.sleep(0.001)
            except Exception as e:
                self.logger.error(f"Producer error: {e}")
                await asyncio.sleep(0.1)

    async def _get_task_from_queue(self) -> Optional[Dict[str, Any]]:
        """Get task from shared mp.Queue.

        Reads from shared multiprocessing.Queue using run_in_executor.

        Returns:
            Task data or None if no tasks available
        """
        try:
            # Read from shared mp.Queue (blocking operation in executor)
            loop = asyncio.get_running_loop()
            task_data = await loop.run_in_executor(
                None,  # Use default executor
                self.output_queue.get,
                True,  # block=True
                1.0  # timeout (seconds) - increased from 0.1s to reduce busy-waiting
            )
            return task_data
        except Exception as e:
            # Timeout or queue error
            return None

    def _cleanup_resources(self, loop: asyncio.AbstractEventLoop) -> None:
        """Clean up streams and event loop resources."""
        for stream in self.producer_streams.values():
            try:
                loop.run_until_complete(stream.async_close())
            except Exception as e:
                self.logger.error(f"Error closing producer stream: {e}")

        try:
            loop.close()
        except Exception as e:
            self.logger.error(f"Error closing event loop: {e}")

        self.logger.info(f"Producer worker {self.worker_id} stopped")

    async def _initialize_streams(self) -> None:
        """Initialize producer streams for all cameras with proper error handling."""
        try:
            from matrice_common.stream.matrice_stream import MatriceStream, StreamType

            for camera_id, camera_config in self.camera_configs.items():
                try:
                    await self._initialize_camera_stream(camera_id, camera_config, StreamType)
                except Exception as e:
                    self.logger.error(f"Failed to initialize producer stream for camera {camera_id}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Failed to initialize producer streams: {e}")
            raise

    async def _initialize_camera_stream(
        self, camera_id: str, camera_config: CameraConfig, StreamType: Any
    ) -> None:
        """Initialize producer stream for a single camera."""
        from matrice_common.stream.matrice_stream import MatriceStream

        stream_type = self._get_stream_type(camera_config.stream_config, StreamType)
        stream_params = self._build_stream_params(camera_config.stream_config, stream_type, StreamType)

        producer_stream = MatriceStream(stream_type, **stream_params)
        await producer_stream.async_setup(camera_config.output_topic)
        self.producer_streams[camera_id] = producer_stream

        self.logger.info(
            f"Initialized {stream_type.value} producer stream for camera {camera_id} in worker {self.worker_id}"
        )

    def _get_stream_type(self, stream_config: Dict[str, Any], StreamType: Any) -> Any:
        """Determine stream type from configuration."""
        stream_type_str = stream_config.get("stream_type", "kafka").lower()
        return StreamType.KAFKA if stream_type_str == "kafka" else StreamType.REDIS

    def _build_stream_params(self, stream_config: Dict[str, Any], stream_type: Any, StreamType: Any) -> Dict[str, Any]:
        """Build stream parameters based on type."""
        if stream_type == StreamType.KAFKA:
            return {
                "bootstrap_servers": stream_config.get("bootstrap_servers", "localhost:9092"),
                "sasl_username": stream_config.get("sasl_username", "matrice-sdk-user"),
                "sasl_password": stream_config.get("sasl_password", "matrice-sdk-password"),
                "sasl_mechanism": stream_config.get("sasl_mechanism", "SCRAM-SHA-256"),
                "security_protocol": stream_config.get("security_protocol", "SASL_PLAINTEXT"),
            }
        else:
            return {
                "host": stream_config.get("host") or "localhost",
                "port": stream_config.get("port") or 6379,
                "password": stream_config.get("password"),
                "username": stream_config.get("username"),
                "db": stream_config.get("db", self.DEFAULT_DB),
            }
    
    async def _send_message_safely(self, task_data: Dict[str, Any]) -> None:
        """Send message to the appropriate stream with validation and error handling.

        Also handles frame caching (moved from consumer to avoid blocking inference flow).
        """
        try:
            if not self._validate_task_data(task_data):
                return

            camera_id = task_data["camera_id"]
            frame_id = task_data.get("frame_id")

            # CRITICAL: Validate frame_id exists - skip if missing
            if not frame_id:
                self.logger.error(
                    f"[FRAME_ID_MISSING] camera={camera_id} - No frame_id in task_data. Skipping message."
                )
                return

            if not self._validate_camera_availability(camera_id):
                return

            # Log producer state for debugging
            self.logger.debug(
                f"[PRODUCER_PROCESSING] camera_id={camera_id}, frame_id={frame_id}, "
                f"has_frame_cache={self.frame_cache is not None}, "
                f"has_app_deployment_id={self.app_deployment_id is not None}, "
                f"app_deployment_id={self.app_deployment_id}"
            )

            # Cache frame asynchronously (non-blocking)
            await self._cache_frame_if_needed(task_data)

            # Store overlay results with composite key for multiple app support
            await self._store_overlay_results(task_data, camera_id, frame_id)

            await self._send_message_to_stream(task_data, camera_id)

        except Exception as e:
            self.logger.error(f"Error sending message: {e}", exc_info=True)

    async def _cache_frame_if_needed(self, task_data: Dict[str, Any]) -> None:
        """Cache frame to Redis asynchronously (moved from consumer).

        This caches the frame content to Redis for low-latency retrieval by clients.
        The frame_id is preserved throughout the pipeline for consistency.
        """
        frame_id = task_data.get("frame_id", "unknown")
        
        if not self.frame_cache:
            self.logger.debug(
                f"[FRAME_CACHE_SKIP] frame_id={frame_id} - frame_cache is None"
            )
            return

        try:
            if not frame_id or frame_id == "unknown":
                self.logger.warning(
                    f"[FRAME_CACHE_SKIP] No frame_id in task_data"
                )
                return

            # Get frame content from input_stream
            input_stream = task_data.get("input_stream", {})
            if not isinstance(input_stream, dict):
                self.logger.warning(
                    f"[FRAME_CACHE_SKIP] frame_id={frame_id} - input_stream is not a dict: {type(input_stream)}"
                )
                return

            content = input_stream.get("content")
            if not isinstance(content, bytes):
                self.logger.warning(
                    f"[FRAME_CACHE_SKIP] frame_id={frame_id} - content is not bytes: {type(content)}"
                )
                return
            
            if not content:
                self.logger.warning(
                    f"[FRAME_CACHE_SKIP] frame_id={frame_id} - content is empty"
                )
                return

            # Cache frame asynchronously (non-blocking)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,  # Use default executor
                self.frame_cache.put,
                frame_id,
                content
            )

            self.logger.debug(
                f"[FRAME_CACHE_OK] Cached frame: frame_id={frame_id}, size={len(content)} bytes"
            )

        except Exception as e:
            self.logger.error(f"[FRAME_CACHE_ERROR] frame_id={frame_id} - Failed to cache: {e}")

    def _make_json_serializable(self, obj: Any) -> Any:
        """Recursively convert non-JSON-serializable objects to serializable types.

        Handles:
        - Enum values (convert to string/value)
        - Objects with to_dict() method
        - Objects with __dict__ attribute
        - Dataclasses
        - bytes (convert to base64 string for JSON)
        - Custom objects (convert to string representation)
        """
        if obj is None:
            return None

        # Handle primitives
        if isinstance(obj, (str, int, float, bool)):
            return obj

        # Handle bytes - convert to base64 for JSON compatibility
        if isinstance(obj, bytes):
            import base64
            return base64.b64encode(obj).decode("ascii")

        # Handle Enum types (check before __dict__ since Enums have __dict__)
        if hasattr(obj, "value") and hasattr(obj, "name") and hasattr(obj, "__class__"):
            # Check if it's actually an Enum by checking if class has __members__
            if hasattr(obj.__class__, "__members__"):
                try:
                    return obj.value
                except Exception:
                    return str(obj)

        # Handle objects with to_dict() method
        if hasattr(obj, "to_dict") and callable(obj.to_dict):
            try:
                return self._make_json_serializable(obj.to_dict())
            except Exception:
                return str(obj)

        # Handle dataclasses
        if hasattr(obj, "__dataclass_fields__"):
            try:
                from dataclasses import asdict
                return self._make_json_serializable(asdict(obj))
            except Exception:
                return str(obj)

        # Handle dicts
        if isinstance(obj, dict):
            return {
                self._make_json_serializable(k): self._make_json_serializable(v)
                for k, v in obj.items()
            }

        # Handle lists/tuples
        if isinstance(obj, (list, tuple)):
            return [self._make_json_serializable(item) for item in obj]

        # Handle objects with __dict__ (custom classes)
        if hasattr(obj, "__dict__"):
            try:
                return self._make_json_serializable(vars(obj))
            except Exception:
                return str(obj)

        # Fallback: convert to string
        try:
            return str(obj)
        except Exception:
            return f"<non-serializable: {type(obj).__name__}>"

    async def _store_overlay_results(
        self, task_data: Dict[str, Any], camera_id: str, frame_id: str
    ) -> None:
        """Store overlay/results data to Redis with composite key for multiple app support.

        Key format: overlay:{frame_id}_{camera_id}_{app_deployment_id}
        This allows multiple apps to store their results for the same frame independently.

        Args:
            task_data: Task data containing the results
            camera_id: Camera identifier
            frame_id: Frame identifier
        """
        if not self.frame_cache:
            self.logger.debug(
                f"[OVERLAY_SKIP] frame_id={frame_id}, camera_id={camera_id} - frame_cache is None"
            )
            return

        if not self.app_deployment_id:
            self.logger.warning(
                f"[OVERLAY_SKIP] frame_id={frame_id}, camera_id={camera_id} - "
                f"app_deployment_id is None/empty"
            )
            return

        try:
            # Extract results data to store
            data = task_data.get("data", {})
            if not data:
                self.logger.warning(
                    f"[OVERLAY_SKIP] frame_id={frame_id}, camera_id={camera_id} - "
                    f"No data in task_data to store"
                )
                return

            # Convert data to JSON-serializable format (handles Enums, custom objects, etc.)
            serializable_data = self._make_json_serializable(data)

            # Serialize results to JSON bytes
            overlay_data = json.dumps(serializable_data).encode("utf-8")

            # Log the composite key that will be used
            composite_key = f"overlay:{frame_id}_{camera_id}_{self.app_deployment_id}"
            self.logger.debug(
                f"[OVERLAY_STORE] Storing overlay: key={composite_key}, "
                f"data_size={len(overlay_data)} bytes"
            )

            # Store overlay asynchronously using frame_cache's put_overlay method
            loop = asyncio.get_running_loop()
            success = await loop.run_in_executor(
                None,  # Use default executor
                self.frame_cache.put_overlay,
                frame_id,
                camera_id,
                self.app_deployment_id,
                overlay_data
            )

            if success:
                self.logger.debug(
                    f"[OVERLAY_OK] Stored overlay: key={composite_key}, "
                    f"data_size={len(overlay_data)} bytes"
                )
            else:
                self.logger.error(
                    f"[OVERLAY_FAIL] Failed to store overlay: key={composite_key}"
                )

        except Exception as e:
            self.logger.error(
                f"[OVERLAY_ERROR] frame_id={frame_id}, camera_id={camera_id}, "
                f"app_deployment_id={self.app_deployment_id}, error={e}",
                exc_info=True
            )

    def _validate_task_data(self, task_data: Dict[str, Any]) -> bool:
        """Validate that task data contains required fields."""
        required_fields = ["camera_id", "message_key", "data"]
        for field in required_fields:
            if field not in task_data:
                self.logger.error(f"Missing required field '{field}' in task data")
                return False
        return True

    def _validate_camera_availability(self, camera_id: str) -> bool:
        """Validate that camera and its stream are available."""
        if camera_id not in self.camera_configs:
            self.logger.warning(f"Camera {camera_id} not found in camera configs")
            return False

        camera_config = self.camera_configs[camera_id]
        if not camera_config.enabled:
            self.logger.debug(f"Camera {camera_id} is disabled, skipping message")
            return False

        # Stream will be created lazily if it doesn't exist yet
        if camera_id not in self.producer_streams:
            self.logger.info(f"Producer stream not found for camera {camera_id}, will be created on first send")

        return True

    def _serialize_for_json(self, obj: Any) -> Any:
        """Recursively serialize objects to JSON-safe types.

        Handles:
        - Objects with .to_dict() method (ProcessingResult, StreamMessage, etc.)
        - Dataclasses (CameraConfig, etc.)
        - Dicts and lists (recursive)
        - Primitive types (str, int, float, bool, None)
        - Bytes (keep as-is for Redis binary storage)
        """
        # Handle None
        if obj is None:
            return None

        # Handle primitives
        if isinstance(obj, (str, int, float, bool)):
            return obj

        # CRITICAL: Keep bytes as-is for Redis binary storage
        # Redis client will handle binary data correctly (stores as separate field)
        # See redis_stream.py:598-617 for binary content extraction logic
        if isinstance(obj, bytes):
            return obj

        # Handle objects with to_dict method
        if hasattr(obj, "to_dict") and callable(obj.to_dict):
            return self._serialize_for_json(obj.to_dict())

        # Handle dataclasses
        if hasattr(obj, "__dataclass_fields__"):
            from dataclasses import asdict
            return self._serialize_for_json(asdict(obj))

        # Handle dicts
        if isinstance(obj, dict):
            return {k: self._serialize_for_json(v) for k, v in obj.items()}

        # Handle lists/tuples
        if isinstance(obj, (list, tuple)):
            return [self._serialize_for_json(item) for item in obj]

        # Fallback: convert to string
        try:
            return str(obj)
        except Exception:
            return None

    async def _send_message_to_stream(self, task_data: Dict[str, Any], camera_id: str) -> None:
        """Send message to the stream for the specified camera with data validation."""
        # Create producer stream dynamically if it doesn't exist (for cameras added after startup)
        if camera_id not in self.producer_streams:
            camera_config = self.camera_configs[camera_id]
            try:
                from matrice_common.stream.matrice_stream import StreamType
                await self._initialize_camera_stream(camera_id, camera_config, StreamType)
                self.logger.info(f"Dynamically created producer stream for camera {camera_id}")
            except Exception as e:
                self.logger.error(f"Failed to create producer stream for camera {camera_id}: {e}")
                raise

        producer_stream = self.producer_streams[camera_id]
        camera_config = self.camera_configs[camera_id]

        # Build complete message structure for backend
        # Backend expects: {"frame_id": str, "camera_id": str, "input_stream": {...}, "data": {...}}
        # See be-inference-ws/internal/service/redis-service.go:455 - extracts frame_id at TOP LEVEL
        # NOTE: frame_id was already validated in _send_message_safely() - use task_data["frame_id"]
        message_to_send = {
            "frame_id": task_data["frame_id"],  # TOP LEVEL - forced, no fallback
            "camera_id": camera_id,
            "message_key": task_data.get("message_key"),
            "input_stream": task_data.get("input_stream", {}),
            "data": task_data.get("data", {}),
        }

        # Serialize all objects to JSON-safe types
        message_to_send = self._serialize_for_json(message_to_send)

        # Extract data field for validation logging
        data_to_send = message_to_send.get("data", {})
        
        # Validate post_processing_result structure
        if "post_processing_result" in data_to_send:
            post_proc_result = data_to_send["post_processing_result"]
            if isinstance(post_proc_result, dict):
                # Log successful post-processing with available data
                # PostProcessor can return different structures:
                # - agg_summary at top level (current format after flattening in post_processing_manager)
                # - data, predictions, summary (other use case results)
                # Check for agg_summary at top level (current) or nested in data field (legacy/fallback)
                agg_summary = None
                if "agg_summary" in post_proc_result:
                    # Current format: agg_summary at top level (flattened by post_processing_manager)
                    agg_summary = post_proc_result.get("agg_summary", {})
                elif "data" in post_proc_result and isinstance(post_proc_result.get("data"), dict):
                    # Legacy format: agg_summary nested in data field (kept for backward compatibility)
                    agg_summary = post_proc_result.get("data", {}).get("agg_summary")
                
                if agg_summary:
                    if isinstance(agg_summary, dict) and agg_summary:
                        frame_keys = list(agg_summary.keys())
                        self.logger.debug(
                            f"Sending message for camera={camera_id} with agg_summary containing {len(frame_keys)} frame(s): {frame_keys}"
                        )
                    else:
                        self.logger.debug(f"Message for camera={camera_id} has empty agg_summary")
                elif "data" in post_proc_result or "predictions" in post_proc_result:
                    # Modern post-processing result structure without agg_summary
                    self.logger.debug(
                        f"Sending message for camera={camera_id} with post_processing_result keys: {list(post_proc_result.keys())}"
                    )
                else:
                    # Unknown structure
                    self.logger.warning(
                        f"Message for camera={camera_id} missing 'agg_summary' in post_processing_result. "
                        f"Available keys: {list(post_proc_result.keys())}"
                    )
        else:
            self.logger.warning(
                f"Message for camera={camera_id} missing 'post_processing_result'. "
                f"Available keys: {list(data_to_send.keys())}"
            )

        # Send COMPLETE message structure to Redis as DICT (not JSON string)
        # Backend needs frame_id, camera_id, input_stream at top level as separate Redis fields
        # Redis will store each top-level key as a separate field in the stream
        # DO NOT json.dumps() - pass the dict directly so Redis stores fields at top level
        await producer_stream.async_add_message(
            camera_config.output_topic,
            message_to_send,  # Send as dict, NOT json string
            key=task_data["message_key"]
        )
        
        # Notify analytics publisher if available
        if self.analytics_publisher:
            try:
                # Log what we're sending to analytics for debugging
                data_to_send = task_data.get("data", {})
                post_proc = data_to_send.get("post_processing_result", {})
                agg_summary = post_proc.get("agg_summary")
                self.logger.debug(
                    f"[PRODUCER_TO_ANALYTICS] camera={camera_id} - "
                    f"Enqueueing analytics data. Has agg_summary: {agg_summary is not None}, "
                    f"agg_summary type: {type(agg_summary).__name__ if agg_summary else 'None'}"
                )
                self.analytics_publisher.enqueue_analytics_data(task_data)
            except Exception as e:
                self.logger.warning(
                    f"[PRODUCER_ANALYTICS_FAIL] camera={camera_id} - Failed to enqueue analytics data: {e}"
                )
        else:
            # Only warn once to avoid log spam - analytics_publisher may be lazily initialized later
            if not self._analytics_warning_logged:
                self.logger.warning(
                    f"[PRODUCER_NO_ANALYTICS] camera={camera_id} - "
                    "analytics_publisher is None, skipping analytics enqueue. "
                    "Will be updated when AnalyticsPublisher is lazily initialized."
                )
                self._analytics_warning_logged = True

