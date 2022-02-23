import numpy as np
import warnings

__all__ = ('_fod_dimensionality_fixer', 'iterable_data_array', 'data_array_builder', 'not_nan_indexer')

def not_nan_indexer(tpl:()):
    """
    Return an indexer of good indices (not nan) which checks all arrays in the tpl. Resulting indexer will work for all elements in tpl.

    args:
        tpl (array-like): Array-like of arrays to find good indices in.

    examples:

        .. code-block:: python

            angle = fod.iterable_data_array(data_dict, 'angle')
            r_ida = fod.iterable_data_array(data_dict, 'R')
            
            for a, r in zip(angle, r_ida):
                indexer = fod.not_nan_indexer((a, r)) # retun only non-nans for both `a` and `r`
                a = a[indexer] # access not nan
                r = r[indexer] # acces not nan
    """
    l = len(tpl[0])
    for t in tpl:
        assert len(t) == l, 'Not all arrays in tpl have the same length.'

    indexer = []
    for i in range(l):
        # checker will be 0 if all are not nan
        checker = sum(np.isnan([tpl[j][i] for j in range(len(tpl))]))
        if checker == 0:
            indexer.append(True)

        else:
            indexer.append(False)

    return indexer


class iterable_data_array():
    """
    Iterable for usage building functions on data. 

    args:
        data_dict (dict): Dict of Data
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
    def __init__(self, data_dict, key, dropna_on_pass=True):
        
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
    
    def build(self, fix_lengths=True, coerce_to_ndarray=True, ignore_coerce_warnings=False):
        """Build the final array (create a numpy.vstack).

        args:
            fix_lengths (bool): Whether or not to append nans to make lengths match. Only works with 1D data.
            coerce_to_ndarray (bool): Whether or not to coerce data type into an ndarray.  
            ignore_coerce_warnings (bool): Whether or not to surpress coercing to ndarray warnings. 

        returns:
            (numpy.vstack): VStacks all items in the data_array_builder.

        """

        convert_to_ndarray = False

        if fix_lengths:
            for thing in self:
                # import pdb; pdb.set_trace()
                if not hasattr(thing, 'shape') or thing.shape == ():
                    if coerce_to_ndarray:
                    # case where we will have to coerce to ndarray anyway so we will force it to be 1D
                        if not ignore_coerce_warnings:
                            warnings.showwarning("You are coercing data into a 1D ndarray. The data is of type {} and will be converted following numpy.array([{}]).flatten(). \nTO SURPRESS THIS WARNING use .build(..., ignore_coerce_warnings=True)".format(type(thing), thing), UserWarning, '', '')
                        convert_to_ndarray = True
                        continue 
                    else:
                        raise ValueError('Data is not an ndarray. To coerce to ndarray use .build(..., coerce_to_ndarray=True)')
                if len(thing.shape)!=1:
                    raise ValueError('Data is not 1-dimensional. (Shape is {}). Cannot fix lengths. Try again with .build(..., fix_lengths=False)'.format(thing.shape))
        
        target_length = 0
        
        for thing in self:
            if convert_to_ndarray:
                thing = np.array([thing]).flatten()

            if len(thing)>target_length:
                target_length = len(thing)

        for thing in self:
            if convert_to_ndarray:
                thing = np.array([thing]).flatten()
            # get thing into target shape
            while len(thing) != target_length:
                thing = np.concatenate((thing, np.array([np.nan])))
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

