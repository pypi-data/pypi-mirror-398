def db2mag(db, s=20.):
    r"""Converts decibel values to magnitudes

    .. math::
       {\rm mag} = 10^{db / s}

    Parameters
    ----------
    db : int, float, tuple, list, ndarray
        The decibel values.
    s : int or float
        The scale value, default is 20.

    Returns
    -------
     int, float, tuple, list, ndarray
        The magnitudes of inputs with the same type.
    """

def mag2db(mag, s=20.):
    r"""Converts decibel values to magnitudes

    .. math::
       {\rm db} = s*{\rm log10}{\rm mag}

    Parameters
    ----------
    mag : int, float, tuple, list, ndarray
        The magnitude values.
    s : int or float
        The scale value, default is 20.

    Returns
    -------
     int, float, tuple, list, ndarray
        The decibel of inputs with the same type.
    """

def fnab(n):
    """gives the closest two integer number factor of a number

    Parameters
    ----------
    n : int or float
        the number

    Returns
    -------
    a : int
    b : int
        the factor number

    Examples
    --------

    ::

        print(fnab(5))
        print(fnab(6))
        print(fnab(7))
        print(fnab(8))
        print(fnab(9))

        # ---output
        (2, 3)
        (2, 3)
        (2, 4)
        (2, 4)
        (3, 3)

    """    

def ebeo(a, b, op='+'):
    r"""element by element operation

    Element by element operation.

    Parameters
    ----------
    a : list, tuple or ndarray
        The first list/tuple/ndarray.
    b : list, tuple or ndarray
        The second list/tuple/ndarray.
    op : str, optional
        Supported operations are:
        - ``'+'`` or ``'add'`` for addition (default)
        - ``'-'`` or ``'sub'`` for substraction
        - ``'*'`` or ``'mul'`` for multiplication
        - ``'/'`` or ``'div'`` for division
        - ``'**'`` or ``pow`` for power
        - ``'<'``, or ``'lt'`` for less than
        - ``'<='``, or ``'le'`` for less than or equal to
        - ``'>'``, or ``'gt'`` for greater than
        - ``'>='``, or ``'ge'`` for greater than or equal to
        - ``'&'`` for bitwise and
        - ``'|'`` for bitwise or
        - ``'^'`` for bitwise xor
        - function for custom operation.

    Raises
    ------
    TypeError
        If the specified operator not in the above list, raise a TypeError.
    """

def nextpow2(x):
    r"""get the next higher power of 2.

    Given an number :math:`x`, returns the first p such that :math:`2^p >=|x|`. 

    Args:
        x (int or float): an number.

    Returns:
        int: Next higher power of 2.

    Examples:

        ::

            print(prevpow2(-5), nextpow2(-5))
            print(prevpow2(5), nextpow2(5))
            print(prevpow2(0.3), nextpow2(0.3))
            print(prevpow2(7.3), nextpow2(7.3))
            print(prevpow2(-3.5), nextpow2(-3.5))

            # output
            2 3
            2 3
            -2 -1
            2 3
            1 2

    """

def prevpow2(x):
    r"""get the previous lower power of 2.

    Given an number :math:`x`, returns the first p such that :math:`2^p <=|x|`. 

    Args:
        x (int or float): an number.

    Returns:
        int: Next higher power of 2.

    Examples:

        ::

            print(prevpow2(-5), nextpow2(-5))
            print(prevpow2(5), nextpow2(5))
            print(prevpow2(0.3), nextpow2(0.3))
            print(prevpow2(7.3), nextpow2(7.3))
            print(prevpow2(-3.5), nextpow2(-3.5))

            # output
            2 3
            2 3
            -2 -1
            2 3
            1 2

    """

