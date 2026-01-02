def rad2deg(rad):
    r"""radian --> degree

    Parameters
    ----------
    rad : float, list, array or tensor
        radian value data

    Returns
    -------
    tensor
        degree value of input
    """   

def deg2rad(deg):
    r"""degree --> radian

    Parameters
    ----------
    deg : float, list, array or tensor
        degree value data

    Returns
    -------
    tensor
        radian value of input
    """   

def pol2car(r, a, unita='rad'):
    r"""Polar coordinate --> Cartesian coordinate

    .. math::
          \begin{aligned}
            x &= r \cos(a) \\
            y &= r \sin(a)
          \end{aligned}

    Parameters
    ----------
    r : float, list, array or tensor
        polar radius
    a : float, list, array or tensor
        polar angle
    unita : str, optional
        the unit of angle, ``'deg'`` or ``'rad'``, by default ``'rad'``

    Returns
    -------
    tensor
        x coordinates in Cartesian
    tensor
        y coordinates in Cartesian

    Examples
    ---------

    ::

        r, a = 10, 30
        x, y = pol2car(r, a, 'deg')
        print(x, y)
        r, a = car2pol(x, y, 'deg')
        print(r, a)

    """    

def sph2car(r, a, e, unita='rad'):
    r"""Spherical coordinate --> Cartesian coordinate

    .. math::
        \begin{aligned}
            x &= r \cos(e) \cos(a) \\
            y &= r \cos(e) \sin(a) \\
            z &= r \sin(e)
        \end{aligned}

    Parameters
    ----------
    r : float, list, array or tensor
        radius
    a : float, list, array or tensor
        azimuth
    e : float, list, array or tensor
        elevation
    unita : str, optional
        the unit of angle, ``'deg'`` or ``'rad'``, by default ``'rad'``

    Returns
    -------
    tensor
        x coordinates in Cartesian
    tensor
        y coordinates in Cartesian
    tensor
        z coordinates in Cartesian

    Examples
    ---------

    ::

        r, a, e = 10, 30, 60
        x, y, z = sph2car(r, a, e, 'deg')
        print(x, y, z)
        r, a, e = car2sph(x, y, z, 'deg')
        print(r, a, e)

    """   

def car2pol(x, y, unita='rad'):
    r"""Cartesian coordinate --> Spherical coordinate

    Parameters
    ----------
    x : float, list, array or tensor
        x coordinates in Cartesian
    y : float, list, array or tensor
        y coordinates in Cartesian
    unita : str, optional
        the unit of angle, ``'deg'`` or ``'rad'``, by default ``'rad'``

    Returns
    -------
    tensor
        radius in Polar
    tensor
        angle in Polar

    Examples
    ---------

    ::

        r, a = 10, 30
        x, y = pol2car(r, a, 'deg')
        print(x, y)
        r, a = car2pol(x, y, 'deg')
        print(r, a)

    """    

def car2sph(x, y, z, unita='rad'):
    r"""Cartesian coordinate --> Spherical coordinate

    .. math::
        \begin{aligned}
            r &= \sqrt{x^2+y^2+z^2}\\
            a &= \arctan{(\sqrt{x^2+y^2}/z)}\\
            e &= \arctan{(y/x)}
        \end{aligned}

    Parameters
    ----------
    x : float, list, array or tensor
        x coordinates in Cartesian
    y : float, list, array or tensor
        y coordinates in Cartesian
    z : float, list, array or tensor
        z coordinates in Cartesian
    unita : str, optional
        the unit of angle, ``'deg'`` or ``'rad'``, by default ``'rad'``
        
    Returns
    -------
    tensor
        radius in Spherical
    tensor
        azimuth in Spherical
    tensor
        elevation in Spherical

    Examples
    ---------

    ::

        r, a, e = 10, 30, 60
        x, y, z = sph2car(r, a, e, 'deg')
        print(x, y, z)
        r, a, e = car2sph(x, y, z, 'deg')
        print(r, a, e)

    """    


