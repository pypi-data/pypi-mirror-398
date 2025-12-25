# Linear Programming: Computation of Simplex Tableaux
# Written for CHBE444: Design I, University of Maryland
# (C) Ganesh Sriram, 2025
# Licensed under GNU Public License 3.0
# Author contact info: gsriram@umd.edu


def simplex_tableaux(c, A_ub=[], b_ub=[],
                     var_names=[], slack_names=[],
                     tol=1e-6, decimals=2, dec=2, iters=10,
                     colormap='Greys'):
    """
    Solve an LP by the simplex method, implemented as a series of matrix
        operations.

    Notes:
        This version:
            - Supports inequality constraints only; equality constraints
                are not accepted.
            - Does not update the auxiliary after each pivot.

    Example:
        Tlist = simplex_tableaux(c=[0,-1/2],
                                 A_ub=[[1,-1/2],[-1/3,1/2]],
                                 b_ub=[0,1],
                                 var_names=['x1', 'x3'],
                                 slack_names=['x4','x5'],
                                 tol=1e-6,
                                 decimals=3,
                                 colormap='YlGn')

    Args:
        c: Cost vector specifying objective function.
        A_ub: Matrix containing the coefficients of x_i in the inequality
            constraints (A_ub.x <= b_ub). The number of columns of A_ub
            should equal the number of elements in c. The number of rows
            of A_ub should equal the number of elements in b_ub.
        b_ub: Vector containing the constants in the inequality constraints
            (A_ub.x <= b_ub).
        var_names: Optional column headers in simplex tableaux, specified as
            a list of of strings equal to the number of variables x_i or the
            number of columns in A_ub. If this arg is not specified, these
            headers are created during execution.
        slack_names: Optional row headers in simplex tableaux, specified as
            a list of strings equal to the number of slack variables or the
            number of rows in A_ub. If this arg is not specified, these
            headers are created during execution.
        tol: Tolerance for element of ``z`` row that determines whether
            iterations will continue. Use this arg to suppress iterations
            with little or no incremental benefit. Defaults to 1e-6.
        iters: Number of tableaux to be computed beyond the initial tableau.
            Use this arg to suppress iterations with little or no incremental
            benefit. Defaults to 10.
        decimals: Number of decimals in output. Can also be specified as
            ``dec``. If both ``decimals`` and ``dec`` are specified,
            ``decimals`` overrides. Defaults to 2.
        colormap: Colormap used for conditional formatting of tableaux.
            Choose from the palettes available in Matplotlib:
            https://matplotlib.org/stable/users/explain/colors/colormaps.html.
            Defaults to 'Greys'.

    Returns:
        A list of pandas dataframes, each containing a simplex tableau with
            headers.
    """

    import numpy as np
    import pandas as pd

    # Examine vectors and matrix dimensions for consistency
    Arows = np.size(A_ub, axis=0)
    Acols = np.size(A_ub, axis=1)
    brows = np.size(b_ub)
    ccols = np.size(c)

    if Acols != ccols:
        raise ValueError(
            'Check input dimensions. ' +
            'A and c have different numbers of columns.'
        )
    if Arows != brows:
        raise ValueError(
            'Check input dimensions. ' +
            'A and b have different numbers of rows.'
        )

    if decimals is None:
        decimals = dec

    # Create headers (variable and slack names) if not provided
    if var_names == []:  # create var_names if empty
        var_names = [f"x{j}" for j in range(1, 1 + Acols)]
        # Acols and ccols would have been checked for consistency by now

    var_num = np.size(var_names)
    var_max = max(int(s.lstrip('x')) for s in var_names)

    if slack_names == []:  # create slack_names if empty
        slack_names = [f"x{i}" for i in range(var_max + 1,
                                              var_max + 1 + Arows)]
        # Arows and brows would have been checked for consistency by now

    slack_min = min(int(s.lstrip('x')) for s in slack_names)

    # Create slack_names if empty or index is <= var_max
    if slack_names == [] or slack_min <= var_max:
        slack_names = [f"x{i}" for i in range(var_max + 1,
                                              var_max + 1 + Arows)]
        # Arows and brows would have been checked for consistency by now

    slack_num = np.size(slack_names)

    if Acols != var_num:
        raise ValueError(
            'Check input dimensions. ' +
            'The number of original variables is different ' +
            'from the number of columns of A.'
        )
    if Arows != slack_num:
        raise ValueError(
            'Check input dimensions. ' +
            'The number of slack variables is different ' +
            'from the number of rows of A.'
        )

    # Create initial tableau
    n = np.size(c)  # number of original variables
    m = np.size(b_ub)  # number of slack variables

    # Function to get the ith row of an m x m identity matrix
    def sleq(i, m):
        identity = np.identity(m)
        return identity[i]

    # Construct initial tableau T
    T = np.concatenate(([1], c, np.zeros(m), [0]), 0)

    for i in range(0, m):
        t = np.concatenate(([0],
                            A_ub[i],
                            sleq(i, m),
                            [b_ub[i]]),
                           0)  # current row

        T = np.vstack((T, t))  # append current row below T

    Trows = np.size(T, axis=0)
    Tcols = np.size(T, axis=1)

    aux_needed = False  # compose auxiliary if needed

    c_aux = np.zeros(Tcols)  # initialize cost vector for auxiliary
    for i in range(1, 1 + m):
        if T[i, Tcols - 1] < 0:
            aux_needed = True
            c_aux += T[i]  # update cost vector for auxiliary objective

    if aux_needed is True:
        T = np.insert(T, 1, c_aux, axis=0)
        t = np.concatenate(([0], [1], np.zeros(m)), 0)
        T = np.insert(T, 1, t, axis=1)

    if aux_needed is False:
        row_names = ["z"]
    else:
        row_names = ["z", "z'"]

    for k in range(0, np.size(slack_names)):
        row_names.append(slack_names[k])

    if aux_needed is False:
        col_names = ["z"]
    else:
        col_names = ["z", "z'"]

    for j in range(0, np.size(var_names)):
        col_names.append(var_names[j])
    for i in range(0, np.size(slack_names)):
        col_names.append(slack_names[i])
    col_names.append('b')

    Tlist = [pd.DataFrame(T, columns=col_names,
                          index=row_names)]  # store tableau in a list

    # Use pandas to display T as a tableau
    def conditionally_format_initial(styler):
        styler.background_gradient(axis=None,
                                   vmin=np.min(T),
                                   vmax=np.max(T),
                                   cmap=colormap)
        return styler

    df = pd.DataFrame(T, columns=col_names,
                      index=row_names)
    df_style = df.style.format(
        precision=decimals).pipe(conditionally_format_initial).set_properties(
        **{'text-align': 'center'})

    df_style.set_table_styles([{'selector': 'th.col_heading',
                                'props': 'text-align: center;'},],
                              overwrite=False)
    show_df(df_style)
    N = 0  # iteration number

    Trows = np.size(T, axis=0)
    Tcols = np.size(T, axis=1)

    if aux_needed is True:
        start = 2
        index = 1
    else:
        start = 1
        index = 0

    # Iterate
    stop_condition = False
    while stop_condition is False:
        if aux_needed is True and T[1, Tcols - 1] >= 0:
            aux_needed = False
            index = 0

        pcol = 0  # initialize pivot column
        cval = tol

        for j in range(start, start + m + n):
            if T[index, j] < tol and T[index, j] < cval:
                cval = T[index, j]
                pcol = j  # identify pivot column
        if np.abs(cval) <= tol or N >= iters:
            stop_condition = True

        if stop_condition is False:
            prow = 0  # initialize pivot row
            rval = np.inf
            for i in range(start, start + m):
                if T[i, pcol] > 0 and T[i, Tcols - 1]/T[i, pcol] < rval:
                    rval = T[i, Tcols - 1] / T[i, pcol]
                    prow = i  # identify pivot row

            # Perform pivot
            # Initialize pivoting matrix R to identity matrix
            R = np.identity(Trows)

            # Compile factors to turn pivot column elements above and
            # below pivot element to zero
            factors = -T[:, pcol] / T[prow, pcol]
            factors[prow] = 1  # pivot row is unaltered during pivot
            R[:, prow] = factors

            T = np.dot(R, T)  # pivot operation

            row_names[prow] = col_names[pcol]  # update row headers

            # Append tableau to the list
            Tlist.append(pd.DataFrame(T, columns=col_names,
                                      index=row_names))

            def conditionally_format_current(styler):
                styler.background_gradient(axis=None,
                                           vmin=np.min(T),
                                           vmax=np.max(T),
                                           cmap=colormap)
                return styler

            df = pd.DataFrame(T, columns=col_names,
                              index=row_names)
            df_style = (
                df.style
                .format(precision=decimals)
                .pipe(conditionally_format_current)
                .set_properties(**{'text-align': 'center'})
            )
            df_style.set_table_styles([{'selector': 'th.col_heading',
                                        'props': 'text-align: center;'},],
                                      overwrite=False)
            show_df(df_style)
            N += 1

    return Tlist  # return tableaux as a list of dataframes


def show_df(df):
    """
    Display a DataFrame nicely in Jupyter, or print it in text mode.
    """
    try:
        from IPython.display import display
        display(df)
    except Exception:
        print(df.to_string())