def ematmul(A, B, **kwargs):
    r"""Element-by-element complex multiplication

    like A .* B in matlab

    Parameters
    ----------
    A : array
        any size array, both complex and real representation are supported.
        For real representation, the real and imaginary dimension is specified by :attr:`cdim` or :attr:`cdim`.
    B : array
        any size array, both complex and real representation are supported.
        For real representation, the real and imaginary dimension is specified by :attr:`cdim` or :attr:`cdim`.
    cdim : int or None, optional
        if :attr:`A` and :attr:`B` are complex arrays but represented in real format, :attr:`cdim` or :attr:`cdim`
        should be specified (Default is :obj:`None`).

    Returns
    -------
    array
        result of element-by-element complex multiplication with the same repesentation as :attr:`A` and :attr:`B`.
    
    Examples
    ----------

    ::

        np.random.seed(2020)
        Ar = np.random.randn(3, 3, 2)
        Br = np.random.randn(3, 3, 2)

        Ac = pb.r2c(Ar)
        Bc = pb.r2c(Br)

        Mr = pb.c2r(Ac * Bc)
        print(np.sum(Mr - ematmul(Ar, Br, cdim=-1)))
        print(np.sum(Ac * Bc - ematmul(Ac, Bc)))

        # output
        array(0)
        array(0j)

    """

def matmul(A, B, **kwargs):
    r"""Complex matrix multiplication

    like A * B in matlab

    Parameters
    ----------
    A : array
        any size array, both complex and real representation are supported.
        For real representation, the real and imaginary dimension is specified by :attr:`cdim` or :attr:`cdim`.
    B : array
        any size array, both complex and real representation are supported.
        For real representation, the real and imaginary dimension is specified by :attr:`cdim` or :attr:`cdim`.
    cdim : int or None, optional
        if :attr:`A` and :attr:`B` are complex arrays but represented in real format, :attr:`cdim` or :attr:`cdim`
        should be specified (Default is :obj:`None`).

    Returns
    -------
    array
        result of complex multiplication with the same repesentation as :attr:`A` and :attr:`B`.
    
    Examples
    ----------

    ::

        np.random.seed(2020)
        Ar = np.random.randn(3, 3, 2)
        Br = np.random.randn(3, 3, 2)

        Ac = pb.r2c(Ar)
        Bc = pb.r2c(Br)

        print(np.sum(np.matmul(Ac, Bc) - matmul(Ac, Bc)))
        Mr = matmul(Ar, Br, cdim=-1)
        Mc = pb.c2r(np.matmul(Ac, Bc))
        print(np.sum(Mr - Mc))

        # output
        array(0j)
        array(0)

    """

def c2r(X, cdim=-1, keepdim=False):
    r"""convert complex-valued array to real-valued array

    Args:
        X (numpy array): input in complex representaion
        cdim (int, optional): complex axis for real-valued array. Defaults to -1.
        keepdim (bool, optional): if :obj:`False`, stacks (make a new axis) at dimension :attr:`cdim`, 
        otherwise concatenates the real and imag part at exist dimension :attr:`cdim`, (Default is :obj:`False`).

    Returns:
        numpy array: output in real representaion

    see also :func:`r2c`

    Examples:

        ::

            import numpy as np

            np.random.seed(2020)

            Xreal = np.random.randint(0, 30, (3, 2, 4))
            Xcplx = r2c(Xreal, cdim=1)
            Yreal = c2r(Xcplx, cdim=0, keepdim=True)

            print(Xreal, Xreal.shape, 'Xreal')
            print(Xcplx, Xcplx.shape, 'Xcplx')
            print(Yreal, Yreal.shape, 'Yreal')
            print(np.sum(Yreal[0] - Xcplx.real), np.sum(Yreal[1] - Xcplx.imag), 'Error')

            # output
            [[[ 0  8  3 22]
            [ 3 27 29  3]]

            [[ 7 24 29 16]
            [ 0 24 10  9]]

            [[19 11 23 18]
            [ 3  6  5 16]]] (3, 2, 4) Xreal

            [[[ 0. +3.j  8.+27.j  3.+29.j 22. +3.j]]

            [[ 7. +0.j 24.+24.j 29.+10.j 16. +9.j]]

            [[19. +3.j 11. +6.j 23. +5.j 18.+16.j]]] (3, 1, 4) Xcplx

            [[[[ 0.  8.  3. 22.]]

            [[ 7. 24. 29. 16.]]

            [[19. 11. 23. 18.]]]


            [[[ 3. 27. 29.  3.]]

            [[ 0. 24. 10.  9.]]

            [[ 3.  6.  5. 16.]]]] (2, 3, 1, 4) Yreal

            0.0 0.0, Error
    """

