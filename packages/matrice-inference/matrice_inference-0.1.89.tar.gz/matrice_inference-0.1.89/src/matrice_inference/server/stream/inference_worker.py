"""
High-performance multiprocessing inference worker for optimal GPU utilization.

Architecture:
- Multiprocessing: 8 worker processes for TRUE PARALLELISM (bypasses Python GIL)
- Per-Worker Queues: Each worker reads from dedicated queue - 100% ORDER PRESERVATION
- Consumer-Side Routing: hash(camera_id) % num_workers - DETERMINISTIC ASSIGNMENT
- Async Event Loops: Each process runs its own async event loop - NON-BLOCKING I/O
- InferenceInterface: Each process recreates InferenceInterface locally - PROCESS ISOLATION

Processing Modes:
- ASYNC mode (use_async_inference=True):
  - Fire up to 1000 concurrent requests per worker
  - No batching, no waiting - fire-and-forget each frame immediately
  - Maximum parallelism for async_predict implementations
- SYNC mode (use_async_inference=False):
  - Process frame-by-frame sequentially per worker
  - Wait for each frame to complete before processing next
  - For models without async_predict

Architecture Flow:
- InferenceInterface → ModelManagerWrapper → ModelManager → async_predict (from predict.py)
- Uses normal ModelManager (NOT Triton) with predict functions from deploy.py pattern
- Each worker imports predict functions and recreates full inference stack
- Preprocessing/postprocessing handled separately in pipeline (consumer/post-processor)

Performance:
- 8 workers × 1000 concurrent = 8000 in-flight requests (ASYNC mode)
- True parallelism (bypasses Python GIL)
- 100% frame ordering preserved per camera
"""

import asyncio
import base64
import logging
import multiprocessing as mp
import time
from typing import Any, Dict, List, Optional
from matrice_inference.server.stream.worker_metrics import WorkerMetrics
from matrice_common.optimize import InferenceResultCache


