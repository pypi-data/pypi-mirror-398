"""
High-performance multiprocessing post-processing worker for stateful tracking.

Architecture:
- Multiprocessing: Multiple separate processes - TRUE PARALLELISM
- Camera Routing: hash(camera_id) % num_workers for state isolation - ORDER PRESERVATION
- Isolated Tracker States: Each process maintains trackers for assigned cameras
- CPU-bound Processing: Object tracking, aggregation, analytics

Architecture Flow:
- PostProcessor creates per-camera tracker states (stateful tracking)
- Each process handles subset of cameras (e.g., 250 cameras per process)
- Camera-based routing ensures same camera always goes to same worker
- Tracker states remain isolated within each process

Performance Targets:
- 10,000 FPS throughput
- <100ms latency per frame
- Isolated tracker state per camera
- True parallelism (bypasses Python GIL)
"""

import logging
import multiprocessing as mp
import time
from typing import Any, Dict, List, Optional


def postprocessing_worker_process(
    worker_id: int,
    num_workers: int,
    input_queue: mp.Queue,
    output_queue: mp.Queue,
    post_processor_config: Dict[str, Any],
    metrics_queue: Optional[mp.Queue] = None,
):
    """
    Worker process for CPU-bound post-processing with stateful tracking.

    IMPORTANT: Each worker reads from its OWN dedicated queue (input_queue).
    Inference workers route frames based on hash(camera_id) % num_workers.
    This ensures strict ordering per camera and isolated tracker states.

    Each process:
    1. Initializes PostProcessor with config
    2. Maintains isolated tracker states for assigned cameras
    3. Processes tasks from its dedicated queue (no re-queuing needed)
    4. Outputs results to single output queue (producer is single-threaded)

    Args:
        worker_id: Worker process ID
        num_workers: Total number of worker processes
        input_queue: This worker's dedicated queue (routed by inference workers)
        output_queue: Single output queue for producer
        post_processor_config: Configuration for PostProcessor initialization
        metrics_queue: Queue for sending metrics back to main process
    """
    # Set up logging for this process
    logger = logging.getLogger(f"postproc_worker_{worker_id}")
    logger.setLevel(logging.INFO)

    try:
        # Import dependencies inside process to avoid pickle issues
        import asyncio
        from matrice_analytics.post_processing.post_processor import PostProcessor
        from matrice_inference.server.stream.worker_metrics import MultiprocessWorkerMetrics

        # Initialize post-processor with config
        post_processor = PostProcessor(**post_processor_config)

        # Create ONE event loop for this worker process and reuse for all frames
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Initialize metrics for this worker (multiprocess-safe via queue)
        # NOTE: Metrics are sent to main process via metrics_queue for aggregation
        # This is required because multiprocessing doesn't share memory between processes
        if metrics_queue is not None:
            metrics = MultiprocessWorkerMetrics(
                worker_id=f"post_processing_{worker_id}",
                worker_type="post_processing",
                metrics_queue=metrics_queue
            )
        else:
            logger.warning(f"Worker {worker_id}: No metrics_queue provided, metrics will not be collected")
            metrics = None
        
        if metrics:
            metrics.mark_active()

        logger.info(f"Post-processing worker {worker_id}/{num_workers} initialized")

        # Main processing loop
        try:
            while True:
                try:
                    # Get task from queue (blocking with timeout)
                    start_time = time.time()
                    task_data = input_queue.get(timeout=1.0)

                    # Extract task fields
                    camera_id = task_data.get("camera_id")
                    frame_id = task_data.get("frame_id")
                    model_result = task_data.get("model_result")
                    stream_key = task_data.get("stream_key", camera_id)
                    input_stream = task_data.get("input_stream", {})
                    camera_config = task_data.get("camera_config")

                    if not camera_id:
                        logger.error("Task missing camera_id - skipping")
                        continue

                    # CRITICAL: Validate frame_id exists - skip if missing
                    if not frame_id:
                        logger.error(
                            f"[FRAME_ID_MISSING] camera={camera_id} - No frame_id in task_data. Skipping frame."
                        )
                        continue

                    if model_result is None:
                        # Inference failed for this frame - this is expected when model errors occur
                        # Don't log as error since inference_worker already logged the actual error
                        logger.debug(f"Skipping frame for camera {camera_id} - inference returned no result")
                        continue

                    # No re-queue needed - inference workers already routed this task to correct worker
                    # This worker's dedicated queue only contains tasks for cameras assigned to it
                    # Same camera always goes to same worker for tracker state isolation

                    # Process with stateful tracking
                    # PostProcessor handles tracker state internally via its use case cache
                    # stream_key ensures same camera uses same cached use case instance with persistent tracker

                    # Extract input bytes if available (needed for some use cases like face recognition)
                    input_bytes = None
                    if isinstance(input_stream, dict):
                        content = input_stream.get("content")
                        if isinstance(content, bytes):
                            input_bytes = content

                    # CRITICAL: Extract stream_info from input_stream and add frame_id to it
                    # This matches staging behavior in post_processing_worker._extract_processing_params()
                    stream_info = {}
                    if isinstance(input_stream, dict):
                        stream_info = input_stream.get("stream_info", {})
                        if not isinstance(stream_info, dict):
                            stream_info = {}
                        # Add frame_id to stream_info if available (required by post-processing use cases)
                        if frame_id:
                            stream_info["frame_id"] = frame_id

                    # Use the worker's persistent event loop (created at startup)
                    # PostProcessor uses internal config from initialization (server.py lines 426-431)
                    # Pass stream_key for use case caching (same pattern as inference_interface.py line 234-239)
                    # CRITICAL: Pass stream_info for use cases that need frame metadata
                    result = loop.run_until_complete(
                        post_processor.process(
                            data=model_result,
                            stream_key=stream_key,
                            input_bytes=input_bytes,
                            stream_info=stream_info,
                        )
                    )

                    # Serialize ProcessingResult to dict (handles nested objects)
                    post_processed_dict = result.to_dict() if hasattr(result, "to_dict") else result

                    # Extract message_key from original_message (StreamMessage object)
                    original_message = task_data.get("original_message")
                    message_key = original_message.message_key if hasattr(original_message, "message_key") else str(task_data.get("frame_id", ""))

                    # Create output data matching Producer expectations
                    # Producer expects: {"camera_id": str, "message_key": str, "data": {...}}
                    # IMPORTANT: post_processing_result should be at top level of "data" object
                    # Frontend expects: data.post_processing_result.agg_summary (not data.post_processing_result.data.agg_summary)

                    # Extract agg_summary from post_processed_dict if it exists
                    # post_processed_dict has structure: {"data": {"agg_summary": {...}}, "status": "success", ...}
                    # We need to flatten this so agg_summary is directly under post_processing_result
                    if isinstance(post_processed_dict, dict) and "data" in post_processed_dict:
                        # Extract the inner data and merge it with other fields
                        inner_data = post_processed_dict.pop("data", {})
                        # Merge inner_data fields directly into post_processed_dict
                        post_processed_dict.update(inner_data)

                    output_data = {
                        "camera_id": camera_id,
                        "message_key": message_key,  # Required by producer (line 408)
                        "frame_id": frame_id,  # Forced - no fallback (top-level for frame caching)
                        "input_stream": task_data.get("input_stream", {}),  # Needed for frame caching
                        "data": {  # Producer expects data wrapped in "data" key
                            "post_processing_result": post_processed_dict,  # Now flattened: agg_summary at top level
                            "model_result": model_result,
                            "metadata": task_data.get("metadata", {}),
                            "processing_time": task_data.get("processing_time", 0),
                            "stream_key": task_data.get("stream_key"),
                            "frame_id": frame_id,  # Forced - no fallback (in data for backend)
                        }
                    }

                    # Put result in output queue
                    output_queue.put(output_data)

                    # Record metrics for successfully processed frame
                    latency_ms = (time.time() - start_time) * 1000
                    if metrics:
                        metrics.record_latency(latency_ms)
                        metrics.record_throughput(count=1)

                except Exception as e:
                    # Ignore queue.Empty exceptions (timeout)
                    if "Empty" not in str(type(e)):
                        logger.error(f"Error processing task: {e}", exc_info=True)
        finally:
            # Close event loop when worker shuts down
            loop.close()
            # Mark worker as inactive when stopping and flush remaining metrics
            if metrics:
                metrics.mark_inactive()
            logger.info(f"Post-processing worker {worker_id} stopped")

    except Exception as e:
        logger.error(f"Worker {worker_id} crashed: {e}", exc_info=True)
        raise