def r2c(X, cdim=-1, keepdim=False):
    r"""convert real-valued array to complex-valued array

    Convert real-valued array (the size of :attr:`axis` -th dimension is 2) to complex-valued array

    Args:
        X (numpy array): input in real representaion
        cdim (int, optional): the complex axis. Defaults to -1.
        keepdim (bool, optional): if :obj:`False`, discards axis :attr:`cdim`, 
        otherwise preserves the axis :attr:`cdim`, (Default is :obj:`False`). 
        (only work when the dimension at :attr:`cdim` equals 2)

    Returns:
        numpy array: complex-valued array

    Examples:

        ::

            import numpy as np

            np.random.seed(2020)

            Xreal = np.random.randint(0, 30, (3, 2, 4))
            Xcplx = r2c(Xreal, cdim=1)
            Yreal = c2r(Xcplx, cdim=0, keepdim=True)

            print(Xreal, Xreal.shape, 'Xreal')
            print(Xcplx, Xcplx.shape, 'Xcplx')
            print(Yreal, Yreal.shape, 'Yreal')
            print(np.sum(Yreal[0] - Xcplx.real), np.sum(Yreal[1] - Xcplx.imag), 'Error')

            # output
            [[[ 0  8  3 22]
            [ 3 27 29  3]]

            [[ 7 24 29 16]
            [ 0 24 10  9]]

            [[19 11 23 18]
            [ 3  6  5 16]]] (3, 2, 4) Xreal

            [[[ 0. +3.j  8.+27.j  3.+29.j 22. +3.j]]

            [[ 7. +0.j 24.+24.j 29.+10.j 16. +9.j]]

            [[19. +3.j 11. +6.j 23. +5.j 18.+16.j]]] (3, 1, 4) Xcplx

            [[[[ 0.  8.  3. 22.]]

            [[ 7. 24. 29. 16.]]

            [[19. 11. 23. 18.]]]


            [[[ 3. 27. 29.  3.]]

            [[ 0. 24. 10.  9.]]

            [[ 3.  6.  5. 16.]]]] (2, 3, 1, 4) Yreal

            0.0 0.0, Error
    """

def conj(X, cdim=None):
    r"""conjugates a array

    Both complex and real representation are supported.

    Parameters
    ----------
    X : array
        input
    cdim : int or None
        If :attr:`X` is complex-valued, :attr:`cdim` is ignored. If :attr:`X` is real-valued and :attr:`cdim` is integer
        then :attr:`X` will be treated as complex-valued, in this case, :attr:`cdim` specifies the complex axis;
        otherwise (None), :attr:`X` will be treated as real-valued

    Returns
    -------
    array
         the inputs's conjugate matrix.

    Examples
    ---------

    ::

        np.random.seed(2020)
        X = np.random.rand(2, 3, 3)

        print('---conj')
        print(conj(X, cdim=0))
        print(conj(X[0] + 1j * X[1]))

        # ---output
        ---conj
        [[[ 0.98627683  0.87339195  0.50974552]
        [ 0.27183571  0.33691873  0.21695427]
        [ 0.27647714  0.34331559  0.86215894]]

        [[-0.15669967 -0.14088724 -0.75708028]
        [-0.73632492 -0.35566309 -0.34109302]
        [-0.66680305 -0.21710064 -0.56142698]]]
        [[0.98627683-0.15669967j 0.87339195-0.14088724j 0.50974552-0.75708028j]
        [0.27183571-0.73632492j 0.33691873-0.35566309j 0.21695427-0.34109302j]
        [0.27647714-0.66680305j 0.34331559-0.21710064j 0.86215894-0.56142698j]]

    """

def real(X, cdim=None, keepdim=False):
    r"""obtain real part of a array

    Both complex and real representation are supported.

    Parameters
    ----------
    X : array
        input
    cdim : int or None
        If :attr:`X` is complex-valued, :attr:`cdim` is ignored. If :attr:`X` is real-valued and :attr:`cdim` is integer
        then :attr:`X` will be treated as complex-valued, in this case, :attr:`cdim` specifies the complex axis;
        otherwise (None), :attr:`X` will be treated as real-valued
    keepdim : bool, optional
        keep complex-dimension?

    Returns
    -------
    array
         the inputs's real part array.

    Examples
    ---------

    ::

        np.random.seed(2020)
        X = np.random.rand(2, 3, 3)

        print('---real')
        print(real(X, cdim=0))
        print(real(X[0] + 1j * X[1]))

        # ---output
        ---real
        [[0.98627683 0.87339195 0.50974552]
        [0.27183571 0.33691873 0.21695427]
        [0.27647714 0.34331559 0.86215894]]
        [[0.98627683 0.87339195 0.50974552]
        [0.27183571 0.33691873 0.21695427]
        [0.27647714 0.34331559 0.86215894]]
    """

