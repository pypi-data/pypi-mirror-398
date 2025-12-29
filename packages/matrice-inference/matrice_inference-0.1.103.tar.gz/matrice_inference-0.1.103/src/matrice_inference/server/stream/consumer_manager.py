"""
Single async event loop consumer manager for 1000 cameras.

Architecture:
- Single async event loop handles all 1000 camera streams
- Async Redis operations (non-blocking) via direct redis.asyncio
- Direct frame bytes extraction and forwarding
- No codec-specific processing (simplified)
- No frame caching (moved to producer)
- Backpressure handling (drop frames if queue full)

Optimizations (matching optimized.py pattern):
- Direct redis.asyncio client (no MatriceStream abstraction)
- Single XREAD for ALL streams (not XREADGROUP with consumer groups)
- Pre-encoded byte keys for field access
- At-most-once delivery (drop under backpressure, no ACK)
- Lightweight FrameTask tuples instead of Dict[str, Any]
"""

import asyncio
import os
import logging
import time
from typing import Dict, Any, Optional, List, NamedTuple

import redis.asyncio as aioredis

from matrice_inference.server.stream.utils import CameraConfig, StreamMessage
from matrice_inference.server.stream.worker_metrics import WorkerMetrics
from matrice_common.stream.shm_ring_buffer import ShmRingBuffer

USE_SHM = os.getenv("USE_SHM", "false").lower() == "true"
# ============================================================================
# PRE-ENCODED FIELD KEYS (avoid repeated string encoding at high FPS)
# ============================================================================
KEY_CAM_ID = b"cam_id"
KEY_CAMERA_ID = b"camera_id"
KEY_SHM_NAME = b"shm_name"
KEY_FRAME_IDX = b"frame_idx"
KEY_TS_NS = b"ts_ns"
KEY_WIDTH = b"width"
KEY_HEIGHT = b"height"
KEY_SHM_MODE = b"shm_mode"
KEY_FORMAT = b"format"
KEY_FRAME_ID = b"frame_id"
KEY_IS_SIMILAR = b"is_similar"
KEY_REFERENCE_FRAME_IDX = b"reference_frame_idx"
KEY_CONTENT = b"content"
KEY_INPUT_STREAM_CONTENT = b"input_stream__content"


class FrameTask(NamedTuple):
    """Lightweight frame task for minimal overhead message passing.

    Using NamedTuple instead of Dict[str, Any] reduces:
    - Memory allocation (no dict overhead)
    - Attribute access time (direct vs hash lookup)
    - Serialization cost (fixed structure)

    Supports both SHM mode (shm_name/frame_idx) and legacy mode (frame_bytes).
    """
    camera_id: str
    shm_name: bytes
    frame_idx: int
    width: int
    height: int
    ts_ns: int
    frame_format: str = "BGR"
    is_similar: bool = False
    reference_frame_idx: Optional[int] = None
    frame_bytes: Optional[bytes] = None  # For legacy (non-SHM) mode
    is_shm_mode: bool = True  # True for SHM mode, False for legacy mode


