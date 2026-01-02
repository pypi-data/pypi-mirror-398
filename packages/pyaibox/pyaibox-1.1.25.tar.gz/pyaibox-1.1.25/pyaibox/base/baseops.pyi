def sub2ind(siz, sub):
    """returns linear index from multiple subscripts

    Parameters
    ----------
    siz : list, tuple, ndarray
        the size of matrix (S1, S2, ...)
    sub : list, tuple, ndarray
        the subscripts [(s11, s12, ...), (s21, s22, ...), ...]

    .. seealso:: :func:`ind2sub`
        
    Examples
    ---------

    conversion between subscripts and linear index of one, two and three dimensional data.

    ::

        print('---sub2ind([12], [1, 10])')
        print(sub2ind([12], [1, 10]))
        print('---ind2sub([12], [1, 10])')
        print(ind2sub([12], [1, 10]))

        print('---sub2ind([3, 4], [[1, 2], [2, 3], [0, 2]])')
        print(sub2ind([3, 4], [[1, 2], [2, 3], [0, 2]]))
        print('---ind2sub([3, 4], [6, 11, 2])')
        print(ind2sub([3, 4], [6, 11, 2]))

        print('---sub2ind([3, 4, 5], [[0, 3, 0], [1, 1, 1]])')
        print(sub2ind([3, 4, 5], [[0, 3, 0], [1, 1, 1]]))
        print('---ind2sub([3, 4, 5], [15, 26])')
        print(ind2sub([3, 4, 5], [15, 26]))

    """

def ind2sub(siz, ind):
    """returns multiple subscripts from linear index

    Parameters
    ----------
    siz : list, tuple, ndarray
        the size of matrix (S1, S2, ...)
    ind : list, tuple, ndarray
        the linear index


    .. seealso:: :func:`sub2ind`
        
    Examples
    ---------

    conversion between subscripts and linear index of one, two and three dimensional data.

    ::

        print('---sub2ind([12], [1, 10])')
        print(sub2ind([12], [1, 10]))
        print('---ind2sub([12], [1, 10])')
        print(ind2sub([12], [1, 10]))

        print('---sub2ind([3, 4], [[1, 2], [2, 3], [0, 2]])')
        print(sub2ind([3, 4], [[1, 2], [2, 3], [0, 2]]))
        print('---ind2sub([3, 4], [6, 11, 2])')
        print(ind2sub([3, 4], [6, 11, 2]))

        print('---sub2ind([3, 4, 5], [[0, 3, 0], [1, 1, 1]])')
        print(sub2ind([3, 4, 5], [[0, 3, 0], [1, 1, 1]]))
        print('---ind2sub([3, 4, 5], [15, 26])')
        print(ind2sub([3, 4, 5], [15, 26]))

    """    

def dimpos(ndim, dim):
    """make positive dimensions

    Parameters
    ----------
    ndim : int
        the number of dimensions
    dim : int, list or tuple
        the dimension index to be converted
    """

def rmcdim(ndim, cdim, dim, keepdim):
    r"""get dimension indexes after removing cdim

    Parameters
    ----------
    ndim : int
        the number of dimensions
    cdim : int, optional
        If data is complex-valued but represented as real tensors, 
        you should specify the dimension. Otherwise, set it to :obj:`None`
    dim : int, None, tuple or list
        dimensions to be re-defined
    keepdim : bool
        keep dimensions? (include complex dim, defalut is :obj:`False`)

    Returns
    -------
    int, tuple or list
         re-defined dimensions
        
    """

def dimpermute(ndim, dim, mode=None, dir='f'):
    """permutes dimensions

    Parameters
    ----------
    ndim : int
        the number of dimensions
    dim : list or tuple
        the order of new dimensions (:attr:`mode` is :obj:`None`) or multiplication dimensions (``'matmul'``)
    mode : str or None, optional
        permution mode, ``'matmul'`` for matrix multiplication; ``'swap'`` for swapping two dimensions;
        ``'merge'`` for dimension merging (putting the dimensions specified by second and subsequent elements of :attr:`dim`
        after the dimension specified by the specified by the first element of :attr:`dim`); 
        ``'gather0'``: the specified dims are gathered at begin; ``'gather-1'``: the specified dims are gathered at end.
        :obj:`None` for regular permute, such as torch.permute, by default :obj:`None`.
    dir : str, optional
        the direction, ``'f'`` or ``'b'`` (reverse process of ``'f'``), default is ``'f'``.
    """

def dimreduce(ndim, cdim, dim, keepcdim=False, reduction=None):
    """get dimensions for reduction operation

    Parameters
    ----------
    ndim : int
        the number of dimensions
    cdim : int, optional
        if the data is complex-valued but represented as real tensors, 
        you should specify the dimension. Otherwise, set it to :obj:`None`
    dim : int, list, tuple or None
        dimensions for processing, :obj:`None` means all
    keepcdim : bool
        keep the complex dimension? The default is :obj:`False`
    reduction : str or None, optional
        The operation in other dimensions except the dimensions specified by :attr:`dim`,
        :obj:`None`, ``'mean'`` or ``'sum'`` (the default is :obj:`None`)

    """    

def dimmerge(ndim, mdim, dim, keepdim=False):
    """obtain new dimension indexes after merging

    Parameters
    ----------
    ndim : int
        the number of dimensions
    mdim : int, list or tuple
        the dimension indexes for merging
    dim : int, list or tuple
        the dimension indexes that are not merged
    keepdim : bool
        keep the dimensions when merging?
    """

def upkeys(D, mode='-', k='module.'):
    r"""update keys of a dictionary

    Parameters
    ----------
    D : dict
        the input dictionary
    mode : str, optional
        ``'-'`` for remove key string which is specified by :attr:`k`, by default '-'
        ``'+'`` for add key string which is specified by :attr:`k`, by default '-'
    k : str, optional
        key string pattern, by default 'module.'

    Returns
    -------
    dict
        new dictionary with keys updated
    """

def dreplace(d, fv=None, rv='None', new=False):
    ...

def dmka(D, Ds):
    """Multi-key value assign

    Multi-key value assign

    Parameters
    ----------
    D : dict
        main dict.
    Ds : dict
        sub dict
    """

def strfind(mainstr, patnstr):
    """find all patterns in string

    Parameters
    ----------
    mainstr :7710.0  xb4I/*-  str
        the main string
    patnstr :  str
        the pattern string
    """

def unique(arr, issort=True):
    """returns unique elements and it's positions

    Parameters
    ----------
    arr : list tuple or array
        the input
    issort :  bool
        sort before
    """


