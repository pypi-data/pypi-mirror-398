def tr2mimo(tc, rc, tid=None, rid=None, otype='list'):
    """calculate mimo array coordinates from transmiter and receiver array coordinates

    Parameters
    ----------
    tc : list, tuple, ndarray
        coordinates of transmit array elements (Nt x ?)
    rc : list, tuple, ndarray
        coordinates of receive array elements (Nr x ?)
    tid : list, tuple or None, optional
        ids of transmit array elements, by default None
    rid : list, tuple or None, optional
        ids of receive array elements, by default None
    otype : str, optional
        output type, by default ``'list'`` or ``'array'``


    Examples
    ---------

    ::

        import pyaibox as pb

        tc = [[0, 0], [0, 1], [0, 2]]
        rc = [[0, 0], [1, 0], [2, 0], [3, 0]]

        mc = pb.tr2mimo(tc, rc)
        plt = pb.scatterxy([[tc, rc, mc]], sizes=None, markers=[['^', 's', 'o']], fcolors=[['none', 'none', 'none']], ecolors=[['r', 'b', 'g']], legends=[['Tx', 'Rx', 'Vx']], grids=True); plt.show()


    """


