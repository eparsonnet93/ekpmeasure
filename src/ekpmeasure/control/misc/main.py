__all__ = ('get_save_name',)

def get_save_name(name, path):
    """returns a unique name correctly indexed"""
    import os
    existing_files = os.listdir(path)

    same_basename_indices = []

    for file in existing_files:
        base_name = file.split('_')[:-1]
        bname = ''
        for x in base_name:
            bname+=x + '_'
        bname = bname[:-1]
        if name == bname:
            same_basename_indices.append(int(file.split('_')[-1][:-4]))
    
    if len(same_basename_indices) == 0:
        index = '0'
    else:
        index = str(max(same_basename_indices)+1)

    save_name = name+'_'+index+'.csv'
    if save_name in set(existing_files):
        raise ValueError('error in get_save_name, did not generate a unique name')
    return save_name