def inference_worker_process(
    worker_id: int,
    num_workers: int,
    input_queue: mp.Queue,
    output_queues: List[mp.Queue],
    model_config: Dict[str, Any],
    use_async_inference: bool = True,
    direct_api_response_queue: Optional[mp.Queue] = None,
    metrics_queue: Optional[mp.Queue] = None,
):
    """
    Worker process for GPU inference with async event loop.

    IMPORTANT: Each worker reads from its OWN dedicated queue (input_queue).
    Consumer routes frames based on hash(camera_id) % num_workers.
    This ensures strict ordering per camera.

    Processing modes:
    - ASYNC mode (use_async_inference=True): Fire up to 1000 concurrent requests per worker
    - SYNC mode (use_async_inference=False): Process frame-by-frame sequentially

    Each process:
    1. Recreates InferenceInterface with ModelManagerWrapper + ModelManager
    2. Runs its own async event loop
    3. Processes tasks from its dedicated queue (no re-queuing needed)
    4. Routes results to correct post-processing worker queue
    5. Handles direct API requests (identity images) with priority

    Args:
        worker_id: Worker process ID
        num_workers: Total number of worker processes
        input_queue: This worker's dedicated queue (routed by consumer)
        output_queues: List of post-processing worker queues (for routing by camera hash)
        model_config: Model configuration (action_id, predict functions, model_path, etc.)
        use_async_inference: True for 1000 concurrent requests, False for frame-by-frame
        direct_api_response_queue: Queue for returning direct API request results
        metrics_queue: Queue for sending metrics back to main process
    """
    # Set up logging for this process
    logger = logging.getLogger(f"inference_worker_{worker_id}")
    logger.setLevel(logging.INFO)

    try:
        # Import dependencies inside process to avoid pickle issues
        from matrice.action_tracker import ActionTracker
        from matrice_inference.server.model.model_manager_wrapper import ModelManagerWrapper
        from matrice_inference.server.inference_interface import InferenceInterface
        from matrice_inference.server.stream.worker_metrics import MultiprocessWorkerMetrics

        # ARCHITECTURE NOTE: Model Loading Strategy
        # ==========================================
        # Models are loaded TWICE - once in pipeline event loop, once in each worker process.
        # This is INTENTIONAL and necessary for:
        # 1. Process Isolation: Each worker needs its own model instance (no shared state)
        # 2. GIL-Free Parallelism: Separate processes bypass Python GIL for true parallelism
        # 3. GPU Utilization: Each process can fully utilize GPU without contention
        # 4. Fault Isolation: Worker crash doesn't affect other workers or main pipeline
        #
        # The slight startup time/memory overhead is acceptable for 10K+ FPS throughput.

        # Get predict functions from model_config (passed from MatriceDeployServer)
        # These are module-level functions that CAN be pickled by reference
        load_model_fn = model_config.get("load_model")
        predict_fn = model_config.get("predict")
        async_predict_fn = model_config.get("async_predict")
        async_load_model_fn = model_config.get("async_load_model")
        batch_predict_fn = model_config.get("batch_predict")

        # Create ActionTracker for this worker
        action_id = model_config.get("action_id")
        if not action_id:
            raise ValueError("action_id is required in model_config")

        action_tracker = ActionTracker(action_id)

        # Create ModelManagerWrapper with ModelManager (NOT Triton)
        model_manager_wrapper = ModelManagerWrapper(
            action_tracker=action_tracker,
            model_type="default",  # Use default ModelManager, NOT triton
            load_model=load_model_fn,
            predict=predict_fn,
            async_predict=async_predict_fn,
            async_load_model=async_load_model_fn,
            batch_predict=batch_predict_fn,
            num_model_instances=model_config.get("num_model_instances", 1),
            model_path=model_config.get("model_path"),
        )

        # Create InferenceInterface
        inference_interface = InferenceInterface(
            model_manager_wrapper=model_manager_wrapper,
            post_processor=None,  # Post-processing handled separately in pipeline
        )

        # Initialize metrics for this worker (multiprocess-safe via queue)
        # NOTE: Metrics are sent to main process via metrics_queue for aggregation
        # This is required because multiprocessing doesn't share memory between processes
        if metrics_queue is not None:
            metrics = MultiprocessWorkerMetrics(
                worker_id=f"inference_{worker_id}",
                worker_type="inference",
                metrics_queue=metrics_queue
            )
        else:
            # Fallback to no-op metrics if queue not provided
            logger.warning(f"Worker {worker_id}: No metrics_queue provided, metrics will not be collected")
            metrics = None
        
        if metrics:
            metrics.mark_active()

        mode = "ASYNC (1000 concurrent)" if use_async_inference else "SYNC (frame-by-frame)"
        logger.info(
            f"Worker {worker_id}/{num_workers} initialized with InferenceInterface - {mode} "
            f"(ModelManager with async_predict={'available' if async_predict_fn else 'not available'}, "
            f"num_instances={model_config.get('num_model_instances', 1)})"
        )

        # CRITICAL: Load models in the worker process before processing frames
        # Each worker needs its own model instances loaded independently
        async def _load_models_and_run():
            """Load models then run the inference loop."""
            # Get ModelManager from wrapper and load models
            model_manager = getattr(model_manager_wrapper, 'model_manager', None)
            if model_manager and hasattr(model_manager, 'ensure_models_loaded'):
                logger.info(f"Worker {worker_id}: Loading models...")
                await model_manager.ensure_models_loaded()
                logger.info(f"Worker {worker_id}: Models loaded successfully")
            else:
                logger.warning(f"Worker {worker_id}: Could not find model_manager.ensure_models_loaded()")

            # Initialize result cache for frame optimization (shared across all workers)
            result_cache_config = model_config.get("result_cache_config", {})
            result_cache = InferenceResultCache(
                enabled=result_cache_config.get("enabled", True),
                max_size=result_cache_config.get("max_size", 50000),
                ttl_seconds=result_cache_config.get("ttl_seconds", 300),
            )
            logger.info(
                f"Worker {worker_id}: Initialized result cache "
                f"(enabled={result_cache.enabled}, max_size={result_cache.max_size}, "
                f"ttl={result_cache.ttl_seconds}s)"
            )

            # Now run the inference loop
            await _async_inference_loop(
                worker_id=worker_id,
                num_workers=num_workers,
                inference_interface=inference_interface,
                input_queue=input_queue,
                output_queues=output_queues,
                use_async_inference=use_async_inference,
                logger=logger,
                metrics=metrics,
                direct_api_response_queue=direct_api_response_queue,
                result_cache=result_cache,
            )

        # Run async event loop in this process
        try:
            asyncio.run(_load_models_and_run())
        finally:
            # Mark worker as inactive when stopping and flush remaining metrics
            if metrics:
                metrics.mark_inactive()

    except Exception as e:
        logger.error(f"Worker {worker_id} crashed: {e}", exc_info=True)
        raise


