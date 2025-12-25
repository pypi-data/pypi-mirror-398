import queue
import threading
import collections.abc

from ... import multiprocessing
from . import sampler as sampler_module
from ._utils import worker
from ._utils.collate import default_collate

class _DatasetKind:
    Map = 0
    Iterable = 1

    @staticmethod
    def create_fetcher(kind, dataset, auto_collation, collate_fn, drop_last, batch_size=None):
        if kind == _DatasetKind.Map:
            return _MapDatasetFetcher(dataset, auto_collation, collate_fn, drop_last)
        else:
            return _IterableDatasetFetcher(dataset, auto_collation, collate_fn, drop_last, batch_size)

class WorkerInfo:
    __slots__ = ('id', 'num_workers', 'seed', 'dataset')
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

_worker_info = None

def get_worker_info():
    return _worker_info

def _pin_memory(data):
    if hasattr(data, 'pin_memory'):
        return data.pin_memory()
    elif isinstance(data, str) or isinstance(data, bytes):
        return data
    elif isinstance(data, collections.abc.Mapping):
        try:
            return type(data)({k: _pin_memory(v) for k, v in data.items()})
        except TypeError:
             return {k: _pin_memory(v) for k, v in data.items()}
    elif isinstance(data, tuple) and hasattr(data, '_fields'):  # namedtuple
        return type(data)(*(_pin_memory(d) for d in data))
    elif isinstance(data, collections.abc.Sequence):
        try:
            return type(data)([_pin_memory(d) for d in data])
        except TypeError:
             return [_pin_memory(d) for d in data]
    return data

def _to_device(data, device):
    if device is None:
        return data
    if hasattr(data, 'to'):
        return data.to(device)
    elif isinstance(data, str) or isinstance(data, bytes):
        return data
    elif isinstance(data, collections.abc.Mapping):
        try:
            return type(data)({k: _to_device(v, device) for k, v in data.items()})
        except TypeError:
             return {k: _to_device(v, device) for k, v in data.items()}
    elif isinstance(data, tuple) and hasattr(data, '_fields'):  # namedtuple
        return type(data)(*(_to_device(d, device) for d in data))
    elif isinstance(data, collections.abc.Sequence):
        try:
            return type(data)([_to_device(d, device) for d in data])
        except TypeError:
             return [_to_device(d, device) for d in data]
    return data

def _pin_memory_loop(in_queue, out_queue, device_id, done_event):
    while not done_event.is_set():
        try:
            r = in_queue.get(timeout=0.1)
        except queue.Empty:
            continue
        
        idx, data = r
        if isinstance(data, Exception) or isinstance(data, _WorkerDone):
             out_queue.put(r)
             continue
        
        try:
             pinned_data = _pin_memory(data)
             out_queue.put((idx, pinned_data))
        except Exception as e:
             out_queue.put((idx, e))

