import tensorplay
import re
import collections

np_str_obj_array_pattern = re.compile(r'[SaUO]')

def default_collate(batch):
    """Puts each data field into a tensor with outer dimension batch size"""

    elem = batch[0]
    elem_type = type(elem)
    if isinstance(elem, tensorplay.Tensor):
        return tensorplay.stack(batch, 0)
    elif elem_type.__module__ == 'numpy' and elem_type.__name__ != 'str_' and elem_type.__name__ != 'string_':
        if elem_type.__name__ == 'ndarray' or elem_type.__name__ == 'memmap':
            # array of string classes and object
            if np_str_obj_array_pattern.search(elem.dtype.str) is not None:
                raise TypeError("default_collate: numpy array of strings is not supported")
            return default_collate([tensorplay.tensor(b) for b in batch])
        elif elem.shape == ():  # scalars
            return tensorplay.tensor(batch)
    elif isinstance(elem, float):
        return tensorplay.tensor(batch, dtype=tensorplay.float32) # Default to float32
    elif isinstance(elem, int):
        return tensorplay.tensor(batch, dtype=tensorplay.int64) # Default to int64
    elif isinstance(elem, str):
        return batch
    elif isinstance(elem, collections.abc.Mapping):
        return {key: default_collate([d[key] for d in batch]) for key in elem}
    elif isinstance(elem, tuple) and hasattr(elem, '_fields'):  # namedtuple
        return elem_type(*(default_collate(samples) for samples in zip(*batch)))
    elif isinstance(elem, collections.abc.Sequence):
        # check to make sure that the elements in batch have consistent size
        it = iter(batch)
        elem_size = len(next(it))
        if not all(len(elem) == elem_size for elem in it):
            raise RuntimeError('each element in list of batch should be of equal size')
        transposed = zip(*batch)
        return [default_collate(samples) for samples in transposed]

    raise TypeError(f"default_collate: batch must contain tensors, numpy arrays, numbers, "
                    f"dicts or lists; found {elem_type}")
