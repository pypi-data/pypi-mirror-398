import tensorplay
import random
import queue
from dataclasses import dataclass

try:
    import numpy as np
except ImportError:
    np = None

def _worker_loop(
    dataset_kind,
    dataset,
    index_queue,
    data_queue,
    done_event,
    auto_collation,
    collate_fn,
    drop_last,
    seed,
    init_fn,
    worker_id,
    num_workers,
    batch_size=None,
    done_signal=None,
    worker_debug=False,
    ack_queue=None
    ):
    """
    Worker loop function for DataLoader.

    Args:
        dataset_kind: The kind of dataset (_DatasetKind.Map or _DatasetKind.Iterable).
        dataset: The dataset to sample from.
        index_queue: The queue to receive indices from the main process.
        data_queue: The queue to send data to the main process.
        done_event: The event to signal that the worker is done.
        auto_collation: Whether to automatically collate samples into batches.
        collate_fn: The function to collate samples into batches.
        drop_last: Whether to drop the last batch if it is smaller than the batch size.
        seed: The seed for random number generation.
        init_fn: The function to initialize the worker process.
        worker_id: The ID of the worker process.
        num_workers: The total number of worker processes.
        batch_size: The batch size to use for collation.
        done_signal: The signal to send to the main process when done.
        worker_debug: Whether to enable debug mode for the worker process.
        ack_queue: The queue to receive acknowledgements from the main process.
    """
    if worker_debug:
        print(f"[Worker {worker_id}] Started. Seed: {seed}")

    # Set seed
    random.seed(seed)
    if np is not None:
        np.random.seed(seed)
    tensorplay.manual_seed(seed)

    # Set worker info
    # We need to set this in the dataloader module of the worker process
    from .. import dataloader
    dataloader._worker_info = dataloader.WorkerInfo(id=worker_id, num_workers=num_workers, seed=seed, dataset=dataset)

    # Init function
    if init_fn is not None:
        init_fn(worker_id)

    # Fetcher
    from ..dataloader import _DatasetKind
    fetcher = _DatasetKind.create_fetcher(
        dataset_kind, dataset, auto_collation, collate_fn, drop_last, batch_size)

    # Cache for shared memory tensors to keep them alive until acknowledged
    # Map: idx -> data
    # We use a simple check to drain the ack_queue periodically
    sent_data_cache = {}

    def check_acks():
        if ack_queue is None: return
        try:
            while True:
                ack_idx = ack_queue.get_nowait()
                if ack_idx in sent_data_cache:
                    del sent_data_cache[ack_idx]
        except queue.Empty:
            pass

    try:
        if dataset_kind == _DatasetKind.Map:
            while not done_event.is_set():
                check_acks()
                try:
                    r = index_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                if r is None:
                    # None is the signal to stop
                    if worker_debug:
                        print(f"[Worker {worker_id}] Received stop signal.")
                    break
                
                idx, batch_indices = r
                if worker_debug:
                    print(f"[Worker {worker_id}] Fetching batch {idx}.")
                try:
                    data = fetcher.fetch(batch_indices)
                    
                    # Store data in cache before sending to prevent early GC/SharedMemory closure
                    if ack_queue is not None:
                        sent_data_cache[idx] = data
                    
                    data_queue.put((idx, data))
                except Exception as e:
                    if worker_debug:
                        print(f"[Worker {worker_id}] Error fetching batch {idx}: {e}")
                    data_queue.put((idx, e))
        else:
             # IterableDataset
             # Loop until dataset is exhausted or done_event is set
             # No index_queue usage for tasks
             try:
                 idx_counter = 0
                 while not done_event.is_set():
                     check_acks()
                     try:
                         # fetch(None) will return a batch if batch_size is set, or a single item
                         data = fetcher.fetch(None)
                         
                         idx = idx_counter
                         idx_counter += 1
                         
                         if ack_queue is not None:
                            sent_data_cache[idx] = data

                         data_queue.put((idx, data))
                     except StopIteration:
                         break
                 
                 # Send done signal
                 if done_signal is not None:
                      data_queue.put((None, done_signal))

             except Exception as e:
                 data_queue.put((None, e))
                 
    except KeyboardInterrupt:
        pass
    except Exception as e:
        # If the worker crashes, we should probably try to notify main process
        # But for now, we just rely on main process timeout or queue get failure?
        pass