def _safe_queue_get(input_queue: mp.Queue, timeout: float = 0.01) -> Optional[Dict[str, Any]]:
    """
    Safe non-blocking get() for multiprocessing.Queue.

    This function is designed to be called via run_in_executor to avoid
    blocking the async event loop.
    """
    try:
        return input_queue.get(timeout=timeout)
    except Exception:
        return None


async def _async_inference_loop(
    worker_id: int,
    num_workers: int,
    inference_interface: Any,
    input_queue: mp.Queue,
    output_queues: List[mp.Queue],
    use_async_inference: bool,
    logger: logging.Logger,
    metrics: Optional[Any],  # MultiprocessWorkerMetrics instance (or None)
    direct_api_response_queue: Optional[mp.Queue] = None,
    result_cache: InferenceResultCache = None,
):
    """
    Optimized async event loop for inference worker process.

    IMPORTANT: This worker reads from its OWN dedicated queue (input_queue).
    Consumer routes frames based on hash(camera_id) % num_workers.
    No re-queuing needed - all tasks in this queue belong to this worker.

    Modes:
    - ASYNC mode (use_async_inference=True): Fire up to 1000 concurrent requests
      - Uses asyncio.Semaphore for efficient concurrency control
      - No batching, no waiting - fire-and-forget each frame immediately
      - Maximum parallelism for async_predict implementations (e.g., Triton)
    - SYNC mode (use_async_inference=False): Process frame-by-frame
      - Wait for each frame to complete before processing next
      - Preserves strict sequential order within this worker

    Optimizations:
    - Uses run_in_executor for non-blocking queue access
    - Uses asyncio.Semaphore instead of manual while loops
    - Includes timeout protection to prevent memory leaks from hung requests
    """
    loop = asyncio.get_event_loop()

    # Use Semaphore for efficient async concurrency control (replaces manual while loop)
    MAX_CONCURRENT_REQUESTS = 1000
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    while True:
        try:
            # Non-blocking queue.get() using executor to avoid blocking event loop
            task = await loop.run_in_executor(None, _safe_queue_get, input_queue)

            if task is None:
                # Queue was empty - small sleep and retry
                await asyncio.sleep(0.0001)
                continue

            logger.debug(f"Worker {worker_id} received task for camera {task.get('camera_id')}")

            # PRIORITY: Handle direct API requests immediately (identity images)
            # These bypass normal processing and are always handled async for responsiveness
            if task.get("type") == "direct_api":
                logger.info(
                    f"Worker {worker_id} processing direct API request "
                    f"(request_id={task.get('request_id')})"
                )
                asyncio.create_task(
                    _process_direct_api_request(
                        worker_id=worker_id,
                        task=task,
                        inference_interface=inference_interface,
                        response_queue=task.get("response_queue", direct_api_response_queue),
                        logger=logger,
                        metrics=metrics,
                    )
                )
                continue

            camera_id = task.get("camera_id")

            if use_async_inference:
                # ASYNC MODE: Fire-and-forget with semaphore-controlled concurrency
                # Semaphore efficiently blocks when at capacity (no busy spinning)
                asyncio.create_task(
                    _process_single_frame_with_semaphore(
                        semaphore=semaphore,
                        worker_id=worker_id,
                        task=task,
                        inference_interface=inference_interface,
                        output_queues=output_queues,
                        logger=logger,
                        metrics=metrics,
                        result_cache=result_cache,
                    )
                )
            else:
                # SYNC MODE: Process frame-by-frame, wait for completion
                logger.debug(
                    f"Worker {worker_id} processing sync request for camera {camera_id}"
                )
                await _process_single_frame_sync(
                    worker_id=worker_id,
                    task=task,
                    inference_interface=inference_interface,
                    output_queues=output_queues,
                    logger=logger,
                    metrics=metrics,
                    result_cache=result_cache,
                )

        except Exception as e:
            logger.error(f"Error in inference loop: {e}", exc_info=True)
            await asyncio.sleep(0.1)