def imag(X, cdim=None, keepdim=False):
    r"""obtain imaginary part of a array

    Both complex and real representation are supported.

    Parameters
    ----------
    X : array
        input
    cdim : int or None
        If :attr:`X` is complex-valued, :attr:`cdim` is ignored. If :attr:`X` is real-valued and :attr:`cdim` is integer
        then :attr:`X` will be treated as complex-valued, in this case, :attr:`cdim` specifies the complex axis;
        otherwise (None), :attr:`X` will be treated as real-valued
    keepdim : bool, optional
        keep complex-dimension?

    Returns
    -------
    array
         the inputs's imaginary part array.

    Examples
    ---------

    ::

        np.random.seed(2020)
        X = np.random.rand(2, 3, 3)

        print('---imag')
        print(imag(X, cdim=0))
        print(imag(X[0] + 1j * X[1]))

        # ---output
        ---imag
        [[0.15669967 0.14088724 0.75708028]
        [0.73632492 0.35566309 0.34109302]
        [0.66680305 0.21710064 0.56142698]]
        [[0.15669967 0.14088724 0.75708028]
        [0.73632492 0.35566309 0.34109302]
        [0.66680305 0.21710064 0.56142698]]

    """

def angle(X, cdim=None, keepdim=False):
    r"""obtain angle

    Both complex and real representation are supported.

    .. math::
       {\rm angle}(x) = {\rm atan}(\frac{v}{u}), x\in {\bf X}

    where, :math:`u, v` are the real and imaginary part of x, respectively.

    Parameters
    ----------
    X : array
        input
    cdim : int or None
        If :attr:`X` is complex-valued, :attr:`cdim` is ignored. If :attr:`X` is real-valued and :attr:`cdim` is integer
        then :attr:`X` will be treated as complex-valued, in this case, :attr:`cdim` specifies the complex axis;
        otherwise (None), :attr:`X` will be treated as real-valued
    keepdim : bool, optional
        keep dimensions? (include complex dim, defalut is :obj:`False`) (only work when the dimension at :attr:`cdim` equals 2)

    Returns
    -------
    array
         the angles of inputs.

    Examples
    ---------

    ::

        np.manual_seed(2020)
        X = np.random.rand((2, 3, 3))

        print('---angle')
        print(angle(X))  # real
        print(angle(X, cdim=0))  # complex in real
        print(angle(X[0] + 1j * X[1]))  # complex in complex

    """

def abs(X, cdim=None, keepdim=False):
    r"""obtain amplitude of a array

    Both complex and real representation are supported.

    .. math::
       {\rm abs}({\bf X}) = |{\bf x}| = \sqrt{u^2 + v^2}, x\in {\bf X}

    where, :math:`u, v` are the real and imaginary part of x, respectively.

    Parameters
    ----------
    X : array
        input
    cdim : int or None
        If :attr:`X` is complex-valued, :attr:`cdim` is ignored. If :attr:`X` is real-valued and :attr:`cdim` is integer
        then :attr:`X` will be treated as complex-valued, in this case, :attr:`cdim` specifies the complex axis;
        otherwise (None), :attr:`X` will be treated as real-valued
    keepdim : bool, optional
        keep complex-dimension?

    Returns
    -------
    array
         the inputs's amplitude.
   
    Examples
    ---------

    ::

        np.random.seed(2020)
        X = np.random.rand(2, 3, 3)

        print('---abs')
        print(abs(X, cdim=0))
        print(abs(X[0] + 1j * X[1]))

        # ---output
        ---abs
        [[0.99864747 0.88468226 0.91269439]
        [0.78490066 0.48990863 0.40424448]
        [0.72184896 0.40619981 1.02884318]]
        [[0.99864747 0.88468226 0.91269439]
        [0.78490066 0.48990863 0.40424448]
        [0.72184896 0.40619981 1.02884318]]

    """