class DataLoader:
    def __init__(
        self,
        dataset, 
        batch_size=1, 
        shuffle=False, 
        sampler=None,
        batch_sampler=None, 
        num_workers=0,
        collate_fn=None,
        pin_memory=False, 
        drop_last=False, 
        timeout=0,
        worker_init_fn=None,
        multiprocessing_context=None,
        generator=None,
        *, 
        prefetch_factor=2,
        persistent_workers=False,
        device=None,
        worker_debug=False
        ):
        
        self.dataset = dataset
        self.num_workers = num_workers
        self.prefetch_factor = prefetch_factor
        self.pin_memory = pin_memory
        self.timeout = timeout
        self.worker_init_fn = worker_init_fn
        self.multiprocessing_context = multiprocessing_context
        self.persistent_workers = persistent_workers
        self.device = device
        self.worker_debug = worker_debug
        self._iterator = None

        # Determine dataset kind
        # We assume dataset matches the protocol
        # But we can check instance if we import Dataset
        from .dataset import IterableDataset
        if isinstance(dataset, IterableDataset):
            self.dataset_kind = _DatasetKind.Iterable
            if shuffle:
                raise ValueError("DataLoader with IterableDataset: expected shuffle=False")
            if sampler is not None:
                 raise ValueError("DataLoader with IterableDataset: expected sampler=None")
            if batch_sampler is not None:
                 raise ValueError("DataLoader with IterableDataset: expected batch_sampler=None")
        else:
            self.dataset_kind = _DatasetKind.Map

        self.batch_size = batch_size
        self.drop_last = drop_last
        self.sampler = sampler
        self.batch_sampler = batch_sampler
        self.generator = generator

        if collate_fn is None:
            if self._auto_collation:
                collate_fn = default_collate
            else:
                collate_fn = default_collate
        self.collate_fn = collate_fn
        
        # Base seed for workers
        import random
        self.base_seed = random.randint(0, 2**32 - 1)

        if self.dataset_kind == _DatasetKind.Map:
             # Sampler initialization logic
             if batch_sampler is not None:
                 if batch_size != 1 or shuffle or sampler is not None or drop_last:
                     raise ValueError('batch_sampler option is mutually exclusive '
                                      'with batch_size, shuffle, sampler, and drop_last')
                 self.batch_size = None
                 self.drop_last = False
             elif batch_size is None:
                 # No batching
                 if self.drop_last:
                      raise ValueError('batch_size=None option is mutually exclusive with drop_last')
                 if sampler is None:
                      if shuffle:
                           sampler = sampler_module.RandomSampler(dataset, generator=generator)
                      else:
                           sampler = sampler_module.SequentialSampler(dataset)
                 self.batch_sampler = None
             else:
                 # Batching
                 if sampler is None:
                      if shuffle:
                           sampler = sampler_module.RandomSampler(dataset, generator=generator)
                      else:
                           sampler = sampler_module.SequentialSampler(dataset)
                 self.batch_sampler = sampler_module.BatchSampler(sampler, batch_size, drop_last)
             
             self.sampler = sampler

    @property
    def _auto_collation(self):
        return self.batch_sampler is not None

    def __iter__(self):
        if self.num_workers == 0:
            return _SingleProcessDataLoaderIter(self)
        else:
            if self.persistent_workers and self.dataset_kind != _DatasetKind.Iterable:
                if self._iterator is None:
                    self._iterator = _MultiProcessingDataLoaderIter(self)
                else:
                    self._iterator._reset(self)
                return self._iterator
            else:
                return _MultiProcessingDataLoaderIter(self)
            
    def __len__(self):
        if self.dataset_kind == _DatasetKind.Iterable:
            # TODO: length of iterable dataset?
            raise TypeError("IterableDataset does not support len()")
        if self.batch_sampler is not None:
            return len(self.batch_sampler)
        if self.sampler is not None:
            # No batching
            return len(self.sampler)
        return len(self.dataset)

class _MapDatasetFetcher(object):
    def __init__(self, dataset, auto_collation, collate_fn, drop_last):
        self.dataset = dataset
        self.auto_collation = auto_collation
        self.collate_fn = collate_fn
        self.drop_last = drop_last

    def fetch(self, possibly_batched_index):
        if self.auto_collation:
            # possibly_batched_index is a list of indices
            data = [self.dataset[idx] for idx in possibly_batched_index]
        else:
            data = self.dataset[possibly_batched_index]
        return self.collate_fn(data)

class _IterableDatasetFetcher(object):
    def __init__(self, dataset, auto_collation, collate_fn, drop_last, batch_size=None):
        self.dataset = dataset
        self.auto_collation = auto_collation
        self.collate_fn = collate_fn
        self.drop_last = drop_last
        self.dataset_iter = iter(dataset)
        self.batch_size = batch_size

    def fetch(self, possibly_batched_index):
        if self.auto_collation:
             # TODO: Implement batching for iterable dataset
             raise NotImplementedError("Batching for IterableDataset not fully implemented")
        
        if self.batch_size is None:
            return next(self.dataset_iter)

        # Manual batching
        batch = []
        try:
            for _ in range(self.batch_size):
                batch.append(next(self.dataset_iter))
        except StopIteration:
            if len(batch) == 0:
                raise StopIteration
            if self.drop_last:
                raise StopIteration
        
        if self.drop_last and len(batch) < self.batch_size:
             raise StopIteration
             
        return self.collate_fn(batch)

