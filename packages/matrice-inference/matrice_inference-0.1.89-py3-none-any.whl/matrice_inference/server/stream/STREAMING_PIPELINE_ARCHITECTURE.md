# Streaming Pipeline Architecture - Server Side

> **Comprehensive documentation for the high-performance streaming inference pipeline**

## Table of Contents

1. [Overview](#overview)
2. [Architecture Design](#architecture-design)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [Queue Architecture](#queue-architecture)
6. [Metrics System](#metrics-system)
7. [Camera Management](#camera-management)
8. [Performance Characteristics](#performance-characteristics)
9. [Code Reference](#code-reference)

---

## Overview

The streaming pipeline is a high-performance, distributed system designed to process video inference at scale. It handles **1000+ camera streams** concurrently with target throughput of **10,000 FPS** and latency under **500ms (P50)**.

### Key Features

- **Hybrid Architecture**: Combines asyncio (I/O-bound) with multiprocessing (CPU-bound)
- **True Parallelism**: Multiprocessing workers bypass Python's GIL for CPU-intensive tasks
- **Shared Queue Model**: Single shared `multiprocessing.Queue` per stage (simplified from per-camera queues)
- **Dynamic Camera Management**: Add/remove cameras without pipeline restart
- **Built-in Metrics**: Real-time performance monitoring with Kafka publishing
- **Backpressure Handling**: Queue-based flow control prevents OOM

### Performance Targets

| Metric | Target |
|--------|--------|
| Throughput | 10,000 FPS |
| Latency (P50) | < 500ms |
| Latency (P99) | < 800ms |
| GPU Utilization | 85%+ |
| Concurrent Cameras | 1000+ |

---

## Architecture Design

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Streaming Pipeline                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐       │
│  │   Consumer   │ ───> │  Inference   │ ───> │ Post-Process │ ───>  │
│  │   Manager    │      │    Workers   │      │   Workers    │       │
│  │  (Async)     │      │ (Multiproc)  │      │ (Multiproc)  │       │
│  └──────────────┘      └──────────────┘      └──────────────┘       │
│         │                      │                      │             │
│         │ mp.Queue             │ mp.Queue             │ mp.Queue    │
│         │ (inference)          │ (postproc)           │ (output)    │
│         v                      v                      v             │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │                    Producer Workers                      │       │
│  │                      (Threading)                         │       │
│  └──────────────────────────────────────────────────────────┘       │
│                                │                                    │
└────────────────────────────────┼────────────────────────────────────┘
                                 │
                                 v
                          Kafka/Redis Output
```

### Architecture Principles

1. **Async for I/O**: Consumer and Producer use asyncio for non-blocking stream operations
2. **Multiprocessing for CPU**: Inference and post-processing use separate processes for true parallelism
3. **Shared Queues**: Single `multiprocessing.Queue` per stage reduces complexity
4. **Camera-based Routing**: Hash-based routing ensures consistent worker assignment per camera
5. **Isolated State**: Post-processing workers maintain per-camera tracker states

---

## Component Details

### 1. Consumer Manager (`AsyncConsumerManager`)

**Purpose**: Consume messages from 1000+ camera streams asynchronously

**Architecture**:

- **Type**: Single async event loop
- **Location**: `src/matrice_inference/server/stream/consumer_manager.py`
- **Pattern**: One async task per camera (all in same event loop)

**Key Responsibilities**:

- Read from Kafka/Redis streams (async, non-blocking)
- Extract frame bytes from stream messages
- Validate and enrich metadata (frame_id, camera_id)
- Enqueue tasks to inference queue via `loop.run_in_executor()`
- Handle backpressure (drop frames if queue full)

**Metrics Tracked**:

- Latency per message (ms)
- Throughput (messages consumed)
- Worker status (active/inactive)

**Code Flow**:

```python
# src/matrice_inference/server/stream/consumer_manager.py:227-258

async def _consume_camera(camera_id, config):
    """Per-camera async consumer loop"""
    while running:
        message_data = await stream.async_get_message(timeout)
        await _process_message(camera_id, config, message_data)

async def _process_message(camera_id, camera_config, message_data):
    """Extract bytes and enqueue for inference"""
    frame_bytes = _extract_frame_bytes(input_stream)
    task_data = {
        "camera_id": camera_id,
        "frame_bytes": frame_bytes,  # Direct bytes
        "frame_id": frame_id,
        ...
    }
    await _enqueue_task(camera_id, task_data)

    # Record metrics
    metrics.record_latency(latency_ms)
    metrics.record_throughput(count=1)
```

---

### 2. Inference Workers (`MultiprocessInferencePool`)

**Purpose**: Perform GPU inference with dynamic batching

**Architecture**:

- **Type**: Multiprocessing pool (4-8 workers)
- **Location**: `src/matrice_inference/server/stream/inference_worker.py`
- **Pattern**: Each process runs its own async event loop

**Key Responsibilities**:

- Dynamic batching (accumulate requests for `batch_timeout_ms` or until `batch_size`)
- Concurrent inference requests (multiple batches in-flight per worker)
- Camera-based routing (`hash(camera_id) % num_workers`)
- GPU model execution via `InferenceInterface`

**Configuration**:

```python
num_workers = 4-8  # One per GPU/core
batch_size = 4  # Target batch size
batch_timeout_ms = 10.0  # Max wait for batch accumulation
max_concurrent_requests = 3  # Max in-flight batches per worker
```

**Metrics Tracked**:

- Batch latency (ms)
- Throughput (frames processed)
- Worker status (active/inactive)

**Code Flow**:

```python
# src/matrice_inference/server/stream/inference_worker.py:144-230

async def _async_inference_loop(...):
    """Async event loop in each worker process"""
    batch_buffer = []

    while True:
        # Accumulate tasks
        task = input_queue.get(timeout=0.001)
        if hash(task["camera_id"]) % num_workers == worker_id:
            batch_buffer.append(task)

        # Process when ready
        if should_process_batch():
            asyncio.create_task(
                _process_batch_async(batch_buffer, metrics)
            )

async def _process_batch_async(batch, metrics):
    """Process batch concurrently"""
    for task in batch:
        result = await inference_interface.async_inference(...)
        output_queue.put(result)

    # Record metrics
    metrics.record_latency(latency_ms)
    metrics.record_throughput(count=len(batch))
```

**Model Loading**:

- Each worker process independently loads the model via `InferenceInterface`
- Uses `ModelManagerWrapper` → `ModelManager` → `async_predict` from `predict.py`
- No shared model instances across processes (true isolation)

---

### 3. Post-Processing Workers (`MultiprocessPostProcessingPool`)

**Purpose**: CPU-bound post-processing with stateful tracking

**Architecture**:

- **Type**: Multiprocessing pool (2-4 workers)
- **Location**: `src/matrice_inference/server/stream/post_processing_manager.py`
- **Pattern**: Blocking processing loop per worker

**Key Responsibilities**:

- Stateful object tracking per camera
- Per-camera tracker state isolation
- Camera-based routing (same camera → same worker)
- Analytics aggregation

**Configuration**:

```python
num_workers = 2-4  # CPU-bound workers
# Camera routing ensures same camera always goes to same worker
```

**Metrics Tracked**:

- Processing latency (ms)
- Throughput (frames processed)
- Worker status (active/inactive)

**Code Flow**:

```python
# src/matrice_inference/server/stream/post_processing_manager.py:74-128

def postprocessing_worker_process(...):
    """Worker process with isolated tracker states"""
    metrics = WorkerMetrics.get_shared("post_processing")
    metrics.mark_active()

    tracker_states = {}  # Per-camera trackers

    while True:
        task_data = input_queue.get(timeout=1.0)
        camera_id = task_data["camera_id"]

        # Get or create tracker for this camera
        if camera_id not in tracker_states:
            tracker_states[camera_id] = post_processor.create_tracker()

        # Process with stateful tracking
        result = post_processor.process(
            data=model_result,
            tracker_state=tracker_states[camera_id],
            camera_id=camera_id
        )

        output_queue.put(output_data)

        # Record metrics
        metrics.record_latency(latency_ms)
        metrics.record_throughput(count=1)
```

**State Isolation**:

- Each worker maintains trackers for its assigned cameras only
- Camera routing: `hash(camera_id) % num_workers`
- Tracker states never shared across processes

---

### 4. Producer Workers (`ProducerWorker`)

**Purpose**: Publish results to output streams

**Architecture**:

- **Type**: Threading (one thread per worker)
- **Location**: `src/matrice_inference/server/stream/producer_worker.py`
- **Pattern**: Async event loop in each thread

**Key Responsibilities**:

- Read from output queue via `loop.run_in_executor()`
- Publish to Kafka/Redis output streams (async)
- Frame caching to Redis (moved from consumer)
- Analytics data forwarding

**Metrics Tracked**:

- Message latency (ms)
- Throughput (messages published)
- Worker status (active/inactive)

**Code Flow**:

```python
# src/matrice_inference/server/stream/producer_worker.py:160-179

async def _async_process_messages():
    """Async message processing loop"""
    while running:
        task = await _get_task_from_queue()  # Uses run_in_executor
        if task:
            await _send_message_safely(task)

            # Record metrics
            metrics.record_latency(latency_ms)
            metrics.record_throughput(count=1)

async def _get_task_from_queue():
    """Get task from shared mp.Queue"""
    loop = asyncio.get_running_loop()
    task_data = await loop.run_in_executor(
        None,
        output_queue.get,  # Blocking mp.Queue operation
        True,  # block=True
        0.1    # timeout
    )
    return task_data
```

---

## Data Flow

### Complete Pipeline Flow

```
1. Stream Message Arrival (Kafka/Redis)
   ↓
2. AsyncConsumerManager._consume_camera()
   - Async read from stream
   - Extract frame bytes
   - Enrich metadata
   ↓
3. Enqueue to inference_queue (mp.Queue)
   - Via loop.run_in_executor()
   - Backpressure if queue full
   ↓
4. InferenceWorker reads from inference_queue
   - Camera-based routing (hash % num_workers)
   - Dynamic batching
   - Concurrent inference requests
   ↓
5. GPU Inference (InferenceInterface)
   - async_predict() via ModelManager
   - Multiple batches in-flight
   ↓
6. Enqueue to postproc_queue (mp.Queue)
   - Put result with metadata
   ↓
7. PostProcessingWorker reads from postproc_queue
   - Get or create per-camera tracker
   - Stateful tracking
   - Analytics aggregation
   ↓
8. Enqueue to output_queue (mp.Queue)
   - Put result with post-processing data
   ↓
9. ProducerWorker reads from output_queue
   - Via loop.run_in_executor()
   - Cache frame to Redis
   - Validate output data
   ↓
10. Publish to Output Stream (Kafka/Redis)
    - Async publish
    - Forward to analytics publisher
```

### Data Structure Evolution

**1. Consumer Output → Inference Input**:

```python
{
    "camera_id": "camera_001",
    "frame_bytes": b"...",  # Raw frame bytes
    "frame_id": "uuid-or-message-key",
    "message": StreamMessage(...),
    "input_stream": {...},
    "stream_key": "camera_001",
    "extra_params": {...},
    "camera_config": CameraConfig(...)
}
```

**2. Inference Output → Post-Processing Input**:

```python
{
    "camera_id": "camera_001",
    "frame_id": "uuid-or-message-key",
    "original_message": StreamMessage(...),
    "model_result": [...],  # Raw model output
    "metadata": {...},
    "processing_time": 0.123,
    "input_stream": {...},
    "stream_key": "camera_001",
    "camera_config": CameraConfig(...)
}
```

**3. Post-Processing Output → Producer Input**:

```python
{
    "camera_id": "camera_001",
    "frame_id": "uuid-or-message-key",
    "original_message": StreamMessage(...),
    "model_result": [...],
    "post_processed_result": {  # Added by post-processor
        "tracked_objects": [...],
        "agg_summary": {...},
        ...
    },
    "metadata": {...},
    "processing_time": 0.145,
    "input_stream": {...},
    "stream_key": "camera_001",
    "camera_config": CameraConfig(...)
}
```

**4. Producer Output → Stream**:

```python
{
    "model_result": [...],
    "post_processing_result": {
        "tracked_objects": [...],
        "agg_summary": {...}
    },
    "metadata": {...},
    "timestamp": "2025-01-23T10:30:45Z"
}
```

---

## Queue Architecture

### Shared Multiprocessing Queue Design

**Before (Per-Camera Queues)**:

```python
# ❌ Old architecture - 3000 queues total
inference_queues: Dict[str, asyncio.Queue] = {}  # 1000 queues
postproc_queues: Dict[str, asyncio.Queue] = {}   # 1000 queues
output_queues: Dict[str, asyncio.Queue] = {}     # 1000 queues
```

**After (Shared Queues)**:

```python
# ✅ New architecture - 3 queues total
import multiprocessing as mp

inference_queue = mp.Queue(maxsize=5000)  # Shared by all cameras
postproc_queue = mp.Queue(maxsize=5000)   # Shared by all cameras
output_queue = mp.Queue(maxsize=5000)     # Shared by all cameras
```

### Benefits of Shared Queue Model

1. **Simplicity**:
   - Reduced from 3000 queues to 3 queues
   - No per-camera queue management needed
   - No dispatcher bridges required

2. **Performance**:
   - Lower memory overhead
   - Better cache locality
   - Automatic load balancing

3. **Scalability**:
   - Easy to add/remove cameras (no queue creation/deletion)
   - Workers naturally balance load via queue polling

### Queue Integration Patterns

**Async → Multiprocessing Queue (Consumer to Inference)**:

```python
# src/matrice_inference/server/stream/consumer_manager.py:336-360

async def _enqueue_task(camera_id, task_data):
    """Async write to mp.Queue without blocking event loop"""
    inference_queue = self.pipeline.inference_queue

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,  # Use default executor
        inference_queue.put,
        task_data,
        True,  # block=True
        0.1    # timeout (seconds)
    )
```

**Multiprocessing Queue → Multiprocessing Queue (Inference to Post-Processing)**:

```python
# src/matrice_inference/server/stream/inference_worker.py:278

# Direct put - both sides are multiprocessing
output_queue.put(output_data)
```

**Multiprocessing Queue → Async (Producer)**:

```python
# src/matrice_inference/server/stream/producer_worker.py:181-201

async def _get_task_from_queue():
    """Async read from mp.Queue without blocking event loop"""
    loop = asyncio.get_running_loop()
    task_data = await loop.run_in_executor(
        None,
        self.output_queue.get,
        True,  # block=True
        0.1    # timeout
    )
    return task_data
```

### Backpressure Handling

When a queue is full:

1. **Consumer**: Drops frame and logs warning (prevents blocking stream reads)
2. **Inference**: Puts back in queue if not for this worker (camera routing)
3. **Post-Processing**: Blocks with timeout (preserves processing order)
4. **Producer**: Blocks with timeout (ensures delivery)

---

## Metrics System

### Architecture

The metrics system uses **shared WorkerMetrics instances** per worker type to minimize memory and simplify aggregation.

```
┌─────────────────────────────────────────────────────────────┐
│                  WorkerMetrics (Class-Level)                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  _shared_instances = {                                        │
│    "consumer": WorkerMetrics(worker_type="consumer"),        │
│    "inference": WorkerMetrics(worker_type="inference"),      │
│    "post_processing": WorkerMetrics(...),                    │
│    "producer": WorkerMetrics(...)                            │
│  }                                                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
         │                │                │              │
         │                │                │              │
         v                v                v              v
    Consumer      Inference (×8)   Post-Proc (×4)   Producer (×N)
    Manager         Workers           Workers         Workers
```

### Metrics Per Worker Type

**Consumer** (`WorkerMetrics.get_shared("consumer")`):

- Latency: Time to consume and enqueue message
- Throughput: Messages consumed per interval
- Status: Active/inactive

**Inference** (`WorkerMetrics.get_shared("inference")`):

- Latency: Batch processing time (including GPU inference)
- Throughput: Frames inferred per interval
- Status: Active/inactive

**Post-Processing** (`WorkerMetrics.get_shared("post_processing")`):

- Latency: Time to process and track
- Throughput: Frames post-processed per interval
- Status: Active/inactive

**Producer** (`WorkerMetrics.get_shared("producer")`):

- Latency: Time to publish message
- Throughput: Messages published per interval
- Status: Active/inactive

### Metric Collection Flow

```python
# src/matrice_inference/server/stream/inference_metric_logger.py:279-334

class InferenceMetricLogger:
    """Background aggregator running on threading.Timer"""

    def _collect_worker_snapshots(interval_start, interval_end):
        """Collect from all worker types"""
        snapshots = []

        # Consumer (AsyncConsumerManager instance)
        snapshot = pipeline.consumer_manager.metrics.snapshot_and_reset(...)
        snapshots.append(snapshot)

        # Inference (shared class-level metrics)
        metrics = WorkerMetrics.get_shared("inference")
        snapshot = metrics.snapshot_and_reset(...)
        snapshots.append(snapshot)

        # Post-processing (shared class-level metrics)
        metrics = WorkerMetrics.get_shared("post_processing")
        snapshot = metrics.snapshot_and_reset(...)
        snapshots.append(snapshot)

        # Producer (from any worker, they share metrics)
        snapshot = pipeline.producer_workers[0].metrics.snapshot_and_reset(...)
        snapshots.append(snapshot)

        return snapshots
```

### Metric Publishing

**Destination**: Kafka topic `"app_deployment_metrics"`

**Format**:

```python
{
    "deployment_id": "deploy_123",
    "deployment_instance_id": "instance_456",
    "app_deploy_id": "app_deploy_789",
    "action_id": "action_abc",
    "app_id": "app_xyz",
    "timestamp": "2025-01-23T10:30:45Z",
    "metrics": {
        "consumer": {
            "latency_ms": 5.2,
            "throughput": 1000,
            "active": true
        },
        "inference": {
            "latency_ms": 45.8,
            "throughput": 950,
            "active": true
        },
        "post_processing": {
            "latency_ms": 12.3,
            "throughput": 950,
            "active": true
        },
        "producer": {
            "latency_ms": 8.1,
            "throughput": 950,
            "active": true
        }
    }
}
```

**Publishing Interval**: 60 seconds (configurable via `metric_logging_interval`)

---

## Camera Management

### Dynamic Camera Operations

The pipeline supports adding and removing cameras without restart.

#### Adding a Camera

**Flow**:

```python
# server.py or external trigger
pipeline.add_camera(camera_id, camera_config)
```

**What Happens**:

1. **Consumer Manager**: Creates new async task for camera
2. **Streams**: Initializes stream connection (Kafka/Redis)
3. **Workers**: Automatically handle new camera (no changes needed)
4. **Producer**: Creates stream lazily on first send

**Code**:

```python
# src/matrice_inference/server/stream/consumer_manager.py:92-119

async def add_camera(camera_id, config):
    """Add camera dynamically"""
    if camera_id in self.consumer_tasks:
        return  # Already exists

    # Initialize stream
    await _initialize_camera_stream(camera_id)

    # Create async task
    task = asyncio.create_task(
        _consume_camera(camera_id, config),
        name=f"consumer_{camera_id}"
    )
    self.consumer_tasks[camera_id] = task

    logger.info(f"Added camera {camera_id}")
```

#### Removing a Camera

**Flow**:

```python
# server.py or external trigger
pipeline.remove_camera(camera_id)
```

**What Happens**:

1. **Consumer Manager**: Cancels async task for camera
2. **Streams**: Closes stream connection
3. **Workers**: In-flight tasks complete normally
4. **Producer**: Closes stream for camera

**Code**:

```python
# src/matrice_inference/server/stream/consumer_manager.py:121-157

async def remove_camera(camera_id):
    """Remove camera dynamically"""
    if camera_id not in self.consumer_tasks:
        return  # Doesn't exist

    # Cancel the task
    task = self.consumer_tasks[camera_id]
    task.cancel()

    # Wait for completion
    await asyncio.wait_for(task, timeout=5.0)

    # Remove from tasks dict
    del self.consumer_tasks[camera_id]

    # Close stream
    if camera_id in self.streams:
        await self.streams[camera_id].async_close()
        del self.streams[camera_id]

    logger.info(f"Removed camera {camera_id}")
```

### Camera Routing

**Hash-Based Routing**: Ensures consistent worker assignment per camera

**Inference Workers**:

```python
# src/matrice_inference/server/stream/inference_worker.py:165-170

camera_id = task.get("camera_id")
assigned_worker = hash(camera_id) % num_workers

if assigned_worker != worker_id:
    # Not for this worker, put back
    input_queue.put(task)
```

**Post-Processing Workers**:

- Implicit routing via shared queue
- Same camera always goes to same worker due to hash consistency
- Tracker states remain isolated per worker

**Benefits**:

1. **State Isolation**: Per-camera trackers stay with same worker
2. **Load Balancing**: Cameras distributed evenly across workers
3. **Order Preservation**: Same camera processes sequentially within worker

---

## Performance Characteristics

**Bottleneck Analysis**:

- **Consumer**: Limited by stream throughput (Kafka/Redis)
- **Inference**: Limited by GPU speed (most likely bottleneck)
- **Post-Processing**: Limited by CPU (object tracking)
- **Producer**: Limited by stream throughput

### Latency Analysis

**Target**: < 500ms (P50), < 800ms (P99)

**Component Breakdown** (typical):

```
Consumer:          5ms   (stream read + bytes extraction)
Inference Queue:   10ms  (queue wait time)
Inference:         100ms (GPU inference + batching)
Post-Proc Queue:   5ms   (queue wait time)
Post-Processing:   20ms  (tracking + aggregation)
Output Queue:      5ms   (queue wait time)
Producer:          10ms  (publish to stream)
─────────────────────────
Total:             155ms (P50 estimate)
```

**Latency Factors**:

- **Batch Timeout**: Higher timeout = higher latency but better throughput
- **Queue Size**: Larger queues = more buffering = higher latency under load
- **Worker Count**: More workers = lower queue wait time
- **Camera Count**: More cameras = more contention

### GPU Usage

**Target**: 85%+ utilization

**Optimization Strategies**:

1. **Dynamic Batching**: Accumulate requests for `batch_timeout_ms`
2. **Concurrent Requests**: Multiple batches in-flight per worker (`max_concurrent_requests=3`)
3. **Optimal Batch Size**: Balance latency vs throughput (typically 4-8)
4. **Multiple Workers**: One worker per GPU core

---

## Code Reference

### Main Files

| Component | File | Lines |
|-----------|------|-------|
| **Pipeline** | `src/matrice_inference/server/stream/stream_pipeline.py` | 1492 |
| **Consumer** | `src/matrice_inference/server/stream/consumer_manager.py` | 422 |
| **Inference** | `src/matrice_inference/server/stream/inference_worker.py` | 516 |
| **Post-Processing** | `src/matrice_inference/server/stream/post_processing_manager.py` | 247 |
| **Producer** | `src/matrice_inference/server/stream/producer_worker.py` | 422 |
| **Metrics** | `src/matrice_inference/server/stream/worker_metrics.py` | ~300 |
| **Metric Logger** | `src/matrice_inference/server/stream/inference_metric_logger.py` | ~500 |
| **Server** | `src/matrice_inference/server/server.py` | 1180 |

### Key Functions by Stage

#### Consumer Stage

```python
# AsyncConsumerManager
async def start()                    # Initialize and start consumers
async def stop()                     # Stop all consumers gracefully
async def add_camera(camera_id)      # Add camera dynamically
async def remove_camera(camera_id)   # Remove camera dynamically
async def _consume_camera(camera_id) # Per-camera async loop
async def _process_message(...)      # Extract bytes and enqueue
async def _enqueue_task(...)         # Write to mp.Queue via executor
```

#### Inference Stage

```python
# MultiprocessInferencePool
def start()                                    # Start worker processes
def stop()                                     # Stop worker processes
def submit_task(task_data, timeout)            # Submit to shared queue
def get_result(timeout)                        # Get from output queue

# inference_worker_process (runs in separate process)
def inference_worker_process(worker_id, ...)   # Worker entry point
async def _async_inference_loop(...)           # Async event loop
async def _process_batch_async(batch, ...)    # Process batch
async def _execute_single_inference(...)      # Single inference call
```

#### Post-Processing Stage

```python
# MultiprocessPostProcessingPool
def start()                                      # Start worker processes
def stop()                                       # Stop worker processes
def submit_task(task_data, timeout)              # Submit to shared queue
def get_result(timeout)                          # Get from output queue

# postprocessing_worker_process (runs in separate process)
def postprocessing_worker_process(worker_id, ...) # Worker entry point
# Blocking loop with per-camera tracker states
```

#### Producer Stage

```python
# ProducerWorker
def start()                              # Start worker thread
def stop()                               # Stop worker thread
def remove_camera_stream(camera_id)      # Remove camera's producer stream
async def _async_process_messages()      # Async processing loop
async def _get_task_from_queue()         # Read from mp.Queue via executor
async def _send_message_safely(task)     # Publish to output stream
async def _cache_frame_if_needed(task)   # Cache frame to Redis
```

### Configuration Parameters

```python
# StreamingPipeline.__init__() parameters

# Queue sizes
inference_queue_maxsize = 5000        # Inference queue max items
postproc_queue_maxsize = 5000         # Post-processing queue max items
output_queue_maxsize = 5000           # Output queue max items

# Timeouts
message_timeout = 10.0                # Stream read timeout (seconds)
inference_timeout = 30.0              # Inference timeout (seconds)
shutdown_timeout = 30.0               # Graceful shutdown timeout

# Workers
num_inference_workers = 4-8           # Based on GPU cores
num_postproc_workers = 2-4            # Based on CPU cores
num_producer_workers = N              # Based on camera count

# Inference
batch_size = 4                        # Dynamic batching target
batch_timeout_ms = 10.0               # Max wait for batch
max_concurrent_requests = 3           # In-flight batches per worker

# Metrics
enable_metric_logging = True          # Enable metrics collection
metric_logging_interval = 60.0        # Collection interval (seconds)
use_shared_metrics = True             # Use shared metrics per type

# Frame cache
frame_cache_worker_threads = 20       # Redis cache threads
frame_cache_max_queue = 50000         # Cache queue size
frame_cache_max_connections = 200     # Redis connection pool
```

---

## Best Practices

### 1. Queue Sizing

**Rule of Thumb**: `queue_size = throughput × latency`

Example:

```python
# For 10,000 fps and 500ms latency:
queue_size = 10,000 × 0.5 = 5,000 items
```

**Considerations**:

- Too small: Frequent backpressure, dropped frames
- Too large: High memory usage, increased latency

### 2. Worker Scaling

**Inference Workers**:

```python
# One worker per GPU core for optimal utilization
num_inference_workers = num_gpu_cores  # Typically 4-8
```

**Post-Processing Workers**:

```python
# Based on CPU cores, but fewer than inference workers
num_postproc_workers = max(2, cpu_count // 20)  # Typically 2-4
```

**Producer Workers**:

```python
# Based on camera count and output stream capacity
num_producer_workers = max(1, num_cameras // 250)  # 250 cameras per worker
```

### 3. Batch Configuration

**Trade-off**: Latency vs Throughput

```python
# Low latency (real-time applications)
batch_size = 1
batch_timeout_ms = 1.0

# Balanced (most use cases)
batch_size = 4
batch_timeout_ms = 10.0

# High throughput (batch processing)
batch_size = 16
batch_timeout_ms = 50.0
```

### 4. Error Handling

**Consumer**: Drop frames on queue full (prevents blocking streams)
**Inference**: Retry on transient errors, skip on permanent errors
**Post-Processing**: Continue on tracking errors, log warnings
**Producer**: Retry on publish failure with exponential backoff

### 5. Monitoring

**Key Metrics to Watch**:

1. Queue sizes (detect bottlenecks)
2. Worker latency (identify slow components)
3. Throughput (verify target met)
4. GPU utilization (optimize batching)
5. Memory usage (prevent OOM)

**Alert Thresholds**:

```python
queue_utilization > 80%        # Backpressure warning
latency_p99 > 800ms           # Latency SLA breach
gpu_utilization < 60%          # Underutilized GPU
dropped_frames > 1%            # Quality degradation
```

---

## Troubleshooting

### Common Issues

#### 1. High Latency

**Symptoms**: P99 latency > 800ms

**Diagnosis**:

- Check queue sizes (high utilization = bottleneck)
- Check worker latency metrics (identify slow stage)
- Check GPU utilization (low = batching issue)

**Solutions**:

- Increase worker count for bottleneck stage
- Reduce batch timeout for lower latency
- Optimize model inference time
- Check for network issues (stream I/O)

#### 2. Low Throughput

**Symptoms**: Actual FPS < target FPS

**Diagnosis**:

- Check GPU utilization (should be 85%+)
- Check queue fullness (backpressure)
- Check for dropped frames (consumer)

**Solutions**:

- Increase batch size for better GPU utilization
- Increase max_concurrent_requests
- Add more inference workers
- Optimize data preprocessing

#### 3. Memory Issues

**Symptoms**: OOM errors, high memory usage

**Diagnosis**:

- Check queue sizes (too large?)
- Check for memory leaks (tracker states)
- Check model size × worker count

**Solutions**:

- Reduce queue sizes
- Implement tracker state cleanup
- Reduce number of workers
- Use model quantization

#### 4. Dropped Frames

**Symptoms**: Consumer drops frames (backpressure)

**Diagnosis**:

- Inference queue full (check size)
- Slow inference workers (check latency)

**Solutions**:

- Increase inference queue size
- Add more inference workers
- Optimize inference performance

---

## Future Enhancements

### Planned Improvements

1. **Adaptive Batching**: Dynamic batch size based on load
2. **Priority Queues**: High-priority cameras get faster processing
3. **Model Warm-up**: Pre-load models before camera activation
4. **Health Checks**: Automated worker health monitoring
5. **Auto-scaling**: Dynamic worker count based on load
6. **Metrics Dashboard**: Real-time visualization (Grafana)
7. **Distributed Deployment**: Multiple pipeline instances with load balancer

### Experimental Features

1. **Zero-copy Frame Transfer**: Use shared memory for frame bytes
2. **GPU Stream Parallelism**: Multiple CUDA streams per worker
3. **Model Batching Across Cameras**: Combine frames from different cameras
4. **Prefetching**: Read-ahead from streams to reduce latency
5. **Compression**: Compress frames in transit to reduce memory

---

## Appendix

### Glossary

- **Async**: Asynchronous I/O using Python's asyncio
- **Multiprocessing**: True parallelism via separate processes (bypasses GIL)
- **mp.Queue**: Multiprocessing queue for cross-process communication
- **GIL**: Global Interpreter Lock (limits Python threading)
- **Backpressure**: Flow control mechanism when downstream is overloaded
- **Dynamic Batching**: Accumulating requests until batch_size or timeout
- **Camera Routing**: Consistent worker assignment per camera via hashing
- **Shared Metrics**: Single WorkerMetrics instance per worker type
- **Frame Cache**: Redis cache for low-latency frame retrieval

### References

- **Python multiprocessing**: <https://docs.python.org/3/library/multiprocessing.html>
- **Python asyncio**: <https://docs.python.org/3/library/asyncio.html>
- **Queue Theory**: <https://en.wikipedia.org/wiki/Queueing_theory>
- **Load Balancing**: <https://en.wikipedia.org/wiki/Load_balancing_(computing)>

---

**Document Version**: 1.0
**Last Updated**: 2025-01-23
**Author**: Claude (Anthropic)
**Status**: Production Ready