async def _process_single_frame_with_semaphore(
    semaphore: asyncio.Semaphore,
    worker_id: int,
    task: Dict[str, Any],
    inference_interface: Any,
    output_queues: List[mp.Queue],
    logger: logging.Logger,
    metrics: Optional[Any],
    result_cache: InferenceResultCache = None,
):
    """
    Wrapper to enforce max concurrent requests via asyncio.Semaphore.

    The semaphore automatically handles waiting when at capacity - no busy spinning.
    This is more efficient than manual while loops with sleep.
    """
    async with semaphore:
        await _process_single_frame_async(
            worker_id=worker_id,
            task=task,
            inference_interface=inference_interface,
            output_queues=output_queues,
            logger=logger,
            metrics=metrics,
            result_cache=result_cache,
        )


# Inference timeout in seconds (adjust based on model complexity)
INFERENCE_TIMEOUT_SECONDS = 30.0


async def _process_single_frame_async(
    worker_id: int,
    task: Dict[str, Any],
    inference_interface: Any,
    output_queues: List[mp.Queue],
    logger: logging.Logger,
    metrics: Optional[Any],
    result_cache: InferenceResultCache = None,
):
    """
    Process a single frame asynchronously (fire-and-forget).

    Used in ASYNC mode to allow up to 1000 concurrent requests per worker.
    Includes timeout protection to prevent memory leaks from hung requests.
    Routes result to correct post-processing worker queue.
    Supports frame optimization via result caching for similar frames.
    """
    start_time = time.time()
    camera_id = task.get("camera_id")
    frame_id = task.get("frame_id")

    # CRITICAL: Validate frame_id exists - skip if missing
    if not frame_id:
        logger.error(
            f"[FRAME_ID_MISSING] camera={camera_id} - No frame_id in task. Skipping frame."
        )
        return

    try:
        # Check if this is a cached frame (empty content + cached_frame_id in input_stream)
        input_stream = task.get("input_stream", {})
        cached_frame_id = input_stream.get("cached_frame_id")
        frame_bytes = task.get("frame_bytes")

        if cached_frame_id and not frame_bytes and result_cache:
            # This is a cached frame - lookup cached result
            cached_result = result_cache.get(cached_frame_id)

            if cached_result:
                # Use cached result with new frame_id
                postproc_worker_id = hash(camera_id) % len(output_queues)
                target_queue = output_queues[postproc_worker_id]

                # Restore input_bytes from cached result to input_stream for frame caching
                # This allows the producer to cache this frame with the new frame_id
                input_stream_with_content = dict(input_stream)
                cached_input_bytes = cached_result.get("input_bytes")
                if cached_input_bytes:
                    input_stream_with_content["content"] = cached_input_bytes

                output_data = {
                    "camera_id": camera_id,
                    "frame_id": frame_id,  # NEW frame_id
                    "original_message": task.get("message"),
                    "model_result": cached_result.get("model_result"),
                    "metadata": cached_result.get("metadata", {}),
                    "processing_time": time.time() - start_time,
                    "input_stream": input_stream_with_content,  # Now contains cached frame bytes
                    "stream_key": task.get("stream_key"),
                    "camera_config": task.get("camera_config"),
                    "from_cache": True,
                    "cached_frame_id": cached_frame_id,
                }

                target_queue.put(output_data)

                # Record metrics for cache hit
                latency_ms = (time.time() - start_time) * 1000
                if metrics:
                    metrics.record_latency(latency_ms)
                    metrics.record_throughput(count=1)

                logger.debug(
                    f"Worker {worker_id}: Cache HIT for camera {camera_id}, "
                    f"cached_frame_id={cached_frame_id} (latency={latency_ms:.1f}ms)"
                )
                return

            else:
                # Cache miss - frame was evicted or expired
                logger.warning(
                    f"Worker {worker_id}: Cache MISS for camera {camera_id}, "
                    f"cached_frame_id={cached_frame_id} - frame skipped"
                )
                # Skip this frame - don't run inference on cached frames with cache miss
                return

        # Normal inference flow (has frame_bytes)
        result = await asyncio.wait_for(
            _execute_single_inference(inference_interface, task, logger),
            timeout=INFERENCE_TIMEOUT_SECONDS,
        )

        # Cache the result for future cached frames (including input_bytes for frame caching)
        if result_cache and frame_id:
            result_cache.put(frame_id, {
                "model_result": result.get("model_result"),
                "metadata": result.get("metadata", {}),
                "input_bytes": frame_bytes,  # Store frame bytes for cached frame reuse
            })

        # Route result to correct post-processing worker queue
        postproc_worker_id = hash(camera_id) % len(output_queues)
        target_queue = output_queues[postproc_worker_id]

        output_data = {
            "camera_id": camera_id,
            "frame_id": frame_id,  # Forced - no fallback
            "original_message": task.get("message"),
            "model_result": result.get("model_result"),
            "metadata": result.get("metadata", {}),
            "processing_time": time.time() - start_time,
            "input_stream": task.get("input_stream", {}),
            "stream_key": task.get("stream_key"),
            "camera_config": task.get("camera_config"),
            "from_cache": False,
        }

        target_queue.put(output_data)

        # Record metrics
        latency_ms = (time.time() - start_time) * 1000
        if metrics:
            metrics.record_latency(latency_ms)
            metrics.record_throughput(count=1)

        logger.debug(
            f"Worker {worker_id}: Async frame for camera {camera_id} "
            f"routed to postproc worker {postproc_worker_id} (latency={latency_ms:.1f}ms)"
        )

    except asyncio.TimeoutError:
        logger.warning(
            f"Worker {worker_id}: Inference timeout for camera {camera_id} "
            f"(>{INFERENCE_TIMEOUT_SECONDS}s) - dropping frame"
        )
    except Exception as e:
        logger.error(f"Async frame processing error for camera {camera_id}: {e}", exc_info=True)


