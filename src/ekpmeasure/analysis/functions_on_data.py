import numpy as np

__all__ = ('_fod_dimensionality_fixer', )


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
