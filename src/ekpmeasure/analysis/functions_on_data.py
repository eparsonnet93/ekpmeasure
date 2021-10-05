import numpy as np

__all__ = ('_fod_dimensionality_fixer', 'iterable_data_array', 'data_array_builder')


class iterable_data_array():
    """
    Iterable for usage building functions on data. 

    args:
        data_dict (dict): data
        key (str or key): Key for which to return iterable data array.

    Examples:
        .. code-block:: python
            
            >>> data
            >   {0: 
                    {'defintion': {'test': {1}}}
                    {'data'}: {'testdata':np.array([[1,2,3], [1,2,3]])}
                }
            >>> ida = iterable_data_array(data[0]['data'], key = 'testdata')
            >>> for x in ida:
            ...     print(x)

            > [1,2,3]
            [1,2,3]
        
    """
    def __init__(self, data_dict, key):
        
        data_dict = self._data_dimensionality_fixer(data_dict)
        array = data_dict[key]
        self.array = array
        self.count = array.shape[0]

    def __str__(self):
        return self.array.__str__()

    def __repr__(self):
        return self.array.__repr__()
        
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

    """Class for building data arrays.

        examples:

            Square data for different trials: 
            
            .. code-block:: python
               
                >>> data
                > {0: 
                    {'definition': {
                        'param1': {'10V'},
                        'param2': {'100ns', '10ns'},
                        'param3': {'1mv'}
                        },
                    'data': {
                        'raw_data': array([[1, 2, 3],[1, 2, 3]], dtype=int64)
                        }
                    }
                }

                >>> data_dict = data[0]['data']
                >>> data_dict
                > {'raw_data': array([[1, 2, 3],
                    [1, 2, 3]], dtype=int64)}

                >>> ida = iterable_data_array(data_dict, 'raw_data')
                >>> out = data_array_builder()
                >>> for d in ida:
                    ... #square each measurement
                    ... out.append(d**2)
                >>> out.build()
                > array([[1, 4, 9],[1, 4, 9]], dtype=int64)

                >>> data_dict.update({'raw_data':out.build()})
                >>> data
                > {0: 
                    {'definition': 
                        {'param1': {'10V'},
                        'param2': {'100ns', '10ns'},
                        'param3': {'1mv'}
                    },
                    'data': {'raw_data': array([[1, 4, 9], [1, 4, 9]], dtype=int64)}
                    }
                }

        """
    
    def __init__(self,):
        super().__init__()
    
    def build(self,):
        """Build the final array (create a numpy.vstack).

        returns:
            (numpy.vstack): VStacks all items in the data_array_builder.

        """
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