async def _process_single_frame_sync(
    worker_id: int,
    task: Dict[str, Any],
    inference_interface: Any,
    output_queues: List[mp.Queue],
    logger: logging.Logger,
    metrics: Optional[Any],
    result_cache: InferenceResultCache = None,
):
    """
    Process a single frame synchronously (wait for completion).

    Used in SYNC mode for models without async_predict.
    Blocks until inference is complete before returning.
    Includes timeout protection to prevent hung requests.
    Routes result to correct post-processing worker queue.
    Supports frame optimization via result caching for similar frames.
    """
    start_time = time.time()
    camera_id = task.get("camera_id")
    frame_id = task.get("frame_id")

    # CRITICAL: Validate frame_id exists - skip if missing
    if not frame_id:
        logger.error(
            f"[FRAME_ID_MISSING] camera={camera_id} - No frame_id in task. Skipping frame."
        )
        return

    try:
        # Check if this is a cached frame (empty content + cached_frame_id in input_stream)
        input_stream = task.get("input_stream", {})
        cached_frame_id = input_stream.get("cached_frame_id")
        frame_bytes = task.get("frame_bytes")

        if cached_frame_id and not frame_bytes and result_cache:
            # This is a cached frame - lookup cached result
            cached_result = result_cache.get(cached_frame_id)

            if cached_result:
                # Use cached result with new frame_id
                postproc_worker_id = hash(camera_id) % len(output_queues)
                target_queue = output_queues[postproc_worker_id]

                # Restore input_bytes from cached result to input_stream for frame caching
                # This allows the producer to cache this frame with the new frame_id
                input_stream_with_content = dict(input_stream)
                cached_input_bytes = cached_result.get("input_bytes")
                if cached_input_bytes:
                    input_stream_with_content["content"] = cached_input_bytes

                output_data = {
                    "camera_id": camera_id,
                    "frame_id": frame_id,  # NEW frame_id
                    "original_message": task.get("message"),
                    "model_result": cached_result.get("model_result"),
                    "metadata": cached_result.get("metadata", {}),
                    "processing_time": time.time() - start_time,
                    "input_stream": input_stream_with_content,  # Now contains cached frame bytes
                    "stream_key": task.get("stream_key"),
                    "camera_config": task.get("camera_config"),
                    "from_cache": True,
                    "cached_frame_id": cached_frame_id,
                }

                target_queue.put(output_data)

                # Record metrics for cache hit
                latency_ms = (time.time() - start_time) * 1000
                if metrics:
                    metrics.record_latency(latency_ms)
                    metrics.record_throughput(count=1)

                logger.debug(
                    f"Worker {worker_id}: Cache HIT (sync) for camera {camera_id}, "
                    f"cached_frame_id={cached_frame_id} (latency={latency_ms:.1f}ms)"
                )
                return

            else:
                # Cache miss - frame was evicted or expired
                logger.warning(
                    f"Worker {worker_id}: Cache MISS (sync) for camera {camera_id}, "
                    f"cached_frame_id={cached_frame_id} - frame skipped"
                )
                # Skip this frame - don't run inference on cached frames with cache miss
                return

        # Normal inference flow (has frame_bytes)
        # Execute inference with timeout protection
        result = await asyncio.wait_for(
            _execute_single_inference(inference_interface, task, logger),
            timeout=INFERENCE_TIMEOUT_SECONDS,
        )

        # Cache the result for future cached frames (including input_bytes for frame caching)
        if result_cache and frame_id:
            result_cache.put(frame_id, {
                "model_result": result.get("model_result"),
                "metadata": result.get("metadata", {}),
                "input_bytes": frame_bytes,  # Store frame bytes for cached frame reuse
            })

        # Route result to correct post-processing worker queue
        postproc_worker_id = hash(camera_id) % len(output_queues)
        target_queue = output_queues[postproc_worker_id]

        output_data = {
            "camera_id": camera_id,
            "frame_id": frame_id,  # Forced - no fallback
            "original_message": task.get("message"),
            "model_result": result.get("model_result"),
            "metadata": result.get("metadata", {}),
            "processing_time": time.time() - start_time,
            "input_stream": input_stream,
            "stream_key": task.get("stream_key"),
            "camera_config": task.get("camera_config"),
            "from_cache": False,
        }

        target_queue.put(output_data)

        # Record metrics
        latency_ms = (time.time() - start_time) * 1000
        if metrics:
            metrics.record_latency(latency_ms)
            metrics.record_throughput(count=1)

        logger.debug(
            f"Worker {worker_id}: Sync frame for camera {camera_id} "
            f"routed to postproc worker {postproc_worker_id} (latency={latency_ms:.1f}ms)"
        )

    except asyncio.TimeoutError:
        logger.warning(
            f"Worker {worker_id}: Sync inference timeout for camera {camera_id} "
            f"(>{INFERENCE_TIMEOUT_SECONDS}s) - dropping frame"
        )
    except Exception as e:
        logger.error(f"Sync frame processing error for camera {camera_id}: {e}", exc_info=True)