class AsyncConsumerManager:
    """
    Manages 1000 camera streams with single async event loop.

    HIGH-PERFORMANCE ARCHITECTURE (optimized.py pattern):
    - Direct redis.asyncio client (no MatriceStream abstraction)
    - Single XREAD call for ALL streams (not per-stream XREADGROUP)
    - Pre-encoded byte keys for field access
    - At-most-once delivery (drop under backpressure, no ACK)
    - asyncio.Queue with put_nowait() (no feeder threads)
    - Lightweight FrameTask tuples instead of Dict[str, Any]

    Key Features:
    - Single event loop for all cameras (not 1000 threads)
    - Non-blocking async stream reads
    - Backpressure handling (drop frames if queue full)
    - Dynamic camera add/remove support
    """

    # ================================================================
    # HIGH-PERFORMANCE CONFIGURATION (matching optimized.py)
    # ================================================================
    BATCH_SIZE = 5000       # Messages to read per XREAD (high for throughput)
    BLOCK_MS = 5            # XREAD block time in ms (low for responsiveness)
    QUEUE_MAX = 200_000     # Max queue size before backpressure drop

    # ================================================================
    # METRIC AGGREGATION
    # ================================================================
    # Problem: Per-frame metrics recording adds lock contention + overhead
    # At 10000 FPS, function calls dominate CPU time
    #
    # Solution: Aggregate metrics and flush periodically (every 1000 frames)
    # ================================================================
    METRICS_AGGREGATION_COUNT = 1000  # Aggregate N frames before recording

    def __init__(
        self,
        camera_configs: Dict[str, CameraConfig],
        stream_config: Dict[str, Any],
        app_deployment_id: str,
        pipeline: Any,
        message_timeout: float = 0.5,  # 500ms - must be well under SHM buffer lifetime
        # ================================================================
        # SHM_MODE: New parameters for shared memory architecture
        # ================================================================
        use_shm: bool = USE_SHM,  # Feature flag for SHM mode
    ):
        self.camera_configs = camera_configs
        self.stream_config = stream_config
        self.pipeline = pipeline
        self.message_timeout = message_timeout
        self.running = False

        # Initialize metrics (shared across all cameras)
        self.metrics = WorkerMetrics.get_shared("consumer")

        # Generate unique app instance identifier for consumer groups
        self.app_deployment_id = app_deployment_id

        self.logger = logging.getLogger(f"{__name__}.AsyncConsumerManager")

        # ================================================================
        # SHM_MODE: Shared memory configuration
        # ================================================================
        self.use_shm = use_shm

        # SHM buffers (attached on demand per camera)
        self._shm_buffers: Dict[str, ShmRingBuffer] = {}

        if use_shm:
            self.logger.info("SHM_MODE ENABLED: Will read frames from shared memory")

        # ================================================================
        # DIRECT REDIS.ASYNCIO CLIENT (no MatriceStream abstraction)
        # ================================================================
        # Single redis connection for ALL streams - much more efficient than
        # one MatriceStream per shard with consumer groups
        self._redis: Optional[aioredis.Redis] = None

        # Stream cursors: {stream_name_bytes: last_id_bytes}
        # Use "$" to start reading only new messages (like optimized.py)
        self._stream_cursors: Dict[bytes, bytes] = {}

        # Reverse mapping: stream_name -> camera_id for message routing
        self._stream_to_camera: Dict[str, str] = {}

        # ================================================================
        # ASYNCIO.QUEUE FOR DIRECT MESSAGE PASSING (no feeder threads)
        # ================================================================
        # Problem: feeder threads add context switch overhead and complexity
        # Solution: asyncio.Queue with put_nowait() for instant non-blocking enqueue
        # Workers read directly from asyncio.Queue in their event loop
        self._task_queue: Optional[asyncio.Queue] = None

        # ================================================================
        # CONSUMER TASK AND BRIDGE TASK
        # ================================================================
        # Single consumer task reads ALL streams with one XREAD call
        self._consumer_task: Optional[asyncio.Task] = None
        # Bridge task transfers from asyncio.Queue to mp.Queues for workers
        self._bridge_task: Optional[asyncio.Task] = None

        # ================================================================
        # METRIC AGGREGATION STATE
        # ================================================================
        self._metrics_frame_count = 0
        self._metrics_latency_sum_ns = 0
        self._metrics_max_latency_ns = 0
        self._metrics_last_flush = time.time()

    async def start(self):
        """Start optimized consumer using single XREAD for all streams.

        HIGH-PERFORMANCE ARCHITECTURE:
        - Single redis.asyncio connection for ALL streams
        - Single XREAD call reads from ALL streams at once
        - asyncio.Queue for direct message passing (no feeder threads)
        - At-most-once delivery (drop under backpressure, no ACK)
        """
        self.running = True
        self.metrics.mark_active()

        num_cameras = len(self.camera_configs)

        self.logger.info(
            f"Starting HIGH-PERFORMANCE async consumer manager for {num_cameras} cameras "
            f"using single XREAD (app_deployment_id={self.app_deployment_id})"
        )

        # Initialize direct redis.asyncio client
        await self._initialize_redis()

        # Build stream cursors for all cameras
        await self._initialize_stream_cursors()

        # Create asyncio.Queue for direct message passing
        self._task_queue = asyncio.Queue(maxsize=self.QUEUE_MAX)

        # Start single consumer task that reads ALL streams
        self._consumer_task = asyncio.create_task(
            self._consume_all_streams(),
            name="consumer_all_streams"
        )

        # Start queue bridge task to transfer from asyncio.Queue to mp.Queues
        self._bridge_task = asyncio.create_task(
            self._bridge_to_mp_queues(),
            name="queue_bridge"
        )

        self.logger.info(
            f"Started high-performance consumer for {len(self._stream_cursors)} streams "
            f"(BATCH_SIZE={self.BATCH_SIZE}, BLOCK_MS={self.BLOCK_MS})"
        )

    async def stop(self):
        """Stop consumer and clean up resources."""
        self.running = False
        self.metrics.mark_inactive()

        # Cancel main consumer task
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await asyncio.wait_for(self._consumer_task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            self._consumer_task = None

        # Cancel bridge task
        if self._bridge_task:
            self._bridge_task.cancel()
            try:
                await asyncio.wait_for(self._bridge_task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            self._bridge_task = None

        # Flush any pending aggregated metrics
        self._flush_aggregated_metrics()

        # Close redis connection
        if self._redis:
            try:
                await self._redis.close()
            except Exception:
                pass
            self._redis = None

        # Clear stream cursors
        self._stream_cursors.clear()
        self._stream_to_camera.clear()

        # ================================================================
        # SHM_MODE: Detach from SHM buffers (consumer does NOT unlink)
        # ================================================================
        if self.use_shm:
            for camera_id, shm_buffer in list(self._shm_buffers.items()):
                try:
                    shm_buffer.close()  # Detach only (consumer doesn't unlink)
                    self.logger.debug(f"Detached from SHM buffer for camera {camera_id}")
                except Exception as e:
                    self.logger.warning(f"Error detaching from SHM {camera_id}: {e}")
            self._shm_buffers.clear()

        self.logger.info("Stopped async consumer manager")

    async def add_camera(self, camera_id: str, config: CameraConfig):
        """
        Add a new camera dynamically.

        The camera's stream will be added to the single XREAD on the next iteration.

        Args:
            camera_id: Unique camera identifier
            config: Camera configuration
        """
        if not config.enabled:
            self.logger.warning(f"Camera {camera_id} is disabled, skipping add")
            return

        stream_name = config.input_topic
        if stream_name in self._stream_to_camera:
            self.logger.warning(f"Stream {stream_name} already registered, skipping add")
            return

        try:
            # Store camera config
            self.camera_configs[camera_id] = config

            # Add to stream cursors (will be picked up by next XREAD)
            stream_name_bytes = stream_name.encode() if isinstance(stream_name, str) else stream_name
            self._stream_cursors[stream_name_bytes] = b"$"  # Read only new messages
            self._stream_to_camera[stream_name] = camera_id

            self.logger.info(f"Added camera {camera_id} -> stream {stream_name}")

        except Exception as e:
            self.logger.error(f"Failed to add camera {camera_id}: {e}")

    async def remove_camera(self, camera_id: str):
        """
        Remove a camera dynamically.

        The camera's stream will be removed from the XREAD on the next iteration.

        Args:
            camera_id: Unique camera identifier
        """
        try:
            # Get stream name from camera config
            config = self.camera_configs.pop(camera_id, None)
            if config:
                stream_name = config.input_topic
                stream_name_bytes = stream_name.encode() if isinstance(stream_name, str) else stream_name

                # Remove from stream cursors
                self._stream_cursors.pop(stream_name_bytes, None)
                self._stream_to_camera.pop(stream_name, None)

            # Detach from SHM buffer if present
            if camera_id in self._shm_buffers:
                try:
                    self._shm_buffers[camera_id].close()
                except Exception:
                    pass
                del self._shm_buffers[camera_id]

            self.logger.info(f"Removed camera {camera_id} from consumer manager")

        except Exception as e:
            self.logger.error(f"Failed to remove camera {camera_id}: {e}")

    # ========================================================================
    # HIGH-PERFORMANCE REDIS INITIALIZATION
    # ========================================================================

    async def _initialize_redis(self) -> None:
        """Initialize direct redis.asyncio client.

        Single connection for ALL streams - much more efficient than
        MatriceStream abstraction with consumer groups.
        """
        host = self.stream_config.get("host") or "localhost"
        port = self.stream_config.get("port") or 6379
        password = self.stream_config.get("password")
        db = self.stream_config.get("db", 0)

        self._redis = aioredis.Redis(
            host=host,
            port=port,
            password=password,
            db=db,
            decode_responses=False,  # Keep bytes for performance
            socket_keepalive=True,
            socket_timeout=30,
            health_check_interval=30,
        )

        # Test connection
        try:
            await self._redis.ping()
            self.logger.info(f"Connected to Redis at {host}:{port}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def _initialize_stream_cursors(self) -> None:
        """Build stream cursors for all enabled cameras.

        Each camera's input_topic becomes a stream to read from.
        Use "$" to start reading only new messages (like optimized.py).
        """
        for camera_id, config in self.camera_configs.items():
            if not config.enabled:
                continue

            stream_name = config.input_topic
            stream_name_bytes = stream_name.encode() if isinstance(stream_name, str) else stream_name

            # Use "$" to read only new messages (no historical backlog)
            self._stream_cursors[stream_name_bytes] = b"$"
            self._stream_to_camera[stream_name] = camera_id

        self.logger.info(
            f"Initialized {len(self._stream_cursors)} stream cursors for cameras"
        )

    # ========================================================================
    # HIGH-PERFORMANCE SINGLE XREAD CONSUMER
    # ========================================================================

    async def _consume_all_streams(self) -> None:
        """Consume ALL streams with single XREAD call (optimized.py pattern).

        HIGH-THROUGHPUT DESIGN:
        - Single XREAD reads from ALL camera streams at once
        - NO consumer groups, NO XACK (at-most-once delivery)
        - Pre-encoded byte keys for field access
        - put_nowait() with backpressure drop
        - Lightweight FrameTask tuples
        - Result: 10,000+ FPS throughput
        """
        self.logger.info(
            f"Starting single XREAD consumer for {len(self._stream_cursors)} streams"
        )

        # Local references for speed (avoid attribute lookup in hot loop)
        redis_client = self._redis
        xread = redis_client.xread
        stream_cursors = self._stream_cursors
        stream_to_camera = self._stream_to_camera
        task_queue = self._task_queue
        time_ns = time.time_ns
        batch_size = self.BATCH_SIZE
        block_ms = self.BLOCK_MS

        frames_processed = 0
        frames_dropped = 0
        frames_backpressure_skipped = 0
        last_log_time = time.time()

        # Backpressure threshold: skip XREAD when queue is 80% full
        # This saves CPU by avoiding SHM parsing + routing work when downstream is saturated
        backpressure_threshold = int(self.QUEUE_MAX * 0.8)

        while self.running:
            try:
                # EARLY BACKPRESSURE CHECK: Skip work when downstream is saturated
                # This saves CPU by avoiding XREAD + SHM parsing when queue is nearly full
                current_queue_size = task_queue.qsize()
                if current_queue_size > backpressure_threshold:
                    frames_backpressure_skipped += 1
                    await asyncio.sleep(0.001)  # Brief backoff (1ms)
                    continue

                # SINGLE XREAD for ALL streams at once
                messages = await xread(
                    streams=stream_cursors,
                    count=batch_size,
                    block=block_ms,
                )

                if not messages:
                    continue

                now_ns = time_ns()

                for stream_name_bytes, entries in messages:
                    # Update stream cursor to last message ID
                    stream_cursors[stream_name_bytes] = entries[-1][0]

                    # Decode stream name for camera lookup
                    stream_name = stream_name_bytes.decode() if isinstance(stream_name_bytes, bytes) else stream_name_bytes
                    camera_id = stream_to_camera.get(stream_name)

                    if not camera_id:
                        continue

                    for msg_id, fields in entries:
                        # Fast field extraction using pre-encoded keys
                        shm_mode = fields.get(KEY_SHM_MODE)

                        if shm_mode in (b"1", b"true", b"True"):
                            # SHM mode: extract metadata for worker to read from SHM
                            frame_task = self._parse_shm_message(
                                camera_id, fields, now_ns
                            )
                        else:
                            # Legacy mode: parse embedded frame bytes
                            frame_task = self._parse_legacy_message(
                                camera_id, fields, now_ns
                            )

                        if frame_task is None:
                            continue

                        # Non-blocking enqueue with backpressure drop
                        try:
                            task_queue.put_nowait(frame_task)
                            frames_processed += 1
                        except asyncio.QueueFull:
                            frames_dropped += 1

                # Periodic logging (every 30 seconds)
                now = time.time()
                if now - last_log_time > 30.0:
                    self.logger.info(
                        f"Consumer: {frames_processed} processed, "
                        f"{frames_dropped} dropped, {frames_backpressure_skipped} backpressure_skipped, "
                        f"queue_size={task_queue.qsize()}"
                    )
                    last_log_time = now

            except asyncio.CancelledError:
                break
            except (aioredis.ConnectionError, aioredis.TimeoutError) as e:
                self.logger.warning(f"Redis connection error: {e}, reconnecting...")
                await asyncio.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Consumer error: {e}")
                await asyncio.sleep(0.1)

        self.logger.info(
            f"Consumer stopped: {frames_processed} processed, {frames_dropped} dropped"
        )

    async def _bridge_to_mp_queues(self) -> None:
        """Bridge from asyncio.Queue to mp.Queues for inference workers.

        This task runs concurrently with _consume_all_streams and transfers
        FrameTask tuples from the internal asyncio.Queue to the mp.Queues
        that inference workers read from.

        Features:
        - Converts FrameTask tuples to dict format expected by workers
        - Routes to correct worker queue based on camera_id hash
        - Non-blocking with configurable batch transfers
        - Backpressure handling (drop if mp.Queue full)
        """
        self.logger.info("Starting queue bridge to mp.Queues")

        # Get inference queues from pipeline
        inference_queues = self.pipeline.inference_queues
        if not inference_queues:
            self.logger.error("No inference queues available, bridge stopping")
            return

        num_workers = len(inference_queues)
        task_queue = self._task_queue
        time_ns = time.time_ns

        frames_bridged = 0
        frames_dropped = 0
        last_log_time = time.time()

        while self.running:
            try:
                # Get FrameTask from asyncio.Queue (with timeout for shutdown check)
                try:
                    frame_task = await asyncio.wait_for(
                        task_queue.get(),
                        timeout=0.01  # 10ms timeout for responsiveness
                    )
                except asyncio.TimeoutError:
                    continue

                if frame_task is None:
                    continue

                # Convert FrameTask to dict format expected by inference workers
                task_data = self._frame_task_to_dict(frame_task)

                # Route to correct worker based on camera_id hash
                camera_id = frame_task.camera_id
                worker_id = hash(camera_id) % num_workers
                target_queue = inference_queues[worker_id]

                # Non-blocking put to mp.Queue
                try:
                    target_queue.put_nowait(task_data)
                    frames_bridged += 1

                    # Record latency metrics
                    now_ns = time_ns()
                    latency_ns = now_ns - frame_task.ts_ns
                    self._record_aggregated_metrics_ns(latency_ns)

                except Exception:
                    # Queue full - drop silently (backpressure)
                    frames_dropped += 1

                # Periodic logging (every 30 seconds)
                now = time.time()
                if now - last_log_time > 30.0:
                    self.logger.info(
                        f"Queue bridge: {frames_bridged} bridged, "
                        f"{frames_dropped} dropped"
                    )
                    last_log_time = now

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Queue bridge error: {e}")
                await asyncio.sleep(0.01)

        self.logger.info(
            f"Queue bridge stopped: {frames_bridged} bridged, {frames_dropped} dropped"
        )

    def _frame_task_to_dict(self, frame_task: FrameTask) -> Dict[str, Any]:
        """Convert FrameTask namedtuple to dict format expected by inference workers.

        The inference workers expect a dict with specific fields.
        - SHM mode: 'shm_ref' for SHM-based frame loading
        - Legacy mode: 'frame_bytes' for direct frame bytes

        Args:
            frame_task: FrameTask namedtuple from consumer

        Returns:
            Dict in format expected by inference workers
        """
        camera_id = frame_task.camera_id

        if frame_task.is_shm_mode:
            # SHM MODE: Worker reads frame from shared memory
            frame_idx = frame_task.frame_idx
            frame_id = f"shm_{camera_id}_{frame_idx}"

            # SHM reference for worker to read frame directly
            shm_ref = {
                "camera_id": camera_id,
                "shm_name": frame_task.shm_name.decode() if isinstance(frame_task.shm_name, bytes) else frame_task.shm_name,
                "frame_idx": frame_idx,
                "width": frame_task.width,
                "height": frame_task.height,
                "format": frame_task.frame_format,
            }

            # Build task dict (compatible with existing inference worker)
            task_data = {
                "camera_id": camera_id,
                "frame_bytes": None,  # ZERO-COPY: No frame bytes, use shm_ref
                "frame_id": frame_id,
                "message": None,  # Lightweight path - no StreamMessage
                "input_stream": {
                    "shm_mode": True,
                    "frame_idx": frame_idx,
                    "width": frame_task.width,
                    "height": frame_task.height,
                    "format": frame_task.frame_format,
                },
                "shm_ref": shm_ref,  # Worker uses this to read from SHM
                "stream_key": camera_id,
                "extra_params": {},
                "camera_config": self.camera_configs.get(camera_id),
                "ts_ns": frame_task.ts_ns,
            }

            # Handle similar frames (use cached result)
            if frame_task.is_similar and frame_task.reference_frame_idx is not None:
                ref_frame_id = f"shm_{camera_id}_{frame_task.reference_frame_idx}"
                task_data["input_stream"]["use_cached_result"] = True
                task_data["input_stream"]["cached_frame_id"] = ref_frame_id

        else:
            # LEGACY MODE: Worker uses embedded frame bytes directly
            import uuid
            frame_id = f"legacy_{camera_id}_{uuid.uuid4().hex[:8]}"

            task_data = {
                "camera_id": camera_id,
                "frame_bytes": frame_task.frame_bytes,  # Direct bytes for worker
                "frame_id": frame_id,
                "message": None,  # Lightweight path - no StreamMessage
                "input_stream": {
                    "shm_mode": False,
                    "width": frame_task.width,
                    "height": frame_task.height,
                    "format": frame_task.frame_format,
                    "content": frame_task.frame_bytes,
                },
                "shm_ref": None,  # No SHM reference in legacy mode
                "stream_key": camera_id,
                "extra_params": {},
                "camera_config": self.camera_configs.get(camera_id),
                "ts_ns": frame_task.ts_ns,
            }

        return task_data

    def _parse_shm_message(
        self,
        camera_id: str,
        fields: Dict[bytes, bytes],
        recv_ns: int
    ) -> Optional[FrameTask]:
        """Parse SHM message fields into lightweight FrameTask.

        Uses pre-encoded byte keys for fast field access.
        Returns None if required fields are missing.

        Args:
            camera_id: Camera identifier
            fields: Raw message fields from XREAD
            recv_ns: Receive timestamp in nanoseconds

        Returns:
            FrameTask or None if invalid
        """
        try:
            # Extract required fields using pre-encoded keys
            shm_name = fields.get(KEY_SHM_NAME)
            frame_idx_raw = fields.get(KEY_FRAME_IDX)
            width_raw = fields.get(KEY_WIDTH)
            height_raw = fields.get(KEY_HEIGHT)
            ts_ns_raw = fields.get(KEY_TS_NS)

            if not all([shm_name, frame_idx_raw, width_raw, height_raw]):
                return None

            # Parse integer fields
            frame_idx = int(frame_idx_raw)
            width = int(width_raw)
            height = int(height_raw)
            ts_ns = int(ts_ns_raw) if ts_ns_raw else recv_ns

            # Optional fields
            frame_format_raw = fields.get(KEY_FORMAT)
            frame_format = frame_format_raw.decode() if frame_format_raw else "BGR"

            is_similar_raw = fields.get(KEY_IS_SIMILAR)
            is_similar = is_similar_raw in (b"1", b"true", b"True") if is_similar_raw else False

            reference_frame_idx = None
            if is_similar:
                ref_raw = fields.get(KEY_REFERENCE_FRAME_IDX)
                if ref_raw:
                    reference_frame_idx = int(ref_raw)

            return FrameTask(
                camera_id=camera_id,
                shm_name=shm_name,
                frame_idx=frame_idx,
                width=width,
                height=height,
                ts_ns=ts_ns,
                frame_format=frame_format,
                is_similar=is_similar,
                reference_frame_idx=reference_frame_idx,
                frame_bytes=None,  # SHM mode - no embedded bytes
                is_shm_mode=True,
            )

        except (ValueError, TypeError):
            return None

    def _parse_legacy_message(
        self,
        camera_id: str,
        fields: Dict[bytes, bytes],
        recv_ns: int
    ) -> Optional[FrameTask]:
        """Parse legacy (non-SHM) message with embedded frame bytes.

        Legacy mode embeds JPEG-encoded frame bytes directly in Redis message.
        This is used when USE_SHM=false in the upstream camera streamer.

        Args:
            camera_id: Camera identifier
            fields: Raw message fields from XREAD
            recv_ns: Receive timestamp in nanoseconds

        Returns:
            FrameTask or None if invalid
        """
        try:
            # Extract frame content - try multiple field names for compatibility
            content = fields.get(KEY_CONTENT) or fields.get(KEY_INPUT_STREAM_CONTENT)

            if not content:
                return None

            # Extract optional dimensions (may not be present in legacy messages)
            width_raw = fields.get(KEY_WIDTH)
            height_raw = fields.get(KEY_HEIGHT)

            width = int(width_raw) if width_raw else 0
            height = int(height_raw) if height_raw else 0

            ts_ns_raw = fields.get(KEY_TS_NS)
            ts_ns = int(ts_ns_raw) if ts_ns_raw else recv_ns

            return FrameTask(
                camera_id=camera_id,
                shm_name=b"",  # Not used in legacy mode
                frame_idx=0,   # Not used in legacy mode
                width=width,
                height=height,
                ts_ns=ts_ns,
                frame_format="JPEG",  # Legacy uses JPEG encoding
                is_similar=False,
                reference_frame_idx=None,
                frame_bytes=content,  # Embedded frame bytes
                is_shm_mode=False,    # Legacy mode flag
            )

        except (ValueError, TypeError):
            return None

    def _is_stream_recoverable_error(self, error: Exception) -> bool:
        """Check if the error is a recoverable stream error.

        Args:
            error: The exception to check

        Returns:
            True if this is a recoverable error
        """
        error_str = str(error).lower()

        recoverable_patterns = [
            "no such key",      # Stream doesn't exist
            "connection",       # Connection issues
            "timeout",          # Timeout issues
        ]

        for pattern in recoverable_patterns:
            if pattern in error_str:
                return True

        return False

    # ========================================================================
    # METRIC AGGREGATION (optimized for nanosecond precision)
    # ========================================================================

    def _record_aggregated_metrics_ns(self, latency_ns: int) -> None:
        """Record metrics in aggregation buffer, flush periodically.

        Uses nanosecond precision for accurate latency tracking at high FPS.
        Flushes every N frames to reduce lock contention.
        """
        self._metrics_frame_count += 1
        self._metrics_latency_sum_ns += latency_ns
        if latency_ns > self._metrics_max_latency_ns:
            self._metrics_max_latency_ns = latency_ns

        # Flush every N frames
        if self._metrics_frame_count >= self.METRICS_AGGREGATION_COUNT:
            self._flush_aggregated_metrics()

    def _flush_aggregated_metrics(self) -> None:
        """Flush aggregated metrics to the metrics system."""
        if self._metrics_frame_count == 0:
            return

        # Convert nanoseconds to milliseconds for metrics system
        avg_latency_ms = (self._metrics_latency_sum_ns / self._metrics_frame_count) / 1_000_000

        # Record batch to metrics system
        self.metrics.record_latency(avg_latency_ms)
        self.metrics.record_throughput(count=self._metrics_frame_count)

        # Reset aggregation state
        self._metrics_frame_count = 0
        self._metrics_latency_sum_ns = 0
        self._metrics_max_latency_ns = 0
        self._metrics_last_flush = time.time()

    # ========================================================================
    # SHM_MODE: Shared Memory Methods (used by inference worker)
    # ========================================================================

    def get_task_queue(self) -> Optional[asyncio.Queue]:
        """Get the task queue for inference workers to consume from.

        Returns:
            asyncio.Queue containing FrameTask tuples
        """
        return self._task_queue

    def _get_frame_from_shm(self, data: Dict[str, Any]) -> Optional[bytes]:
        """Read frame from shared memory using metadata (LEGACY - use SHM refs instead).

        NOTE: The new zero-copy path passes SHM references to workers which read
        directly from SHM. This function is kept for backwards compatibility only.
        Frames are expected to be BGR format - no conversion is performed.

        Args:
            data: SHM metadata from Redis message

        Returns:
            Frame bytes (BGR format), or None if unavailable
        """
        camera_id = data.get("cam_id")
        shm_name = data.get("shm_name")
        frame_idx_str = data.get("frame_idx")
        width_str = data.get("width")
        height_str = data.get("height")
        frame_format = data.get("format", "NV12")

        # Parse string values
        try:
            frame_idx = int(frame_idx_str) if frame_idx_str else None
            width = int(width_str) if width_str else None
            height = int(height_str) if height_str else None
        except (ValueError, TypeError):
            self.logger.error(f"Invalid SHM metadata values: {data}")
            return None

        if not all([camera_id, shm_name, frame_idx is not None, width, height]):
            self.logger.error(f"Incomplete SHM metadata: {data}")
            return None

        # Get or attach to SHM buffer
        try:
            shm_buffer = self._get_or_attach_shm_buffer(
                camera_id, shm_name, width, height, frame_format
            )
        except Exception as e:
            self.logger.error(f"Failed to attach to SHM {shm_name}: {e}")
            return None

        # Calculate consumer lag for monitoring
        header = shm_buffer.get_header()
        current_write_idx = header['write_idx']
        consumer_lag = current_write_idx - frame_idx

        # Log warning if consumer is falling behind (>70% of buffer)
        lag_threshold_warning = shm_buffer.slot_count * 0.7
        lag_threshold_critical = shm_buffer.slot_count * 0.8
        if consumer_lag > lag_threshold_warning:
            self.logger.warning(
                f"Consumer lag warning: camera={camera_id}, "
                f"lag={consumer_lag}/{shm_buffer.slot_count} frames "
                f"({consumer_lag * 100 / shm_buffer.slot_count:.1f}%)"
            )

        # If severely behind (>80% of buffer), skip to latest frame
        if consumer_lag > lag_threshold_critical:
            self.logger.warning(
                f"Consumer severely behind, skipping {consumer_lag} frames "
                f"to latest for camera {camera_id}"
            )
            frame_idx = current_write_idx  # Use latest frame instead

        # Check if frame is still valid (not overwritten)
        if not shm_buffer.is_frame_valid(frame_idx):
            self.logger.debug(f"Frame {frame_idx} overwritten in SHM {shm_name}")
            return None

        # Read frame from SHM with torn frame detection
        # read_frame_copy() checks sequence counters to detect if producer
        # was writing during our read (torn frame)
        raw_bytes = shm_buffer.read_frame_copy(frame_idx)
        if raw_bytes is None:
            self.logger.debug(f"Frame {frame_idx} torn or overwritten in SHM {shm_name}")
            return None

        # Return raw bytes - frames are already BGR format (no conversion needed)
        return raw_bytes

    def _get_or_attach_shm_buffer(
        self,
        camera_id: str,
        shm_name: str,
        width: int,
        height: int,
        frame_format: str
    ) -> ShmRingBuffer:
        """Attach to existing SHM buffer (consumer side).

        Dynamically reads slot_count from SHM header to match producer config.

        Args:
            camera_id: Camera identifier
            shm_name: SHM segment name
            width: Frame width
            height: Frame height
            frame_format: Frame format string

        Returns:
            ShmRingBuffer instance
        """
        if camera_id not in self._shm_buffers:
            format_map = {
                "BGR": ShmRingBuffer.FORMAT_BGR,
                "RGB": ShmRingBuffer.FORMAT_RGB,
                "NV12": ShmRingBuffer.FORMAT_NV12,
            }
            frame_format_int = format_map.get(frame_format, ShmRingBuffer.FORMAT_BGR)

            # First attach with temporary slot_count to read header
            temp_buffer = ShmRingBuffer(
                camera_id=camera_id,
                width=width,
                height=height,
                frame_format=frame_format_int,
                slot_count=1000,  # Temporary - will read actual from header
                create=False
            )

            # Read actual slot_count from producer's header
            header = temp_buffer.get_header()
            actual_slot_count = header.get('slot_count', 1000)
            temp_buffer.close()

            # Create final buffer with correct slot_count from producer
            self._shm_buffers[camera_id] = ShmRingBuffer(
                camera_id=camera_id,
                width=width,
                height=height,
                frame_format=frame_format_int,
                slot_count=actual_slot_count,  # Match producer's config
                create=False  # Consumer attaches (does NOT create)
            )
            self.logger.info(
                f"Attached to SHM buffer for camera {camera_id}: "
                f"{width}x{height} {frame_format}, slot_count={actual_slot_count}"
            )

        return self._shm_buffers[camera_id]
