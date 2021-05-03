import numpy as np

__all__ = ('_fod_dimensionality_fixer', 'iterable_data_array', 'data_array_builder')


class iterable_data_array():
    
    def __init__(self, data_dict, key):
        data_dict = self._data_dimensionality_fixer(data_dict)
        array = data_dict[key]
        self.array = array
        self.count = array.shape[0]
        
    def __iter__(self,):
        self.index = 0
        return self
    
    def __next__(self,):
        if self.index < self.count:
            self.index += 1
            return self.array[self.index - 1, :]
        else:
            raise StopIteration
            
    def _data_dimensionality_fixer(self, data_dict):
        """
        Checks the dimensionality of data in data_dict and reshapes them if their shape is 1d. 

        args:
            data_dict (dict): Data

        returns: 
            out (dict): Reshaped data_dict
        """
        out = {}
        for key in data_dict:
            checker = data_dict[key]
            if len(checker.shape)==1:
                out.update({key: checker.reshape(1, len(checker))})
            else:
                out.update({key:checker})
                
        return out


class data_array_builder(list):
    
    def __init__(self,):
        super().__init__()
    
    def build(self,):
        for thing in self:
            try:
                out = np.vstack((out, thing))
            except NameError:
                out = thing.copy()
        return out


def _fod_dimensionality_fixer(data_dict, check_key, keys_to_fix):
    """
    Checks the dimensionality of data in data_dict for function on data and reshapes them if their shape is 1d. 

    args:
        data_dict (dict): Data
        check_key (str or key): The key to check the dimensionality of
        keys_to_fix (str or key or array-like(str or key)): The keys to reshape

    returns: 
        out (tuple): The reshaped data corresponding to each key in keys to fix.

    example: 
        ```python
        >>> data_dict = {'R':np.array([1,2,3])}
        >>> data_dict['R'].shape
        > (3,)

        >>> newR = _fod_dimensionality_fixer(data_dict, 'R', 'R')
        >>> newR.shape
        > (1, 3)
        ```

    """
    keys_to_fix = np.array([keys_to_fix]).flatten()

    out = []
    checker = data_dict[check_key]
    if len(checker.shape) == 1:
        for key in keys_to_fix:
            out.append(data_dict[key].reshape(1, len(data_dict[key])))
    else:
        for key in keys_to_fix:
            out.append(data_dict[key])

    return tuple(out)