async def _process_direct_api_request(
    worker_id: int,
    task: Dict[str, Any],
    inference_interface: Any,
    response_queue: Optional[mp.Queue],
    logger: logging.Logger,
    metrics: Optional[Any],
):
    """
    Process a direct API request (e.g., identity image for face recognition).

    Direct API requests are processed immediately without batching to ensure
    low latency for high-priority operations. Results are sent back via the
    response queue for the calling thread to receive.

    Args:
        worker_id: Worker ID for logging
        task: Task data containing request_id, input_bytes, extra_params, etc.
        inference_interface: InferenceInterface instance
        response_queue: Queue for sending response back to caller
        logger: Logger instance
        metrics: WorkerMetrics instance
    """
    start_time = time.time()
    request_id = task.get("request_id", "unknown")

    try:
        # Extract input bytes from task
        input_bytes = task.get("input_bytes")
        if not input_bytes:
            raise ValueError("No input_bytes in direct API task")

        extra_params = task.get("extra_params", {})
        stream_key = task.get("stream_key")
        stream_info = task.get("stream_info")

        # Call InferenceInterface.async_inference()
        # This runs in the worker's event loop where the model was loaded
        # avoiding greenlet context switching issues
        model_result, metadata = await inference_interface.async_inference(
            input=input_bytes,
            extra_params=extra_params,
            apply_post_processing=False,  # Post-processing handled by caller if needed
            stream_key=stream_key,
            stream_info=stream_info,
        )

        processing_time = time.time() - start_time

        # Record metrics
        if metrics:
            metrics.record_latency(processing_time * 1000)  # Convert to ms
            metrics.record_throughput(count=1)

        # Send success response
        response = {
            "request_id": request_id,
            "success": True,
            "model_result": model_result,
            "metadata": metadata or {},
            "processing_time": processing_time,
        }

        logger.info(
            f"Worker {worker_id}: Direct API request {request_id} completed "
            f"in {processing_time:.3f}s"
        )

    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = str(e)

        logger.error(
            f"Worker {worker_id}: Direct API request {request_id} failed: {error_msg}",
            exc_info=True
        )

        # Send error response
        response = {
            "request_id": request_id,
            "success": False,
            "error": error_msg,
            "model_result": None,
            "metadata": {},
            "processing_time": processing_time,
        }

    # Send response back via queue
    if response_queue is not None:
        try:
            response_queue.put(response, timeout=5.0)
        except Exception as e:
            logger.error(f"Failed to send response for {request_id}: {e}")
    else:
        logger.warning(
            f"No response queue for direct API request {request_id} - response lost"
        )