class _BaseDataLoaderIter(object):
    def __init__(self, loader: DataLoader):
        self.dataset = loader.dataset
        self.dataset_kind = loader.dataset_kind
        self.auto_collation = loader._auto_collation
        self.drop_last = loader.drop_last
        self.collate_fn = loader.collate_fn
        # We need batch_size for manual batching of IterableDataset
        self.batch_size = loader.batch_size 
        self.sampler = loader.sampler
        self.batch_sampler = loader.batch_sampler
        self.device = loader.device
        
        if self.batch_sampler is not None:
             self.sampler_iter = iter(self.batch_sampler)
        elif self.sampler is not None:
             self.sampler_iter = iter(self.sampler)
        else:
             self.sampler_iter = None

        self._dataset_fetcher = _DatasetKind.create_fetcher(
            self.dataset_kind, self.dataset, self.auto_collation, self.collate_fn, self.drop_last, self.batch_size)

    def __iter__(self):
        return self

class _SingleProcessDataLoaderIter(_BaseDataLoaderIter):
    def __init__(self, loader):
        super(_SingleProcessDataLoaderIter, self).__init__(loader)
        self.pin_memory = loader.pin_memory

    def __next__(self):
        if self.sampler_iter is not None:
            # MapDataset or IterableDataset with sampler (unlikely)
            try:
                index = next(self.sampler_iter)
            except StopIteration:
                raise StopIteration
            data = self._dataset_fetcher.fetch(index)
        else:
            # Iterable dataset without sampler
            # Batching is handled by _IterableDatasetFetcher if batch_size is set
            try:
                data = self._dataset_fetcher.fetch(None)
            except StopIteration:
                raise StopIteration
        
        if self.pin_memory:
             data = _pin_memory(data)
        
        if self.device is not None:
             data = _to_device(data, self.device)
             
        return data

class _WorkerDone(object):
    pass
_WORKER_DONE = _WorkerDone()

