import matplotlib.pyplot as plt

__all__ = ('plot_pfm',)

def plot_pfm(imgdata_dict, meta_data, cmap='viridis', figsize=(20,10)):
    """docstring"""
    l = len(imgdata_dict)
    fig, axs = plt.subplots(ncols = int(l/2), nrows = 2, figsize = figsize)
    axs = axs.flatten()
    d = float(meta_data['ScanSize'])*1e6/int(meta_data['ScanLines'])
    for i, key in enumerate(imgdata_dict):
        image, ax = imgdata_dict[key], axs[i]
        ax.imshow(image,cmap=cmap, extent = [0, d*image.shape[1], 0, d*image.shape[0]])
        ax.set_title(key, size = 20)
        ax.tick_params(labelsize = 20)
        
    return fig, axs