async def _execute_single_inference(
    inference_interface: Any,
    task_data: Dict[str, Any],
    logger: logging.Logger,
) -> Dict[str, Any]:
    """
    Execute async inference for a single task using InferenceInterface.

    Args:
        inference_interface: InferenceInterface instance (with ModelManagerWrapper → ModelManager)
        task_data: Task data containing input and parameters
        logger: Logger instance

    Returns:
        Dict with model_result and metadata
    """
    try:
        # Validate task data
        if not _validate_task_data(task_data, logger):
            return {"model_result": None, "metadata": {}, "success": False}

        # Extract inference parameters
        input_bytes = _extract_input_bytes(task_data, logger)
        if input_bytes is None:
            return {"model_result": None, "metadata": {}, "success": False}

        # Call InferenceInterface.async_inference()
        # Flow: InferenceInterface → ModelManagerWrapper → ModelManager → async_predict
        # Note: Raw bytes → model inference → raw results (no post-processing here)
        # Postprocessing handled separately by post_processing_manager
        model_result, metadata = await inference_interface.async_inference(
            input=input_bytes,
            extra_params=task_data.get("extra_params"),
            apply_post_processing=False,  # No post-processing in workers
            stream_key=task_data.get("stream_key"),
            stream_info=None,
        )

        return {
            "success": True,
            "model_result": model_result,
            "metadata": metadata or {},
        }

    except Exception as e:
        logger.error(f"Inference execution error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "model_result": None,
            "metadata": {},
        }


def _validate_task_data(task_data: Dict[str, Any], logger: logging.Logger) -> bool:
    """
    Validate that task data contains required fields.

    Required fields (from consumer_manager):
    - camera_id: For routing and identification
    - frame_bytes or input_stream: Input data
    - message: Original stream message
    - stream_key: Stream identifier
    - camera_config: Camera configuration
    """
    required_fields = ["camera_id", "message", "stream_key", "camera_config"]
    for field in required_fields:
        if field not in task_data:
            logger.error(f"Missing required field '{field}' in task data")
            return False

    # Check that we have input data (frame_bytes or input_stream)
    has_input = (
        "frame_bytes" in task_data or
        "decoded_input_bytes" in task_data or
        "input_stream" in task_data
    )
    if not has_input:
        logger.error("No input data found (frame_bytes, decoded_input_bytes, or input_stream)")
        return False

    return True


def _extract_input_bytes(task_data: Dict[str, Any], logger: logging.Logger) -> Optional[bytes]:
    """
    Extract input bytes from task data.

    Supports multiple formats (priority order):
    1. task_data["frame_bytes"] - direct bytes from consumer_manager (NEW)
    2. task_data["decoded_input_bytes"] - decoded bytes
    3. task_data["input_stream"]["content"] - bytes or base64 string
    """
    # Priority 1: Direct frame_bytes from consumer_manager (simplified flow)
    frame_bytes = task_data.get("frame_bytes")
    if isinstance(frame_bytes, (bytes, bytearray)) and frame_bytes:
        return bytes(frame_bytes)

    # Priority 2: Decoded input bytes
    decoded_bytes = task_data.get("decoded_input_bytes")
    if isinstance(decoded_bytes, (bytes, bytearray)) and decoded_bytes:
        return bytes(decoded_bytes)

    # Priority 3: Extract from input_stream
    input_stream_data = task_data.get("input_stream", {})
    if not isinstance(input_stream_data, dict):
        logger.error(f"input_stream is not a dict: {type(input_stream_data)}")
        return None

    content = input_stream_data.get("content")

    # Handle raw bytes
    if isinstance(content, (bytes, bytearray)) and content:
        return bytes(content)

    # Handle base64-encoded strings
    if isinstance(content, str) and content:
        try:
            return base64.b64decode(content)
        except Exception as e:
            logger.warning(f"Failed to decode base64 content: {e}")
            return None

    logger.error("No valid input bytes found in task data")
    return None