class _MultiProcessingDataLoaderIter(_BaseDataLoaderIter):
    def __init__(self, loader):
        super(_MultiProcessingDataLoaderIter, self).__init__(loader)
        
        self.persistent_workers = loader.persistent_workers
        self.pin_memory = loader.pin_memory
        self.num_workers = loader.num_workers
        self.worker_init_fn = loader.worker_init_fn
        self.worker_debug = loader.worker_debug
        self.worker_result_queue = multiprocessing.Queue() # (idx, data) or (idx, Exception)
        self.worker_ack_queue = multiprocessing.Queue() # idx
        self.workers_done_event = multiprocessing.Event()
        
        self.index_queues = []
        self.workers = []
        
        if self.pin_memory:
            self.data_queue = queue.Queue()
            self.pin_memory_thread_done_event = threading.Event()
            self.pin_memory_thread = threading.Thread(
                target=_pin_memory_loop,
                args=(self.worker_result_queue, self.data_queue, 0, self.pin_memory_thread_done_event)
            )
            self.pin_memory_thread.daemon = True
            self.pin_memory_thread.start()
        else:
            self.data_queue = self.worker_result_queue
        
        # Pre-fetch setup
        self.send_idx = 0
        self.rcvd_idx = 0
        self.batches_outstanding = 0
        self.active_workers = self.num_workers # For IterableDataset
        
        # Results buffer: {idx: data}
        self.task_info = {} 
        
        # Start workers
        for i in range(self.num_workers):
            index_queue = multiprocessing.Queue()
            index_queue.cancel_join_thread()
            self.index_queues.append(index_queue)
            
            w = multiprocessing.Process(
                target=worker._worker_loop,
                args=(
                    self.dataset_kind,
                    self.dataset,
                    index_queue,
                    self.worker_result_queue,
                    self.workers_done_event,
                    self.auto_collation,
                    self.collate_fn,
                    self.drop_last,
                    loader.base_seed + i,
                    self.worker_init_fn,
                    i,
                    self.num_workers,
                    self.batch_size,
                    _WORKER_DONE,
                    self.worker_debug,
                    self.worker_ack_queue
                )
            )
            w.daemon = True
            w.start()
            self.workers.append(w)
            
        # Prime the prefetch
        self._prime_prefetch()

    def _reset(self, loader, first_iter=False):
        # Reset sampler iterator
        if self.batch_sampler is not None:
             self.sampler_iter = iter(self.batch_sampler)
        elif self.sampler is not None:
             self.sampler_iter = iter(self.sampler)
        else:
             self.sampler_iter = None

        self.send_idx = 0
        self.rcvd_idx = 0
        self.batches_outstanding = 0
        self.task_info = {}
        # For IterableDataset
        self.active_workers = self.num_workers
        
        # Prime prefetch
        self._prime_prefetch()

    def _prime_prefetch(self):
        if self.dataset_kind == _DatasetKind.Iterable:
            return
            
        # Prefetch factor 2 per worker
        for _ in range(2 * self.num_workers):
            self._try_put_index()

    def _try_put_index(self):
        try:
            index = next(self.sampler_iter)
        except StopIteration:
            return
            
        worker_id = self.send_idx % self.num_workers
        self.index_queues[worker_id].put((self.send_idx, index))
        self.send_idx += 1
        self.batches_outstanding += 1

    def __next__(self):
        if self.dataset_kind == _DatasetKind.Map:
             # Check if we are done
            if self.rcvd_idx == self.send_idx:
                if self.batches_outstanding == 0:
                    # No more data to send and no more data to receive
                    if not self.persistent_workers:
                        self._shutdown_workers()
                    raise StopIteration

            # Try to get result
            while True:
                # Check if we have the next result in buffer
                if self.rcvd_idx in self.task_info:
                    data = self.task_info.pop(self.rcvd_idx)
                    self.rcvd_idx += 1
                    self.batches_outstanding -= 1
                    self._try_put_index() # Keep workers busy
                    
                    if isinstance(data, Exception):
                        self._shutdown_workers()
                        raise data
                    if self.device is not None:
                        data = _to_device(data, self.device)
                    return data
                
                # Fetch from queue
                try:
                    idx, data = self.data_queue.get(timeout=1.0) # Timeout to check for deadlocks?
                except queue.Empty:
                     # Check if workers are alive?
                     continue
                
                # Send ACK to worker to release memory cache
                self.worker_ack_queue.put(idx)

                if isinstance(data, Exception):
                     self.task_info[idx] = data
                else:
                     self.task_info[idx] = data
        else:
            # IterableDataset
            if self.active_workers == 0:
                 self._shutdown_workers()
                 raise StopIteration
            
            while True:
                try:
                    # TODO: handling timeout or worker death
                    idx, data = self.data_queue.get(timeout=1.0)
                except queue.Empty:
                     if self.active_workers == 0:
                         self._shutdown_workers()
                         raise StopIteration
                     continue

                if isinstance(data, _WorkerDone):
                    self.active_workers -= 1
                    if self.active_workers == 0:
                         self._shutdown_workers()
                         raise StopIteration
                    continue
                
                # Send ACK to worker (if idx is not None)
                if idx is not None:
                    self.worker_ack_queue.put(idx)

                if isinstance(data, Exception):
                    self._shutdown_workers()
                    raise data
                
                if self.device is not None:
                    data = _to_device(data, self.device)
                return data

    def _shutdown_workers(self):
        # Python's GC handles this usually, but explicit shutdown is good
        try:
            if not self.workers_done_event.is_set():
                self.workers_done_event.set()
                
            for q in self.index_queues:
                q.put(None)
                q.close()
                
            self.worker_result_queue.close()
            self.worker_ack_queue.close()
                
            for w in self.workers:
                w.join(timeout=1.0)
            
            if self.pin_memory:
                 self.pin_memory_thread_done_event.set()
                 self.pin_memory_thread.join(timeout=1.0)
        except:
            pass
            
    def __del__(self):
        self._shutdown_workers()
