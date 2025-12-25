# Ternary VLE Analysis
# Written for CHBE444: Design I, University of Maryland
# (C) Ganesh Sriram, 2025, originally written in MATLAB in 2018
# Licensed under GNU Public License 3.0
# Author contact info: gsriram@umd.edu

import numpy as np
import scipy as sci
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import warnings


class TernarySystem:
    """
    Container for a ternary mixture.

    Notes:
        This class supports a homogeneous, non-ideal liquid phase described by
            the Wilson activity coefficient model (Wilson 1964), in equilibrium
            with an ideal vapor phase (Wilson GM, J. Am. Chem. Soc. 86: 127-
            130, 1964). Vapor pressures are described by the Antoine equation
            in NIST format: log10(P) = A - (B / (T + C), with P in bar and
            T in K.

    Examples:
        sys567 = TernarySystem(  # pentane/hexane/heptane (ideal)
            component_ids=('pen', 'hex', 'hep'),
            component_names={'n-pentane',
                             'n-hexane',
                             'n-heptane'},
            axes={'pen': 0, 'hep': 1},
            Antoine={'pen': {'A': 3.989,   'B': 1070.617, 'C': -40.454},
                     'hex': {'A': 4.00266, 'B': 1171.53,  'C': -48.784},
                     'hep': {'A': 4.02832, 'B': 1268.636, 'C': -56.199}},
                     Wilson_a={'pen': {'pen': 0, 'hex': 0, 'hep': 0},
                               'hex': {'pen': 0, 'hex': 0, 'hep': 0},
                               'hep': {'pen': 0, 'hex': 0, 'hep': 0}},
                     Wilson_b={'pen': {'pen': 0, 'hex': 0, 'hep': 0},
                               'hex': {'pen': 0, 'hex': 0, 'hep': 0},
                               'hep': {'pen': 0, 'hex': 0, 'hep': 0}}
        )

        sysACM = TernarySystem(  # acetone/methanol/chloroform (non-ideal)
            component_ids={'acetone', 'methanol', 'chloroform'},
            component_names={'acetone', 'methanol', 'chloroform'},
            axes={'acetone': 0, 'methanol': 1},
            Antoine={'acetone':    {'A': 4.4245, 'B': 1312.3, 'C': -32.445},
                     'methanol':   {'A': 5.2041, 'B': 1581.3, 'C': -33.5},
                     'chloroform': {'A': 4.2077, 'B': 1233.1, 'C': -40.9530}},
            Wilson_a={
                'acetone': {
                    'acetone': 0,
                    'methanol': 0,
                    'chloroform': -0.7683
                    },
                'methanol': {
                    'acetone': 0,
                    'methanol': 0,
                    'chloroform': 0
                    },
                'chloroform': {
                    'acetone': -0.7191,
                    'methanol': 0,
                    'chloroform': 0
                    }
                },
            Wilson_b={
                'acetone': {
                    'acetone': 0,
                    'methanol': -115.663,
                    'chloroform': 262.1790
                    },
                'methanol': {
                    'acetone': -108.5260,
                    'methanol':  0,
                    'chloroform': -652.8960
                    },
                'chloroform': {
                    'acetone': 435.1440,
                    'methanol': -32.5972,
                    'chloroform': 0
                    }
                },
            P = 1.013
    )

    Args:
        component_ids: Short ids (abbreviations or formulas) for components.
            Enclose component_ids in parentheses.
        component_names: Names or full names of components.
        axes: Dictionary indicating which component is represented on which
            axis. In the example above, component 'pen' is represented on axis
            0 (x-axis) and component 'hep' is represented on axis 1 (y-axis).
        Antoine:  Dictionary of Antoine equation constants from NIST WebBook
            in NIST format (P in bar, T in K).
        Wilson_a, Wilson_b: a_ij and b_ij parameters for Wilson activity
            coefficient correlation.
            - Diagonal elements a_ii and b_ii are always zero.
            - For an ideal liquid mixture, set all a_ij, b_ij to zero.
            - For non-ideal mixtures, obtain a_ij and b_ij from the literature
                or Aspen.
            - To get a_ij and b_ij from Aspen:
             - - Create an Aspen file (in ``apwz`` or ``apw`` format)
                 containing the three compounds in the mixture.
             - - Go to Methods on the left menu pane and select WILSON as the
                 method with default settings.
             - - Navigate to Methods->Parameters->Binary Interaction->Wilson.
             - - Read the parameters a_ij and b_ij from the displayed table.
        P: Pressure of the system (bar). Defaults to 1.013 bar.

    Returns:
        A TernarySystem object containing the specified components, Antoine
            parameters and Wilson parameters.
    """

    def __init__(self, component_ids, component_names, axes,
                 Antoine, Wilson_a, Wilson_b, P=1.013, Tmin=None, Tmax=None):
        self.component_ids = component_ids
        self.components = self.component_ids
        self.component_names = component_names
        self.names = self.component_names
        self.axes = axes
        self.Antoine = Antoine
        self.Wilson_a = Wilson_a
        self.Wilson_b = Wilson_b
        self.P = P

        if self.axes is None:
            raise ValueError('Axes need to be specified')
        if 0 not in list(self.axes.values()):
            raise KeyError('Axis #0 (x-axis) must be specified')
        if 1 not in list(self.axes.values()):
            raise KeyError('Axis #1 (y-axis) must be specified')
        for j in self.components:  # identify implicit component if unspecified
            if j not in self.axes:
                axes[j] = 2

        Ts = self.Tsat(P)

        if Tmin is None:
            Tmin = min(Ts)  # minimum boiling point of system if ideal
        self.Tmin = Tmin

        if Tmax is None:
            Tmax = max(Ts)  # maximum boiling point of system if ideal
        self.Tmax = Tmax

        Tr = (Tmin + Tmax) / 2  # representative temperature of the system
        self.Tr = Tr

    def __repr__(self):
        rows_Ant = '\n'.join(f'          {comp}: {row}'
                             for comp, row in self.Antoine.items())
        rows_a = '\n'.join(f'        {comp}: {row}'
                           for comp, row in self.Wilson_a.items())
        rows_b = '\n'.join(f'        {comp}: {row}'
                           for comp, row in self.Wilson_b.items())
        disp_text = ('Ternary System:\n'
                     f'    component ids:\n\t{self.components}\n'
                     f'    component names:\n\t{self.component_names}\n'
                     f'    axes:\n\t{self.axes}\n'
                     f'    Antoine:\n{rows_Ant}\n'
                     f'    Wilson_b:\n{rows_a}\n'
                     f'    Wilson_b:\n{rows_b}\n')
        return disp_text

    # Temperatures
    T0 = 273.15  # 0 °C in K

    def Psat(self, T):
        """
        Calculate vapor pressure (bar) as a function of T (°C).

        Examples:
            sys567.Psat(60)
            sys567.Psat([60, 100])

        Args:
            T: Temperature in °C. T can be a scalar or an array.

        Returns:
            An array of vapor pressure(s) ``Psat`` at the specified
                temperature(s), with components ordered according to the
                ``axes`` specification used when constructing the
                ``TernarySystem``.
        """

        T = np.asarray(T)
        Psat = np.zeros(T.shape + (3,), dtype=float)  # to vectorize
        for j in self.components:
            if 'A' not in self.Antoine[j]:
                raise KeyError(f"Antoine parameter A is missing for {j}")
            if 'B' not in self.Antoine[j]:
                raise KeyError(f"Antoine parameter B is missing for {j}")
            if 'C' not in self.Antoine[j]:
                raise KeyError(f"Antoine parameter C is missing for {j}")

            A = self.Antoine[j]['A']
            B = self.Antoine[j]['B']
            C = self.Antoine[j]['C']

            Ps = 10**(A - B / (T + self.T0 + C))
            Psat[..., self.axes[j]] = Ps
        return Psat

    def Tsat(self, P):
        """
        Calculate boiling point (°C) as a function of P (bar).

        Examples:
            sys567.Tsat(1.013)
            sys567.Tsat([0.1, 1.0])

        Args:
            P: Pressure in bar. P can be a scalar or an array.

        Returns:
            An array of boiling point(s) ``Tsat`` at the specified
                pressure(s), with components ordered according to the
                ``axes`` specification used when constructing the
                ``TernarySystem``.
        """

        P = np.asarray(P)
        Tsat = np.zeros(P.shape + (3,), dtype=float)  # to vectorize
        for j in self.components:
            if 'A' not in self.Antoine[j]:
                raise KeyError(f"Antoine parameter A is missing for {j}")
            if 'B' not in self.Antoine[j]:
                raise KeyError(f"Antoine parameter B is missing for {j}")
            if 'C' not in self.Antoine[j]:
                raise KeyError(f"Antoine parameter C is missing for {j}")

            A = self.Antoine[j]['A']
            B = self.Antoine[j]['B']
            C = self.Antoine[j]['C']

            Ts = B / (A - np.log10(P)) - C - self.T0
            Tsat[..., self.axes[j]] = Ts
        return Tsat

    def gamma(self, x, T):
        """
        Calculate Wilson activity coefficient as a function of x and T (°C).

        Examples:
            sys567.gamma([0.32, 0.40, 0.28], 60)
            sys567.gamma([[0.32, 0.40, 0.28], [0.46, 0.18, 0.36]], [60, 100])

        Args:
            x: An array of mole fractions, with components ordered
                according to the ``axes`` specification used when
                constructing the ``TernarySystem``. All three mole fractions
                must be specified and must add up to 1. This argument can
                also contain multiple composition points in the form of an
                n x 3 matrix or an m x n x 3 meshgrid, as long as the last
                dimension contains the three mole fractions.
            T: Temperature in °C. If specifying a single composition, T
                should be scalar. If specifying multiple compositions, T
                should be an array with exactly as many elements as the
                number of compositions specified.
        Returns:
            An activity coefficient array ``gamma_i`` of dimension ... x 3,
                with components ordered according to the ``axes``
                specification used when constructing the ``TernarySystem``.
        """

        T = np.asarray(T)
        A = np.zeros(T.shape + (3, 3), dtype=float)  # to vectorize
        for i in self.components:
            for j in self.components:
                A[..., self.axes[i], self.axes[j]] = np.exp(
                    self.Wilson_a[i][j] + self.Wilson_b[i][j] / (T + self.T0)
                )

        x = np.asarray(x)
        Ax = np.einsum('...ij,...j->...i', A, x)
        with np.errstate(divide='ignore', invalid='ignore'):
            xAx = x / Ax
            lng = 1 - np.log(Ax) - np.einsum('...ji,...j->...i', A, xAx)
            g = np.exp(lng)
            return g

    def delxt(self, t, x):
        """
        Calculate the derivative of x with respect to t and express it as
            a function of (t, x).

        Note:
            This function returns the derivative of x without the equilibrium
                temperature. This derivative is used in the computation of
                residue curves.

        Example:
            sys567.delxt(1, [0.32, 0.40, 0.28])

        Args:
            t: A dimensionless, timelike variable.
            x: An array of mole fractions, with components ordered
                according to the ``axes`` specification used when
                constructing the ``TernarySystem``. All three mole fractions
                must be specified and must add up to 1. This argument can
                also contain multiple composition points in the form of an
                n x 3 matrix or an m x n x 3 meshgrid, as long as the last
                dimension contains the mole fractions.

        Returns:
            A derivative array ``dx/dt`` of dimension ... x 3, with
                components ordered according to the ``axes`` specification
                used when constructing the ``TernarySystem``.
        """

        x = np.asarray(x)
        x_shape = x.shape[:-1]
        Tr = np.full(x_shape, [self.Tr])
        T = np.empty(x_shape, dtype=float)
        delxt = np.empty_like(x, dtype=float)

        for i in np.ndindex(x_shape):
            xi = x[i]
            Tr0 = Tr[i]

            with warnings.catch_warnings():
                warnings.simplefilter('ignore', RuntimeWarning)
                res = sci.optimize.root_scalar(
                    lambda T: 1 - np.sum(xi * self.gamma(xi, T) *
                                         self.Psat(T) / self.P),
                    x0=Tr0)
            Ti = res.root
            T[i] = Ti
            g = self.gamma(xi, T)
            Ps = self.Psat(Ti)
            delxt[i] = xi - xi * g * Ps / self.P
        return delxt

    def delxT(self, x):
        """
        Calculate the derivative of x with respect to t, express it as a
            function of x and return it with the corresponding equilibrium
            temperature.

        Note:
            This function returns the derivative of x and the corresponding
                equilibrium temperature, i.e., the bubble point or dew point.
                These values are used in the plotting of equilibrium fields
                as well as in flash and distillation calculations.

        Examples:
            sys567.delxT([0.32, 0.40, 0.28])
            delx, T = sys567.delxT([0.32, 0.40, 0.28])

        Args:
            x: An array of mole fractions, with components ordered
                according to the ``axes`` specification used when
                constructing the ``TernarySystem``. All three mole fractions
                must be specified and must add up to 1. This argument can
                also contain multiple composition points in the form of an
                n x 3 matrix or an m x n x 3 meshgrid, as long as the last
                dimension contains the mole fractions.

        Returns:
            A derivative array ``dx/dt`` of dimension ... x 3, with
                components ordered according to the ``axes`` specification
                used when constructing the ``TernarySystem``.
            An equilibrium temperature value or an array of equilibrium
                temperatures corresponding to the derivatives.
        """

        x = np.asarray(x)
        x_shape = x.shape[:-1]
        Tr = np.full(x_shape, [self.Tr])
        T = np.empty(x_shape, dtype=float)
        delxT = np.empty_like(x, dtype=float)

        for i in np.ndindex(x_shape):
            xi = x[i]
            Tr0 = Tr[i]

            with warnings.catch_warnings():
                warnings.simplefilter('ignore', RuntimeWarning)
                res = sci.optimize.root_scalar(
                    lambda T: 1 - np.sum(xi * self.gamma(xi, T) *
                                         self.Psat(T) / self.P),
                    x0=Tr0
                )
            Ti = res.root
            T[i] = Ti

            g = self.gamma(xi, Ti)
            Ps = self.Psat(Ti)
            delxT[i] = xi - xi * g * Ps / self.P
        return delxT, T

    def delx(self, x):
        """
        Calculate the derivative of x with respect to t and express it
            as a function of x.

        Note:
            This function returns the derivative of x without the equilibrium
                temperature.

        Example:
            sys567.delx([0.32, 0.40, 0.28])

        Args:
            x: An array of mole fractions, with components ordered
                according to the ``axes`` specification used when
                constructing the ``TernarySystem``. All three mole fractions
                must be specified and must add up to 1. This argument can
                also contain multiple composition points in the form of an
                n x 3 matrix or an m x n x 3 meshgrid, as long as the last
                dimension contains the mole fractions.

        Returns:
            A derivative array ``dx/dt`` of dimension ... x 3, with
                components ordered according to the ``axes`` specification
                used when constructing the ``TernarySystem``.
        """

        x = np.asarray(x)
        x_shape = x.shape[:-1]
        Tr = np.full(x_shape, [self.Tr])
        T = np.empty(x_shape, dtype=float)
        delx = np.empty_like(x, dtype=float)

        for i in np.ndindex(x_shape):
            xi = x[i]
            Tr0 = Tr[i]

            with warnings.catch_warnings():
                warnings.simplefilter('ignore', RuntimeWarning)
                res = sci.optimize.root_scalar(
                    lambda T: 1 - np.sum(xi * self.gamma(xi, T) *
                                         self.Psat(T) / self.P),
                    x0=Tr0
                )
            Ti = res.root
            T[i] = Ti

            g = self.gamma(xi, Ti)
            Ps = self.Psat(Ti)
            delx[i] = xi - xi * g * Ps / self.P
        return delx

    def delx2(self, x2):
        """
        Calculate the 2-element derivative of a 2-element vector x with
            respect to t and express it as a function of x. The elements of
            the vector and the derivative correspond with the principal
            axes, i.e., axis 0 (horizontal axis) and axis 1 (vertical axis).

        Note: This function returns the derivative of x without the equilibrium
                temperature. The derivative is used in computing the Jacobian
                and determining stationary points.

        Example:
            sys567.delx([0.32, 0.40])

        Args:
            x2: An array of two mole fractions, with components listed in
                the order specified by the axes argument of the system spec.
                Only two mole fractions must be specified, and they need not
                add up to 1. This argument can also contain multiple
                composition points in the form of an n x 2 matrix or an
                m x n x 2 meshgrid, as long as the last dimension contains
                the two mole fractions.

        Returns:
            A derivative array ``dx/dt`` of dimension ... x 2, with
                the two components ordered according to the ``axes``
                specification used when constructing the ``TernarySystem``.
        """

        x2 = np.asarray(x2)
        if x2.ndim == 1:
            x3 = 1.0 - x2.sum()
            x_full = np.array([x2[0], x2[1], x3])
        else:
            if x2.shape[-1] == 2:
                x_last = x2
            elif x2.shape[0] == 2:
                x_last = np.moveaxis(x2, 0, -1)
            x3 = 1.0 - x_last.sum(axis=-1, keepdims=True)
            x_full = np.concatenate([x_last, x3], axis=-1)

        delx = self.delx(x_full)
        return delx[..., :2]

    def delx2t(self, t, x2):
        """
        Calculate the 2-element derivative of a 2-element vector x2 with
            respect to t and express it as a function of (t, x2).

        Note:
            This function returns the derivative of x without the equilibrium
                temperature. This derivative is used in the computation of
                residue curves and separatrices.

        Example:
            sys567.delx2t(0, [0.32, 0.40])

        Args:
            t: A dimensionless, timelike variable.
            x2: An array of two mole fractions, with components listed in
                the order specified by the axes argument of the system spec.
                Only two mole fractions must be specified, and they need not
                add up to 1. This argument can also contain multiple
                composition points in the form of an n x 2 matrix or an
                m x n x 2 meshgrid, as long as the last dimension contains
                the two mole fractions.

        Returns:
            A derivative array ``dx/dt`` of dimension ... x 2, with
                the two components ordered according to the ``axes``
                specification used when constructing the ``TernarySystem``.
        """

        x2 = np.asarray(x2)
        if x2.ndim == 1:
            x3 = 1.0 - x2.sum()
            x_full = np.array([x2[0], x2[1], x3])
        else:
            if x2.shape[-1] == 2:
                x_last = x2
            elif x2.shape[0] == 2:
                x_last = np.moveaxis(x2, 0, -1)
            x3 = 1.0 - x_last.sum(axis=-1, keepdims=True)
            x_full = np.concatenate([x_last, x3], axis=-1)

        delx = self.delx(x_full)
        return delx[..., :2]

    def yeq(self, x):
        """
        Determine a saturated vapor composition y in equilibrium with a
            saturated liquid composition x, and the bubble point temperature.

        Example:
            sys567.yeq([0.32, 0.40, 0.28])

        Args:
            x: An array of mole fractions, with components listed in the
                order specified by the axes argument of the system spec.
                All three mole fractions must be specified and  must
                add up to 1. This argument can also contain multiple
                composition points in the form of an n x 2 matrix or an
                m x n x 2 meshgrid, as long as the last dimension contains
                the two mole fractions.

        Returns:
            An array of dimension ... x 3 containing the saturated vapor
                composition(s), with components ordered according to the
                ``axes`` specification used when constructing the
                ``TernarySystem``.
            A bubble point temperature value or an array of bubble point
                temperatures corresponding to the saturated vapor
                compositions.
        """

        dx, T = self.delxT(x)
        y = x - dx
        return y, T

    def xeq(self, y):
        """
        Determine a saturated liquid composition x in equilibrium with a
            saturated vapor composition y and the dew point temperature.

        Example:
            sys567.xeq([0.32, 0.40, 0.28])

        Args:
            x: An array of mole fractions, with components listed in the
                order specified by the axes argument of the system spec.
                All three mole fractions must be specified and must add
                up to 1. This argument can also contain multiple
                composition points in the form of an n x 2 matrix or an
                m x n x 2 meshgrid, as long as the last dimension contains
                the two mole fractions.

        Returns:
            An array of dimension ... x 3 containing the saturated liquid
                composition(s), with components ordered according to the
                ``axes`` specification used when constructing the
                ``TernarySystem``.
            A dew point temperature value or an array of dew point
                temperatures corresponding to the saturated liquid
                compositions.

        """

        y = np.asarray(y)
        y_shape = y.shape[:-1]
        x = np.empty_like(y)
        T = np.empty(y_shape)

        for idx in np.ndindex(y_shape):
            yi = y[idx]

            X0 = np.concatenate((yi, [self.Tr]))

            res = sci.optimize.root(
                lambda X: np.append(yi * self.P - X[:3] *
                                    self.gamma(X[:3], X[3]) *
                                    self.Psat(X[3]),
                                    np.sum(X[:3]) - 1),
                x0=X0)
            x[idx] = res.x[:3]
            T[idx] = res.x[3]
        return x, T

    def plot_vle_field(self,
                       fsize=8, font=12, facecolor='white',
                       xy_tol=-1e-6, n_vectors=31, arrow_scale=31,
                       Tmin=None, Tmax=None, contour_T_heavy=10,
                       contour_T_medium=5, contour_T_light=1,
                       **kwargs):
        """
        Plot equilibrium field and constant-temperature contours for a
            ternary vapor-liquid mixture in [x1,x2] or [y1,y2] space.

        Examples:
            fig, ax, _ = sys567.plot_vle_field(
                n_vectors=51, arrow_scale=51,
                contour_T_heavy=10, contour_T_medium=5, contour_T_light=1)

            fig, ax, quiver = sysACM.simulate_vle_field(
                n_vectors=51, arrow_scale=51,
                Tmin=50, Tmax=70,
                contour_T_heavy=1, contour_T_medium=0.5, contour_T_light=0.1)

        Args:
            fsize: Figure size. A square figure with this length is created.
                Defaults to 8.
            font: Base font used for axis labels, etc. Defaults to 12.
            xy_tol: Tolerance for right triangle. Set to slightly less than
                zero, e.g., -1e-6. Defaults to -1e-6.
            n_vectors: Number of e-vectors along each axis. Defaults to 31.
            arrow_scale: Scale of arrows on equilibrium field. Set it
                approximately equal to ``n_vector``. Defaults to 31.
            T_min, T_max: Minimum and maximum temperatures of the system. To
                get all temperature contours to plot, these should be set to
                the minimum and maximum boiling points in the system.
            contour_heavy_T: Temperature increment (°C) for heavy, labeled
                temperature contours. Defaults to 10 °C.
            contour_medium_T: Temperature increment (°C) for medium, unlabeled
                temperature contours. Defaults to 5 °C.
            contour_light_T: Temperature increment (°C) for light, unlabeled
                temperature contours. Defaults to 1 °C.
            **kwargs: Additional keyword arguments passed to
                matplotlib.pyplot.quiver. Common options include ``color``
                and ``linewidth``.
        Returns:
            Figure: Figure object containing the equilibrium field plot.
            Axes: Associated axes object.
        """

        components = self.components
        axes = self.axes
        P = self.P

        def Psat(T):
            return self.Psat(T)

        def gamma(x, T):
            return self.gamma(x, T)

        def delxT(x):
            return self.delxT(x)

        def yeq(x):
            return self.yeq(x)

        def xeq(y):
            return self.xeq(y)

        if Tmin is None:
            Tmin = self.Tmin
        if Tmax is None:
            Tmax = self.Tmax
        Tr = (Tmin + Tmax) / 2  # representative temperature of the system

        fig, ax = plt.subplots(figsize=(fsize, fsize), facecolor=facecolor)
        ax.set_aspect('equal', adjustable='box')
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(1)
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])
        ax.grid(True)
        for j in components:
            if axes[j] == 0:
                ax.set_xlabel(j, fontsize=font)
            if axes[j] == 1:
                ax.set_ylabel(j, fontsize=font)

        X = np.linspace(0, 1, n_vectors)
        xx, yy = np.meshgrid(X, X)

        XY_full = np.stack([xx, yy, 1 - xx - yy], axis=-1)
        mask = 1 - xx - yy >= xy_tol
        XY_flat = XY_full[mask]

        uv_flat, _ = delxT(XY_flat)

        uv = np.full(xx.shape + (3,), np.nan)
        uv[mask] = uv_flat
        uu = uv[..., 0]
        vv = uv[..., 1]

        # Normalize
        mag = np.hypot(uu, vv)
        un, vn = uu, vv
        with np.errstate(invalid='ignore'):
            un = np.where(np.isnan(un), np.nan,
                          np.where(mag > 0, np.divide(uu, mag), 0))
            vn = np.where(np.isnan(vn), np.nan,
                          np.where(mag > 0, np.divide(vv, mag), 0))

        quiver = ax.quiver(X, X, un, vn, angles='xy',
                           color='#8888ff', scale=arrow_scale,
                           alpha=0.5, **kwargs)

        # Calculate and plot temperature contours
        x_contours = 51
        XT = np.linspace(0, 1, x_contours)
        X0, X1 = np.meshgrid(XT, XT)
        Y0, Y1 = np.meshgrid(XT, XT)
        TT0, TT1 = np.meshgrid(XT, XT)

        for i in range(np.size(XT)):
            for j in range(np.size(XT)):
                if XT[i] + XT[j] <= 1:
                    x = [XT[i], XT[j], 1 - XT[i] - XT[j]]
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore', RuntimeWarning)
                        res = sci.optimize.root_scalar(
                            lambda T:
                            1 - np.sum(x * gamma(x, T) * Psat(T) / P),
                            x0=Tr
                        )
                    T = res.root

                    X0[i, j] = XT[i]
                    X1[i, j] = XT[j]
                    TT0[i, j] = T

                    y = x * gamma(x, T) * Psat(T) / P
                    Y0[i, j] = y[0]
                    Y1[i, j] = y[1]
                    TT1[i, j] = T
                else:
                    TT0[i, j] = np.nan
                    TT1[i, j] = np.nan

        def clevels(c):
            tmin = np.round(Tmin / c) * c
            tmax = np.round(Tmax / c + 1) * c
            clevels = np.arange(tmin, tmax, c)
            return clevels

        cl = ax.contour(X0, X1, TT0,
                        levels=clevels(contour_T_heavy),
                        linewidths=0.5, colors='#0000ff')
        ax.clabel(cl, inline=True, fontsize=8)
        ax.contour(X0, X1, TT0,
                   levels=clevels(contour_T_medium),
                   linewidths=0.25, colors='#0000ff')
        ax.contour(X0, X1, TT0,
                   levels=clevels(contour_T_light),
                   linewidths=0.05, colors='#0000ff')

        cl = ax.contour(Y0, Y1, TT1,
                        levels=clevels(contour_T_heavy),
                        linewidths=0.5, colors='#ff0000')
        ax.clabel(cl, inline=True, fontsize=8)
        ax.contour(Y0, Y1, TT1,
                   levels=clevels(contour_T_medium),
                   linewidths=0.25, colors='#ff0000')
        ax.contour(Y0, Y1, TT1,
                   levels=clevels(contour_T_light),
                   linewidths=0.05, colors='#ff0000')

        # Wrap up, save and display plot
        ax.plot([0, 1], [0, 0], 'k-')  # right triangle, horizontal line
        ax.plot([0, 0], [0, 1], 'k-')  # right triangle, vertical line
        ax.plot([0, 1], [1, 0], 'k-')  # right triangle, diagonal line

        plt.draw()
        return fig, ax, quiver

    draw_vle_field = plot_vle_field
    simulate_vle_field = plot_vle_field

    def plot_residue_curve(self, ax, feed=None,
                           integration_direction='both',
                           integration_time=10, max_step=np.inf,
                           show_feed=True,
                           separatrix=False, **kwargs):
        """
        Plot (a) residue curve(s) for a ternary vapor-liquid mixture from a
            specified (a) feed point(s).

        Examples:
            sys567.plot_residue_curve(
                ax, feed=[
                    [0.33, 0.33, 0.34],
                    [0.32, 0.40, 0.28]
                ],
                show_feed=True, max_step=0.1, color='k', ls='-', lw=1.5)

            sys567.plot_residue_curve(
                ax, feed={
                    0: {'pen': 0.33, 'hex': 0.34, 'hep': 0.33},
                    1: {'pen': 0.32, 'hex': 0.28, 'hep': 0.40}
                    },
                    show_feed=True, max_step=0.1, color='k', ls='-', lw=1.5
            )

            ax, res_fwd, res_bwd = sysACM.plot_residue(
                ax, feed={
                    0: {'acetone': 0.4, 'methanol': 0.2, 'chloroform': 0.4},
                    1: {'acetone': 0.6, 'methanol': 0.2, 'chloroform': 0.2},
                    2: {'acetone': 0.2, 'methanol': 0.6, 'chloroform': 0.2},
                    3: {'acetone': 0.5, 'methanol': 0.4, 'chloroform': 0.1}
                },
                integration_time=20, max_step=0.5, show_feed=True,
                linestyle='--', color='k', marker='o', markersize=6
            )

        Args:
            ax: Axes on which residue curve(s) is (are) to be plotted.
            feed: Feed point. One or more feeds can be specified as a
                1 x 3 vector or an n x 3 matrix, as long as the last
                dimension contains the three mole fractions with components
                ordered according to the ``axes`` specification used when
                constructing the ``TernarySystem``. The feed(s) can also be
                as a nested dictionary as shown in the example above.
            integration_direction: Direction of integration. Options are:
                ``both``: forward and backward in time,
                ``positive``, ``pos``, ``forward``, ``fwd``: forward in time,
                ``negative``, ``neg``, ``backward``, ``bwd``: backward in time.
                Defaults to 'both'.
            integration_time: Integration time for forward and backward residue
                curves. Defaults to 10. If different integration times are
                needed in each direction, specify the curves separately setting
                ``integration_direction`` to ``pos`` and ``neg``, respectively.
            max_step: Maximum integration step. Defaults to infinity. Set it
                to a low value, e.g., 0.05 or 0.10, if the residue curve
                is not continuous or contains kinks. Setting this
                parameter to < 1 will slow down residue curve plotting.
                Defaults to infinity (``np.inf``) for regular residue curves
                and 0.2 for separatrices.
            show_feed: True/False value indicating whether feed should be
                displayed as a point.
            separatrix: True/False value indicating whether residue curve is
                a separatrix. This is automatically set to True when called
                by ``plot_separatrices``.
            **kwargs: Additional keyword arguments passed to matplotlib.pyplot.
                Common options include ``linewidth`` for the residue curve and
                ``marker`` for the feed point(s).

        Returns:
            Axes passed to the function and if requested, objects containing
                the residue curve coordinates and other results from
                ``scipy.optimize.solve_ivp``.
        """

        # Parse kwargs
        common_keys = {'color', 'c',
                       'alpha'}  # shared between point and line

        point_keys = {
                'marker',
                'markersize', 'ms',
                'markerfacecolor', 'mfc',
                'markeredgecolor', 'mec',
                'markeredgewidth', 'mew',
                'fillstyle',
            }

        line_keys = {
            'linewidth', 'lw',
            'drawstyle',
            'dash_capstyle',
            'dash_joinstyle',
            'solid_capstyle',
            'solid_joinstyle',
            'antialiased',
        }

        common_kwargs, point_kwargs, line_kwargs = {}, {}, {}

        for key, value in kwargs.items():
            if key in common_keys:
                common_kwargs[key] = value
            elif key in point_keys:
                point_kwargs[key] = value
            elif key in line_keys:
                line_kwargs[key] = value
            else:
                pass

        point_kwargs = {**common_kwargs, **point_kwargs}
        line_kwargs = {**common_kwargs, **line_kwargs}

        if feed is None:
            raise ValueError(
                'Feed point(s) must be specified ' +
                'if residue curve is requested'
            )

        if not separatrix:
            # If not plotting a separatrix, a 3-D derivative is being used
            # Check the dimension and mole fraction sum of the feed
            if isinstance(feed, dict):
                row_sums = {i: sum(d.values()) for i, d in feed.items()}
                for i, total in row_sums.items():
                    if abs(total - 1) > 1e-6:
                        raise ValueError(
                            'Residue curve feed mole fractions must add ' +
                            f"up to 1: got {total} for row {i}"
                        )
            elif isinstance(feed, (list, np.ndarray)):
                feed = np.asarray(feed)
                if feed.ndim == 1:  # feed is a vector: single feed point
                    total = np.sum(feed)
                    if abs(total - 1) > 1e-6:
                        raise ValueError(
                            'Residue curve feed mole fractions must add ' +
                            f"up to 1: got {total}"
                        )
                elif feed.ndim == 2:  # feed is a matrix: multiple feed points
                    total = np.sum(feed, axis=-1)
                    for i in range(len(total)):
                        if abs(total[i] - 1) > 1e-6:
                            raise ValueError(
                                'Residue curve feed mole fractions must add \n'
                                + f"up to 1: got {total[i]} for row {i}"
                            )
                else:
                    raise ValueError(
                        'Residue curve feed must have dimension <= 2'
                    )
            else:
                pass  # feed is of unexpected data type

        if isinstance(feed, dict):
            x_feed = np.zeros((len(feed), 3))
            ii = 0
            for i in feed:
                for jj in feed[i]:
                    x_feed[ii, self.axes[jj]] = feed[i][jj]
                ii += 1
        else:
            x_feed = feed

        if not separatrix:
            func = self.delxt  # 3-D derivative
            events = out_of_triangle  # 3-D version
        else:
            func = self.delx2t  # 2-D derivative
            events = out_of_triangle2  # 2-D version

        res_fwd = []
        res_bwd = []
        for row in np.atleast_2d(x_feed):
            xF = row
            if show_feed:
                ax.plot(xF[0], xF[1], **point_kwargs)
            with np.errstate(all='ignore'):
                int_t = integration_time
                if integration_direction.lower() in ('both',
                                                     'positive',
                                                     'forward',
                                                     'pos', 'fwd'):
                    residue_fwd = sci.integrate.solve_ivp(func,
                                                          [0, int_t], xF,
                                                          method='DOP853',
                                                          events=events,
                                                          max_step=max_step)
                    ax.plot(residue_fwd.y[0, :], residue_fwd.y[1, :],
                            **line_kwargs)
                else:
                    residue_fwd = []
                res_fwd.append(residue_fwd)

                if integration_direction.lower() in ('both',
                                                     'negative',
                                                     'backward',
                                                     'neg', 'bwd'):
                    residue_bwd = sci.integrate.solve_ivp(func,
                                                          [0, -int_t], xF,
                                                          method='DOP853',
                                                          events=events,
                                                          max_step=max_step)
                    ax.plot(residue_bwd.y[0, :], residue_bwd.y[1, :],
                            **line_kwargs)
                else:
                    residue_bwd = []
                res_bwd.append(residue_bwd)

        return ax, res_fwd, res_bwd

    plot_residue = plot_residue_curve
    draw_residue = draw_residue_curve = plot_residue_curve
    simulate_residue = simulate_residue_curve = plot_residue_curve
    integrate_residue = integrate_residue_curve = plot_residue_curve

    def vle_properties(self, z, decimals=3):
        """
        Calculate VLE properties of a ternary mixture defined by a composition
            vector z.

        Example:
            system.vle_properties([0.3, 0.6, 0.1])
            system.mixture_properties([[0.3, 0.6, 0.1], [0.2, 0.3, 0.5]])

        Args:
            z: The overall composition of the mixture, averaged over the
                liquid and vapor phases. The coordinates should be ordered
                according to the ``axes`` specification used when
                constructing the ``TernarySystem``. All three mole fractions
                must be specified and must add up to 1. This argument can
                also contain multiple composition points in the form of an
                n x 3 matrix or an m x n x 3 meshgrid, as long as the last
                dimension contains the three mole fractions.

        Returns:
            A VLEProperties object containing the compositions and temperatures
                of the mixture's bubble point and dew point.
        """
        ye, Tb = self.yeq(z)
        xe, Td = self.xeq(z)
        p = VLEProperties(P=self.P,
                          molefrac=z,
                          yeq=ye,
                          xeq=xe,
                          T_bubl=Tb,
                          T_dew=Td,
                          decimals=decimals)
        return p

    mixture_properties = vle_properties

    def find_stationary_points(self,
                               n_complex=500, iters=1,
                               tol=1e-6, ftol=1e-12,
                               decimals=3):
        """
        Find the stationary points of a ternary vapor-liquid mixture, and
            determine their stability by computing the eigenvalues of the
            system Jacobian. Stationary points are compositions at which
            ``y = x`` and ``dx/dt = 0``.

        Examples:
            sys567.find_stationary_points()
            sysACM.find_stationary_points()

        Args:
            n_complex: Number of points in the simplicial complex in the
                search algorithm. Defaults to 500.
            iters: Number of iterations in the construction of the simplicial
                complex. Defaults to 1.
            ftol: Tolerance for stationary points. Defaults to 1e-12.
            tol: Tolerance for checking positivity or negativity of
                eigenvalues to determine stability. Defaults to 1e-6.
            decimals: Number of decimals used in displaying output.
                Defaults to 3.

        Returns:
            A StationaryPoints object containing the coordinates of the
                stationary points, along with their boiling points (°C),
                eigenvalues (of the local Jacobian) and stabilities.

        """

        res = sci.optimize.shgo(
            lambda x: np.linalg.norm(self.delx(x)),
            bounds=[(0, 1), (0, 1), (0, 1)],
            constraints={sci.optimize.LinearConstraint(A=[1, 1, 1], ub=1)},
            n=n_complex, iters=iters, sampling_method='sobol',
            options={'ftol': ftol}
        )
        x_stat = np.vstack((res.xl, [[1, 0, 0], [0, 1, 0], [0, 0, 1]]))
        x_stat = np.unique(np.round(x_stat, 6), axis=0)

        _, T = self.delxT(x_stat)

        x2 = x_stat[:, :2]
        eigenvals = np.empty((0, 2))
        stability = []
        for row in x2:
            A2 = sci.optimize.approx_fprime(row, self.delx2)
            e = sci.linalg.eigvals(A2).real
            eigenvals = np.vstack([eigenvals, e.ravel()])
            sign0 = sign_tol(e[0])
            sign1 = sign_tol(e[1])
            if sign0 == 1 and sign1 == 1:
                stability.append('unstable')
            elif sign0 == -1 and sign1 == -1:
                stability.append('stable')
            elif sign0 == -1 and sign1 == 1:
                stability.append('saddle')
            elif sign0 == 1 and sign1 == -1:
                stability.append('saddle')
            else:
                # Zero eigenvalue encountered
                # Linear system cannot be used to conclude stability
                stability.append('inconclusive')

        res = StationaryPoints(x=x_stat,
                               T=T,
                               eigenvals=eigenvals,
                               stability=stability,
                               decimals=decimals)
        return res

    def plot_separatrices(self, ax,
                          stationary_points=None,
                          vertex_tol=1e-5,
                          eigen_tol=1e-5,
                          separatrix_feed_dx=1e-6,
                          integration_time=100,
                          max_step=0.2,
                          **kwargs):
        """
        Plot separatrices for a ternary vapor-liquid mixture.

        Note:
            Separatrices are plotted from interior saddle points, i.e.,
                saddle points that are not vertices of the triangle.
                If no separatrices are found, the function returns either
                nothing or a list of stationary points.

        Examples:
            sysACM.plot_separatrices(ax, c='g', ls='-')
            sysACM.plot_separatrices(ax, stationary_points=res,
                                     c='g', ls='-')

        Args:
            ax: Axes on which separatrices are to be plotted.
            stationary_points: A StationaryPoints object containing the
                coordinates of the stationary points, their boiling points,
                eigenvalues and stabilities. This argument is optional. Specify
                if stationary points were previously computed. If not
                specified, stationary points will be computed before plotting
                separatrices.
            vertex_tol: Tolerance for checking whether a stationary point is
                on a vertex of the triangle. Defaults to 1e-5.
            eigen_tol: Tolerance for checking nonnegativity of an eigenvalue.
                Defaults to 1e-5.
            separatrix_feed_dx: The distance from an interior saddle point to
                the feed of each separatrix. Defaults to 1e-6.
            integration_time: Integration time for forward and backward residue
                branches of each separatrix. Defaults to 100.
            max_step: Maximum integration step. Defaults to infinity. Set it
                to a low value, e.g., 0.05 or 0.10, if the separatrix
                contains kinks or other artifacts of integration. Setting this
                parameter to < 1 will slow down separatrix plotting.
                Defaults to 0.2.
            **kwargs: Additional keyword arguments passed to matplotlib.pyplot.
                Common options include ``color`` (``c``), ``linewidth``
                (``lw``) and ``linestyle`` (``ls``).

        Returns:
            Axes passed to the function and if requested, objects containing
                the residue curve coordinates and other results from
                ``scipy.optimize.solve_ivp``.
        """

        if stationary_points is None:
            res = self.find_stationary_points()
        else:
            res = stationary_points

        residue = []
        for i in range(len(res.T)):
            if res.stability[i] == 'saddle':
                vertex_distance = euclidean_distance(
                    res.x[i], [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
                )  # distance from stationary point to all 3 vertices
                # If stationary point is not vertex
                if np.all(vertex_distance > vertex_tol):
                    x2 = res.x[i][:2]
                    A2 = sci.optimize.approx_fprime(x2, self.delx2)
                    w, v = sci.linalg.eig(A2)

                    for j in range(len(w.real)):
                        feed_a = x2 + v[j] * separatrix_feed_dx
                        feed_b = x2 - v[j] * separatrix_feed_dx

                        feed = []
                        feed.append(feed_a)
                        feed.append(feed_b)
                        feed = np.vstack(feed)

                        if w.real[j] > eigen_tol:
                            residue_pos = self.plot_residue_curve(
                                ax, feed=feed,
                                integration_direction='pos',
                                integration_time=integration_time,
                                max_step=max_step,
                                show_feed=False, separatrix=True,
                                **kwargs
                            )
                            residue.append(residue_pos)
                        elif w.real[j] < -eigen_tol:
                            residue_neg = self.plot_residue_curve(
                                ax, feed=feed,
                                integration_direction='neg',
                                integration_time=integration_time,
                                max_step=max_step,
                                show_feed=False, separatrix=True,
                                **kwargs
                            )
                            residue.append(residue_neg)
                        else:
                            pass  # eigenvalue is zero within tolerance
        return ax, residue

    plot_separatrix = plot_separatrices
    draw_separatrix = plot_separatrix
    simulate_separatrix = plot_separatrix
    integrate_separatrix = plot_separatrix
    draw_separatrices = plot_separatrices
    simulate_separatrices = plot_separatrices
    integrate_separatrices = plot_separatrices

    def atanm(self, x):
        """
        Modified arctan function, returns a result in the range (0, π).
        """

        ang = np.atan(x)
        if ang < 0:
            ang = ang + np.pi
        return ang

    def angle_dx(self, x):
        """
        Angle in the range (0, π) made by the equilibrium vector with the
            positive x-axis.
        """

        dx, T = self.delxT(x)
        if abs(dx[0]) <= 1e-6:
            angle = np.pi / 2
        else:
            slope = dx[1] / dx[0]
            angle = self.atanm(slope)
        return angle

    def angle_xy(self, x, y):
        """
        Angle in the range (0, π) made by a vector connecting the points
            x and y with the positive x-axis.
        """

        if np.abs(x[0] - y[0]) <= 1e-6:
            angle = np.pi / 2
        else:
            slope = (x[1] - y[1]) / (x[0] - y[0])
            angle = self.atanm(slope)
        return angle

    def flash_T_objective(self, x, xF, T):
        """
        Objective function for ``flash_at_T``.
        """

        z = ((self.angle_dx(x) - self.angle_xy(x, xF))**2 +
             (self.yeq(x)[1] - T)**2 +
             (self.xeq(self.yeq(x)[0])[1] - T)**2)
        return z

    def flash_at_T(self, xF, T=25, decimals=3):
        """
        Perform a flash calculation by specifying the flash temperature.
        """

        eq_cons = {'type': 'eq',
                   'fun': lambda x: np.sum(x) - 1}

        bounds = sci.optimize.Bounds([0, 0, 0], [1, 1, 1])
        res = sci.optimize.minimize(lambda x: self.flash_T_objective(x, xF, T),
                                    x0=xF,
                                    method='SLSQP',
                                    constraints=[eq_cons],
                                    bounds=bounds,
                                    tol=1e-9)

        x = res.x
        y = self.yeq(x)[0]
        T = self.yeq(x)[1]
        Vfrac = np.linalg.norm(x - xF) / np.linalg.norm(x - y)

        res = FlashResult(xF=xF,
                          x=x,
                          y=y,
                          T=T,
                          P=self.P,
                          Lfrac=1 - Vfrac,
                          Vfrac=Vfrac,
                          decimals=decimals)
        return res

    def flash_Vfrac_objective(self, x, xF, Vfrac=0.5):
        """
        Objective function for ``flash_at_Vfrac``.
        """

        x = np.array(x)
        Tx = self.vle_properties(x).T_bubl
        xF = np.array(xF)
        y, Ty = self.yeq(x)

        z = ((self.angle_dx(x) - self.angle_xy(x, xF))**2 +
             (np.linalg.norm(x - xF) / np.linalg.norm(x - y) - Vfrac)**2 +
             (Tx - Ty)**2)
        return z

    def flash_at_Vfrac(self, xF, Vfrac, decimals=3):
        """
        Perform a flash calculation by specifying the vapor fraction
            (``Vfrac``) of the flash evaporator.
        """

        eq_cons = {'type': 'eq',
                   'fun': lambda x: np.sum(x) - 1}

        bounds = sci.optimize.Bounds([0, 0, 0], [1, 1, 1])
        res = sci.optimize.minimize(
            lambda x: self.flash_Vfrac_objective(x, xF, Vfrac),
            x0=xF,
            method='SLSQP',
            constraints=[eq_cons],
            bounds=bounds,
            tol=1e-9)

        x = res.x
        y = self.yeq(x)[0]
        T = self.yeq(x)[1]
        Vfrac = np.linalg.norm(x - xF) / np.linalg.norm(x - y)

        res = FlashResult(xF=xF,
                          x=x,
                          y=y,
                          T=T,
                          P=self.P,
                          Lfrac=1 - Vfrac,
                          Vfrac=Vfrac,
                          decimals=decimals)
        return res

    def draw_flash_bfd(self, flash_res):
        """
        Draw a BFD of a flash evaporator.
        """

        res = flash_res

        P_str = np.round(res.P, 2)
        T_str = np.round(res.T, 2)
        xF_str = np.round(res.xF, 2)

        if res.x is None:
            x_str = '?'
        else:
            x_str = np.round(res.x, 2)

        if res.y is None:
            y_str = '?'
        else:
            y_str = np.round(res.y, 2)

        if res.Vfrac is None:
            Vfrac_str = '?'
        else:
            Vfrac_str = np.round(res.Vfrac, 2)

        fig1, ax1 = plt.subplots()
        plt.axis('off')
        _ = ax1.set_xlim(-4, 4)
        _ = ax1.set_ylim(-4, 4)

        patches.ArrowStyle.Curve

        feed = patches.Arrow(-3, 0, 2, 0, width=0.5, color='black')
        ax1.add_patch(feed)

        ax1.text(-1.1, 0.2,
                 f"xF = {xF_str}",
                 ha='right',
                 va='bottom',
                 fontsize=8,
                 color='black')

        vap = patches.Arrow(1, 1.6, 2, 0, width=0.5, color='red')
        ax1.add_patch(vap)

        ax1.text(1.1, 1.8,
                 f"y = {y_str}",
                 ha='left',
                 va='bottom',
                 fontsize=8,
                 color='red')

        liq = patches.Arrow(1, -1.6, 2, 0, width=0.5, color='blue')
        ax1.add_patch(liq)

        ax1.text(1.1, -1.4,
                 f"x = {x_str}",
                 ha='left',
                 va='bottom',
                 fontsize=8,
                 color='blue')

        unit = patches.Rectangle((-1, -2), 2, 4,
                                 linewidth=2,
                                 edgecolor='black',
                                 facecolor='white',
                                 alpha=1)
        ax1.add_patch(unit)

        ax1.text(0, 0.5, 'Flash',
                 ha='center',
                 va='center',
                 fontsize=10)

        ax1.text(0, 0, f"P = {P_str} bar",
                 ha='center',
                 va='center',
                 fontsize=8)

        ax1.text(0, -0.5, f"T = {T_str} °C",
                 ha='center',
                 va='center',
                 fontsize=8)

        ax1.text(2, 0, f"Vfrac = {Vfrac_str}",
                 ha='center',
                 va='center',
                 fontsize=8)

        return fig1, ax1


class VLEProperties:
    """
    Container for the properties of a ternary mixture at a specified
        composition.
    """

    def __init__(self, P, molefrac, yeq, xeq, T_bubl, T_dew, decimals):
        self.P = P
        self.molefrac = molefrac
        self.yeq = yeq
        self.xeq = xeq
        self.T_bubl = T_bubl
        self.T_dew = T_dew
        self.decimals = decimals

    def __repr__(self):
        d = self.decimals
        z = np.asarray(self.molefrac)

        if z.ndim == 1:  # single composition
            z_str = indent_array(z, tabs=0, precision=d)
            yeq = indent_array(self.yeq, tabs=0, precision=d)
            T_bubl = indent_array(self.T_bubl, tabs=0, precision=d)
            xeq = indent_array(self.xeq, tabs=0, precision=d)
            T_dew = indent_array(self.T_dew, tabs=0, precision=d)
            disp_text = ('Mixture VLE properties:\n'
                         f'    Pressure (P, bar): {self.P:.{d}f}\n'
                         f'    Overall composition (z): {z_str}\n'
                         f'    If this mixture were a saturated liquid:\n'
                         f'        Vapor in equilibrium (yeq): '
                         f'{yeq}\n'
                         f'        Bubble T (T_bubl, °C): '
                         f'{T_bubl}\n'
                         f'    If this mixture were a saturated vapor:\n'
                         f'        Liquid in equilibrium (xeq): '
                         f'{xeq}\n'
                         f'        Dew T (T_dew, °C): {T_dew} °C\n'
                         f'    Compositions are reported as mole fractions\n')
        else:  # multiple compositions
            z_str = indent_array(z, tabs=1, precision=d)
            yeq = indent_array(self.yeq, tabs=2, precision=d)
            T_bubl = indent_array(self.T_bubl, tabs=2, precision=d)
            xeq = indent_array(self.xeq, tabs=2, precision=d)
            T_dew = indent_array(self.T_dew, tabs=2, precision=d)
            disp_text = ('Mixture VLE properties:\n'
                         f'    Pressure (P, bar): {self.P:.{d}f}\n'
                         f'    Overall composition (z):\n{z_str}\n'
                         f'    If this mixture were a saturated liquid:\n'
                         f'        Vapor in equilibrium (yeq):\n{yeq}\n'
                         f'        Bubble T (T_bubl, °C):\n{T_bubl}\n'
                         f'    If this mixture were a saturated vapor:\n'
                         f'        Liquid in equilibrium (xeq):\n{xeq}\n'
                         f'        Dew T (T_dew, °C):\n{T_dew} °C\n'
                         f'    Compositions are reported as mole fractions\n')
        return disp_text


class StationaryPoints:
    """
    Container for the result of stationary point search.
    """

    def __init__(self, x, T, eigenvals, stability, decimals):
        self.x = x
        self.T = T
        self.eigenvals = eigenvals
        self.stability = stability
        self.decimals = decimals

    def __repr__(self):
        d = self.decimals
        disp_text = ''
        for i in range(len(self.T)):
            disp_row = (
                '[' +
                ', '.join(f'{self.x[i, j]:.{d}f}' for j in range(3)) + ']' +
                '  ' + f'{self.T[i]:{d + 4}.{d}f} °C' +
                '  eigenvalues: ' +
                '  '.join(f'{self.eigenvals[i, j]:+.{d}f}' for j in range(2)) +
                '  ' + (f'({self.stability[i]})\n')
            )
            disp_text = disp_text + disp_row
        return disp_text


class FlashResult:
    """
    Container for the result of a flash calculation.
    """

    def __init__(self, xF, x, y, T, P, Lfrac, Vfrac, decimals):
        self.xF = xF
        self.x = x
        self.y = y
        self.P = P
        self.T = T
        self.Lfrac = Lfrac
        self.Vfrac = Vfrac
        self.decimals = decimals

    def __repr__(self):
        d = self.decimals
        xF_str = indent_array(np.asarray(self.xF), tabs=0, precision=d)
        x_str = indent_array(np.asarray(self.x), tabs=0, precision=d)
        y_str = indent_array(np.asarray(self.y), tabs=0, precision=d)

        disp_text = ('Flash results:\n'
                     f'    Feed: {xF_str}\n'
                     f'    Liquid product (x): {x_str}\n'
                     f'    Vapor product (y): {y_str}\n'
                     f'    Temperature (T, °C): {self.T:.{d}f}\n'
                     f'    Pressure (P, bar): {self.P:.{d}f}\n'
                     f'    Liquid fraction (Lfrac): {self.Lfrac:.{d}f}\n'
                     f'    Vapor fraction (Vfrac): {self.Vfrac:.{d}f}\n'
                     f'    Compositions are reported as mole fractions\n')
        return disp_text


class DistillationResult:
    """
    Container for the result of a distillation calculation.
    """

    def __init__(self, xF, xD, xB, D, B, q, r, s,
                 nstg, fstg, xLr, yVr, Tr, xLs, yVs, Ts, P, decimals):
        self.xF = xF
        self.xD = xD
        self.xB = xB
        self.D = D
        self.B = B
        self.q = q
        self.r = r
        self.s = s
        self.nstg = nstg
        self.fstg = fstg
        self.xLr = xLr
        self.yVr = yVr
        self.Tr = Tr
        self.xLs = xLs
        self.yVs = yVs
        self.Ts = Ts
        self.P = P
        self.decimals = decimals

    def __repr__(self):
        d = self.decimals

        stage_text_r = "Stagewise results (R-section):\n"
        for i in range(len(self.Tr)):
            xLr_row = (
                '[' +
                '  '.join(f'{val:{d + 4}.{d}f}' for val in self.xLr[i])
                + ']'
            )
            yVr_row = (
                '[' +
                '  '.join(f'{val:{d + 4}.{d}f}' for val in self.yVr[i])
                + ']'
            )
            stage_text_r += f'    # {i+1:4d}  xL (liq): {xLr_row}  '
            stage_text_r += f"yV (vap): {yVr_row}  "
            stage_text_r += f"T: {self.Tr[i, 0]:{d + 4}.{d}f} °C\n"

        stage_text_s = "Stagewise results (S-section):\n"
        for i in range(len(self.Ts)):
            xLs_row = (
                '[' +
                '  '.join(f'{val:{d + 4}.{d}f}' for val in self.xLs[i])
                + ']'
            )
            yVs_row = (
                '[' +
                '  '.join(f'{val:{d + 4}.{d}f}' for val in self.yVs[i])
                + ']'
            )
            stage_text_s += f'    # {i+1:4d}  xL (liq): {xLs_row}  '
            stage_text_s += f"yV (vap): {yVs_row}  "
            stage_text_s += f"T: {self.Ts[i, 0]:{d + 4}.{d}f} °C\n"

        xF_str = indent_array(np.asarray(self.xF), tabs=0, precision=d)
        disp_text = ('Distillation parameters:\n'
                     f'    Feed: {xF_str}\n'
                     f'    Distillate composition (xD): {self.xD:.{d}f}\n'
                     f'    Bottoms composition (xB): {self.xB:.{d}f}\n'
                     f'    Distillate flow rate (D): {self.D:.{d}f}\n'
                     f'    Bottoms flow rate (B): {self.B:.{d}f}\n'
                     f'    Feed quality (q): {self.q:.{d}f}\n'
                     f'    Reflux ratio (r): {self.r:.{d}f}\n'
                     f'    Boilup ratio (s): {self.s:.{d}f}\n'
                     f'    Number of stages (nstg): {self.nstg}\n'
                     f'    Feed stage (fstg): {self.fstg}\n'
                     f'    Pressure (P, bar): {self.P:.{d}f}\n'
                     f'{stage_text_r}'
                     f'{stage_text_s}'
                     'Compositions are reported as mole fractions\n'
                     'Flows are molar relative to the feed\n')
        return disp_text


def normalize_fraction(x, tol=1e-4):
    """
    Normalize a ternary mole fraction array.

    Example:
        normalize_fraction([0.35, 0.20, 0.15], tol=1e-4)

    Args:
        x: An array of mole fractions, with components ordered
            according to the ``axes`` specification used when
            constructing the ``TernarySystem``. All three mole fractions
            must be specified and must add up to 1. This argument can
            also contain multiple composition points in the form of an
            n x 3 matrix or an m x n x 3 meshgrid, as long as the last
            dimension contains the three mole fractions.
        tol: Tolerance. Normalization is done if the sum of the mole
            fractions in x differs from 1 by more than the tolerance.

    Returns:
        An array of normalized mole fractions.
    """

    x = np.asarray(x)
    s = np.sum(x, axis=-1, keepdims=True)
    return np.where(np.abs(s - 1) <= tol, x, x / s)


def euclidean_distance(x, y):
    """
    Calculate Euclidean distance between two composition points x and y
        in composition space.

    Example:
        euclidean_distance([0.3, 0.40, 0.3], [0.2, 0.1, 0.7])

    Arguments:
        x, y: Arrays of mole fractions, with components ordered
            according to the ``axes`` specification used when
            constructing the ``TernarySystem``. All three mole fractions
            must be specified and must add up to 1. These arguments can
            also contain multiple composition points in the form of an
            n x 3 matrix or an m x n x 3 meshgrid, as long as the last
            dimension of each array contains the three mole fractions.

    Returns:
        A scalar denoting the Euclidean distance.
    """

    x = np.asarray(x)
    y = np.asarray(y)

    if x.shape[-1] != 3 or y.shape[-1] != 3:
        raise ValueError(
            'Input arrays must have exactly three mole fractions ' +
            'along their last dimension'
        )

    diff = x - y  # difference along last axis
    return np.sqrt(np.sum(diff * diff, axis=-1))


def out_of_triangle(t, y):
    """
    Determine if a 3-D composition point y is outside the mole fraction
        triangle defined by the points (0, 0, 1), (1, 0, 0) and (0, 1, 0).

    Note:
        This function is used in residue curve integration.
    """

    x1, x2, x3 = y
    # return < 0 if point is inside triangle, > 0 if outside
    return max(
        x1 - 1,
        0 - x1,
        x2 - 1,
        0 - x2,
        x3 - 1,
        0 - x3
    )


def out_of_triangle2(t, y):
    """
    Determine if a 2-D composition point y is outside the mole fraction
        triangle defined by the points (0, 0), (1, 0) and (0, 1).

    Note:
        This function is used in residue curve integration, especially
            when plotting separatrices.
    """

    x1, x2 = y
    # return < 0 if point is inside triangle, > 0 if outside
    return max(
        x1 - 1,
        0 - x1,
        x2 - 1,
        0 - x2
    )


def sign_tol(a, tol=1e-5):
    """
    Determines the sign of a scalar within a tolerance.
    """

    if a > tol:
        sign = 1
    elif a < -tol:
        sign = -1
    else:
        sign = 0
    return sign


def is_parallel(v1, v2, tol=1e-6):
    """
    Determine if two vectors are parallel.
    """

    # Test cross product component along perpendicular direction
    return abs(v1[0]*v2[1] - v1[1]*v2[0]) < tol


def indent_lines(text, tabs=1):
    """
    Add a specified number of tabs before each line of a multiline string.

    Note:
        This function is used in displaying VLE property, flash and
            distillation results.
    """

    prefix = "\t" * tabs
    return "\n".join(prefix + line for line in text.split("\n"))


def indent_array(array, tabs=1, **kwargs):
    """
    Convert an array to a string after applying any **kwargs, and pass to
        indent_lines, which displays the string with the specified number of
        tabs.

    Note:
        This function is used in displaying VLE property, flash and
            distillation results.
    """

    s = np.array2string(array, **kwargs)
    return indent_lines(s, tabs=tabs)