def pow(X, cdim=None, keepdim=False):
    r"""obtain power of a array

    Both complex and real representation are supported.

    .. math::
       {\rm pow}({\bf X}) = |{\bf x}| = u^2 + v^2, x\in {\bf X}

    where, :math:`u, v` are the real and imaginary part of x, respectively.

    Parameters
    ----------
    X : array
        input
    cdim : int or None
        If :attr:`X` is complex-valued, :attr:`cdim` is ignored. If :attr:`X` is real-valued and :attr:`cdim` is integer
        then :attr:`X` will be treated as complex-valued, in this case, :attr:`cdim` specifies the complex axis;
        otherwise (None), :attr:`X` will be treated as real-valued
    keepdim : bool, optional
        keep complex-dimension?

    Returns
    -------
    array
         the inputs's power.
   
    Examples
    ---------

    ::

        np.random.seed(2020)
        X = np.random.rand(2, 3, 3)

        print('---pow')
        print(pow(X, cdim=0))
        print(pow(X[0] + 1j * X[1]))

        # ---output
        ---pow
        [[0.99729677 0.78266271 0.83301105]
        [0.61606904 0.24001046 0.1634136 ]
        [0.52106592 0.16499828 1.05851829]]
        [[0.99729677 0.78266271 0.83301105]
        [0.61606904 0.24001046 0.1634136 ]
        [0.52106592 0.16499828 1.05851829]]

    """

def mean(X, cdim=None, dim=None, keepdim=False):
    r"""mean

    Parameters
    ----------
    X : array
        the input array
    cdim : int or None
        If :attr:`X` is complex-valued, :attr:`cdim` is ignored. If :attr:`X` is real-valued and :attr:`cdim` is integer
        then :attr:`X` will be treated as complex-valued, in this case, :attr:`cdim` specifies the complex axis;
        otherwise (None), :attr:`X` will be treated as real-valued
    dim : int, list or None, optional
        the dimensions for calculation, by default :obj:`None` (all dims)
    keepdim : bool, optional
        keep dimensions? (include complex dim, defalut is :obj:`False`)
    
    Examples
    ---------

    ::

        np.manual_seed(2020)
        X = np.random.rand((2, 3, 3))

        print(mean(X))  # real
        print(mean(X, cdim=0))  # complex in real
        print(mean(X[0] + 1j * X[1]))  # complex in complex

    """    

def var(X, biased=False, cdim=None, dim=None, keepdim=False):
    r"""Calculates the variance over the specified dimensions

    .. math::
       \sigma^2=\frac{1}{N-\delta} \sum_{i=0}^{N-1}\left(x_i-\bar{x}\right)^2
    
    where :math:`\delta = 0` for biased estimation, :math:`\delta = 1` for unbiased estimation.
       
    Parameters
    ----------
    X : array
        the input array
    biased : bool, optional
        :obj:`True` for N, :obj:`False` for N-1, by default :obj:`False`
    cdim : int or None
        If :attr:`X` is complex-valued, :attr:`cdim` is ignored. If :attr:`X` is real-valued and :attr:`cdim` is integer
        then :attr:`X` will be treated as complex-valued, in this case, :attr:`cdim` specifies the complex axis;
        otherwise (None), :attr:`X` will be treated as real-valued
    dim : int, list or None, optional
        the dimensions for calculation, by default :obj:`None` (all dims)
    keepdim : bool, optional
        keep dimensions? (include complex dim, defalut is :obj:`False`)

    Returns
    -------
    array
        the result
            
    Examples
    ---------

    ::

        np.random.setseed(2020)
        X = np.random.rand((2, 3, 3))

        print(var(X))  # real
        print(var(X, cdim=0))  # complex in real
        print(var(X[0] + 1j * X[1]))  # complex in complex

    """