class MultiprocessPostProcessingPool:
    """
    Pool of multiprocessing post-processing workers with per-worker queues.

    Architecture:
    - Creates multiple worker processes (4 workers for CPU-bound tasks)
    - Each worker has its OWN dedicated input queue (routed by inference workers)
    - Each process maintains isolated tracker states for assigned cameras
    - 100% order preservation per camera (no re-queuing)
    - Processes communicate via multiprocessing queues
    - True parallelism (bypasses Python GIL)
    - Metrics sent back to main process via metrics_queue for aggregation
    """

    def __init__(
        self,
        pipeline: Any,
        post_processor_config: Dict[str, Any],
        input_queues: List[mp.Queue],
        output_queue: mp.Queue,
        num_processes: int = 4,
        metrics_queue: Optional[mp.Queue] = None,
    ):
        """
        Initialize post-processing pool with per-worker queues.

        Args:
            pipeline: Reference to StreamingPipeline (not used in workers, for compatibility)
            post_processor_config: Configuration for PostProcessor initialization
            input_queues: List of mp.Queues (one per worker, routed by inference workers)
            output_queue: Single mp.Queue for producer (single-threaded)
            num_processes: Number of worker processes
            metrics_queue: Queue for sending metrics back to main process
        """
        self.pipeline = pipeline
        self.post_processor_config = post_processor_config
        self.num_processes = num_processes
        self.running = False

        # Per-worker input queues from pipeline (one per worker)
        self.input_queues = input_queues
        self.output_queue = output_queue
        self.metrics_queue = metrics_queue

        # Validate queue counts
        if len(input_queues) != num_processes:
            raise ValueError(f"Expected {num_processes} input queues, got {len(input_queues)}")

        self.processes = []

        self.logger = logging.getLogger(f"{__name__}.MultiprocessPostProcessingPool")

    def start(self):
        """Start all worker processes with dedicated queues."""
        self.running = True

        # Start worker processes (each reads from its dedicated queue)
        for i in range(self.num_processes):
            process = mp.Process(
                target=postprocessing_worker_process,
                args=(
                    i,
                    self.num_processes,
                    self.input_queues[i],  # Worker's dedicated input queue
                    self.output_queue,  # Single output queue
                    self.post_processor_config,
                    self.metrics_queue,  # For sending metrics back to main process
                ),
                daemon=True,
            )
            process.start()
            self.processes.append(process)

        self.logger.info(
            f"Started {self.num_processes} post-processing workers with dedicated queues "
            f"(metrics_queue={'enabled' if self.metrics_queue else 'disabled'})"
        )

    def stop(self):
        """Stop all worker processes."""
        self.running = False

        # Terminate processes
        for process in self.processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()

        self.processes.clear()
        self.logger.info("Stopped all post-processing worker processes")

    def submit_task(self, task_data: Dict[str, Any], timeout: float = 0.1) -> bool:
        """
        Submit task to shared worker pool queue.

        Workers pull from shared queue and route internally by camera hash.
        Camera-based routing within workers ensures:
        - Same camera always goes to same worker process
        - Tracker state remains isolated within that process
        - Per-camera ordering is preserved

        Args:
            task_data: Task data with camera_id, model_result, etc.
            timeout: Max time to wait if queue is full

        Returns:
            True if task was submitted, False if queue full (backpressure)
        """
        try:
            # Submit to shared input queue (workers handle routing internally)
            self.input_queue.put(task_data, block=True, timeout=timeout)
            return True

        except Exception:
            # Queue full - apply backpressure
            return False

    def get_result(self, timeout: float = 0.001) -> Optional[Dict[str, Any]]:
        """
        Get result from worker pool.

        Args:
            timeout: Max time to wait for result

        Returns:
            Result dict or None if no result available
        """
        try:
            return self.output_queue.get(timeout=timeout)
        except Exception:
            return None