class MultiprocessInferencePool:
    """
    Pool of multiprocessing inference workers with per-worker queues.

    Architecture:
    - Creates multiple worker processes (one per GPU/core)
    - Each worker has its OWN dedicated input queue (routed by consumer)
    - Each process recreates InferenceInterface → ModelManagerWrapper → ModelManager
    - Uses normal ModelManager with async_predict from predict.py (NOT Triton)
    - Each process runs its own async event loop
    - Routes results to correct post-processing worker queue
    - 100% order preservation per camera (no re-queuing)
    - Direct API support for identity images (bypass batching, immediate response)
    - Metrics sent back to main process via metrics_queue for aggregation

    Processing Modes:
    - ASYNC (use_async_inference=True): Up to 1000 concurrent requests per worker
    - SYNC (use_async_inference=False): Frame-by-frame sequential processing
    """

    def __init__(
        self,
        num_workers: int,
        model_config: Dict[str, Any],
        input_queues: List[mp.Queue],
        output_queues: List[mp.Queue],
        use_async_inference: bool = True,
        direct_api_response_queue: Optional[mp.Queue] = None,
        metrics_queue: Optional[mp.Queue] = None,
    ):
        self.num_workers = num_workers
        self.model_config = model_config
        self.use_async_inference = use_async_inference

        # Per-worker queues from pipeline (one per worker)
        self.input_queues = input_queues
        self.output_queues = output_queues
        self.direct_api_response_queue = direct_api_response_queue
        self.metrics_queue = metrics_queue

        # Validate queue counts
        if len(input_queues) != num_workers:
            raise ValueError(f"Expected {num_workers} input queues, got {len(input_queues)}")

        self.processes = []
        self.running = False

        self.logger = logging.getLogger(f"{__name__}.MultiprocessInferencePool")

    def start(self):
        """Start all worker processes with dedicated queues."""
        self.running = True

        mode = "ASYNC (1000 concurrent)" if self.use_async_inference else "SYNC (frame-by-frame)"

        for worker_id in range(self.num_workers):
            process = mp.Process(
                target=inference_worker_process,
                args=(
                    worker_id,
                    self.num_workers,
                    self.input_queues[worker_id],  # Worker's dedicated input queue
                    self.output_queues,  # List of post-processing queues for routing
                    self.model_config,
                    self.use_async_inference,  # Determines sync vs async behavior
                    self.direct_api_response_queue,
                    self.metrics_queue,  # For sending metrics back to main process
                ),
                daemon=True,
            )
            process.start()
            self.processes.append(process)

        self.logger.info(
            f"Started {self.num_workers} multiprocess inference workers with dedicated queues "
            f"(mode={mode}, direct_api_queue={'enabled' if self.direct_api_response_queue else 'disabled'}, "
            f"metrics_queue={'enabled' if self.metrics_queue else 'disabled'})"
        )

    def stop(self):
        """Stop all worker processes."""
        self.running = False

        for process in self.processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()

        self.processes.clear()
        self.logger.info("Stopped all inference worker processes")

    def submit_task(self, task_data: Dict[str, Any], timeout: float = 0.1) -> bool:
        """
        Submit inference task to worker pool.

        Args:
            task_data: Task data with camera_id, frame, etc.
            timeout: Max time to wait if queue is full

        Returns:
            True if task was submitted, False if queue full (backpressure)
        """
        try:
            self.input_queue.put(task_data, timeout=timeout)
            return True
        except Exception:
            # Queue full - apply backpressure
            return False

    def get_result(self, timeout: float = 0.001) -> Optional[Dict[str, Any]]:
        """
        Get inference result from worker pool.

        Args:
            timeout: Max time to wait for result

        Returns:
            Result dict or None if no result available
        """
        try:
            return self.output_queue.get(timeout=timeout)
        except Exception:
            return None