def std(X, biased=False, cdim=None, dim=None, keepdim=False):
    r"""Calculates the standard deviation over the specified dimensions

    Parameters
    ----------
    X : array
        the input array
    biased : bool, optional
        :obj:`True` for N, :obj:`False` for N-1, by default :obj:`False`
    cdim : int or None
        If :attr:`X` is complex-valued, :attr:`cdim` is ignored. If :attr:`X` is real-valued and :attr:`cdim` is integer
        then :attr:`X` will be treated as complex-valued, in this case, :attr:`cdim` specifies the complex axis;
        otherwise (None), :attr:`X` will be treated as real-valued
    dim : int, list or None, optional
        the dimensions for calculation, by default :obj:`None` (all dims)
    keepdim : bool, optional
        keep dimensions? (include complex dim, defalut is :obj:`False`)

    Returns
    -------
    array
        the result

    Examples
    ---------

    ::

        np.random.setseed(2020)
        X = np.random.rand((2, 3, 3))

        print(std(X))  # real
        print(std(X, cdim=0))  # complex in real
        print(std(X[0] + 1j * X[1]))  # complex in complex

    """

def cov(X, Y, biased=False, cdim=None, dim=None, keepdim=False):
    r"""Calculates the covariance over the specified dimensions

    .. math::
       \operatorname{cov}_w(x, y)=\frac{\sum_{i=1}^N\left(x_i-\bar{x}\right)\left(y_i-\bar{y}\right)}{N-\delta}

    where :math:`\delta = 0` for biased estimation, :math:`\delta = 1` for unbiased estimation.

    Parameters
    ----------
    X : array
        the first input array
    Y : array
        the second input array
    biased : bool, optional
        :obj:`True` for N, :obj:`False` for N-1, by default :obj:`False`
    cdim : int or None
        If :attr:`X` is complex-valued, :attr:`cdim` is ignored. If :attr:`X` is real-valued and :attr:`cdim` is integer
        then :attr:`X` will be treated as complex-valued, in this case, :attr:`cdim` specifies the complex axis;
        otherwise (None), :attr:`X` will be treated as real-valued
    dim : int, list or None, optional
        the dimensions for calculation, by default :obj:`None` (all dims)
    keepdim : bool, optional
        keep dimensions? (include complex dim, defalut is :obj:`False`)

    Returns
    -------
    array
        the result
            
    Examples
    ---------

    ::

        np.manual_seed(2020)
        X = np.random.rand((2, 3, 3))
        Y = np.random.rand((2, 3, 3))

        print(cov(X, Y))  # real
        print(cov(X, Y, cdim=0))  # complex in real
        print(cov(X[0] + 1j * X[1], Y[0] + 1j * Y[1]))  # complex in complex

    """

def dot(X, Y, mode='xyh', cdim=None, dim=None, keepdim=False):
    r"""dot product or inner product

    .. math::
       <x,y> = xy^H

    .. note:: 
       the :func:`dot` function in numpy and pytorch compute the inner product by :math:`<x,y> = xy`.

    Parameters
    ----------
    X : array
        the left input
    Y : array
        the right input
    mode : str
        ``'xyh'`` for :math:`<x,y> = xy^H` (default), ``'xy'`` for :math:`<x,y> = xy`, where :math:`y^H` is the complex conjection of :math:`y`
    cdim : int or None
        If :attr:`X` is complex-valued, :attr:`cdim` is ignored. If :attr:`X` is real-valued and :attr:`cdim` is integer
        then :attr:`X` will be treated as complex-valued, in this case, :attr:`cdim` specifies the complex axis;
        otherwise (None), :attr:`X` will be treated as real-valued
    dim : tuple, None, optional
        The dimension axis for computing dot product. The default is :obj:`None`, which means all.
    keepdim : bool
        keep dimensions? (include complex dim, defalut is :obj:`False`)

    Examples
    ---------

    ::

        np.manual_seed(2020)
        X = np.random.rand((2, 3, 3))

        print(dot(X, X))  # real
        print(dot(X, X, cdim=0))  # complex in real
        print(dot(X[0] + 1j * X[1], X[0] + 1j * X[1]))  # complex in complex

    """

def log(x, a=None):
    """returns logarithm of the elements of input

    Parameters
    ----------
    x : float, list, tuple or array
        th input
    a : float, optional
        the base of the logarithmic, by default :obj:`None`

    Returns
    -------
    same as the input
        logarithm value
    """


