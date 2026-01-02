def mplcmap(cmap):
    """returns matplotlib's colormap

    Parameters
    ----------
    cmap : str
        colormap name

    Returns
    -------
    object
        matplotlib's colormap
    """    

def rgb2gray(rgb, fmt='chnllast'):
    r"""Converts RGB image to GRAY image

    Converts RGB image to GRAY image according to

    .. math::
       G = 0.2989R + 0.5870G + 0.1140B

    see matlab's ``rgb2gray`` function for details.

    Parameters
    ----------
    rgb : numpy array
        Original RGB tensor.
    fmt : str, optional
        Specifies the position of channels in :attr:`rgb` tensor, surpported are:
        - ``'chnllast'`` (default)
        - ``'chnlfirst'``
    """

def gray2rgb(gray, cmap, drange=[0, 255], dtype=False):
    r"""Converts gray image values to rgb image

    converts `gray` image values to rgb image according to the specified colormap string 'cmap',
    supported are: ``'parula'``, ``'jet'``, ``'hsv'``, ``'hot'``, ``'cool'``, ``'spring'``,
    ``'summer'``, ``'autumn'``, ``'winter'``, ``'gray'``, ``'bone'``, ``'copper'``, ``'pink'``,
    ``'lines'``, ``'colorcube'``, ``'prism'``, ``'flag'``, ``'white'``.

    Parameters
    ----------
    gray : numpy array
        The gray image.
    cmap : str or colormap
        colormap string
    drange : list or tuple
        The low and high value, default is ``[0, 255]``
    dtype : bool or str
        Specifies the format (``'int'``, ``'uint8'``, ``'uint16'``, ``'uint32'``, ``'float16'``,
        ``'float32'``, , ``'float64'``) for the output rgb matrix. (default is ``False``, don't change)

    Examples
    --------

    ::

        import pyaibox as pl
        import matplotlib.pyplot as plt
        import numpy as np

        cmap = 'jet'
        # cmap = 'hsv'
        # cmap = 'hot'
        # cmap = 'parula'
        gray = pb.imread('../../data/images/LenaGRAY256.png')
        print(gray.shape)

        rgb = gray2rgb(gray, cmap, [0, 1], False)  # rgb --> double, [0, 1]
        # rgb = gray2rgb(gray, cmap, [0, 255], False)  # rgb --> double, [0., 255.]
        # rgb = gray2rgb(gray, cmap, [0, 255], True)  # rgb --> uint8, [0, 255]

        print(gray.shape, np.min(gray), np.max(gray), gray.dtype)
        print(rgb.shape, np.min(rgb), np.max(rgb), rgb.dtype)

        plt.figure()
        plt.subplot(121)
        plt.imshow(gray, cmap=pb.parula if cmap == 'parula' else cmap)
        plt.subplot(122)
        plt.imshow(rgb)
        plt.show()

    """

def ind2rgb(ind, cmap, ncolors=256, drange=(0, 1), dtype='float32', ofmt='RGBA'):
    """convert indexed value to RGB or RGBA color

    Args:
        ind (list, tuple or array): indexing data
        cmap (str or colormap): colormap name
        ncolors (int, optional): the number of colors. Defaults to 256.
        drange (tuple, optional): output data range. Defaults to (0, 1).
        dtype (str, optional): output data dtype. Defaults to ``'float32'``.
        ofmt (str, optional): output formation ``'RGB'`` or ``'RGBA'``. Defaults to ``'RGBA'``.

    Returns:
        array: RGB or RGBA array
    """    


