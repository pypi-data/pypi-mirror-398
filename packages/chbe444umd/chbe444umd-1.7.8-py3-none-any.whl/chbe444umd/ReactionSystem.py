# Reaction Rate Field Plot: Reaction Systems
# Written for CHBE444: Design I, University of Maryland
# (C) Ganesh Sriram, 2025, originally written in MATLAB in 2017
# Licensed under GNU Public License 3.0
# Author contact info: gsriram@umd.edu

import numpy as np
import matplotlib.pyplot as plt


class ReactionSystem:
    """
    Container for components and reactions in a reactive system.

    Example:
        system = ReactionSystem(
            component_ids=('A', 'B', 'C'),
            component_names={'A': 'n-pentane',
                             'B': '2-methylbutane',
                             'C': '2,2-dimethylpropane'},
            axes={'A': 0, 'B': 1},
            h_lim=[0, 1],
            v_lim=[0, 1],
            reactions=('r1', 'r2'),
            stoich={'r1': {'A': -1, 'B': 1},
                    'r2': {'B': -1, 'C': 1}},
            kinetics={'r1': lambda C: 3 * C['A'],
                      'r2': lambda C: 2 * C['B']},
            inequality=lambda C: C['A'] + C['B'] - 1
        )

    Args:
        component_ids: Short ids (abbreviations or formulas) for components.
            Enclose component_ids in parentheses.
        component_names: Names or full names of components.
        axes: Dictionary indicating which component is represented on which
            axis. In the example above, component 'A' is represented on axis
            0 (x-axis) and component B is represented on axis 1 (y-axis).
        h_lim (or x_lim): Horizontal axis limits.
        v_lim (or y_lim): Vertical axis limits.
        reactions: Reaction ids. Enclose in parentheses.
        stoich: Reaction stoichiometry. Reactants get negative coefficients,
            and products get positive coefficients.
        kinetics: Reaction kinetics. Kinetics should be expressed in terms of
            the state variables such as concentrations, mole fractions,
            number of moles or partial pressures. Kinetics could be expressed
            by lambda functions as shown in the example above, or in long form
            as follows:

                k1 = 3  # s^-1
                k2 = 2  # s^-1
                def r1(C):
                    return k1 * C['A']
                def r2(C):
                    return k2 * C['B']
                kinetics = {'r1': r1,
                            'r2': r2}

        inequality: Inequality constraints that constrain the state variables.
            These constraints usually result from material balances, mole
            fraction or partial pressure summations, etc. The inequality
            constraints should be expressed as the left side of a vector that
            should be <= 0, for example:

                inequality=lambda C: [C['A'] + C['B'] - 1, C['A'] - 0.5]

            If the vector has only one element, as in the example above,
            express it as a scalar without the brackets:

                inequality = lambda C: C['A'] + C['B'] - 1

            If there are no inequality constraints, express as:

                inequality=lambda C: None

    Returns:
        A ReactionSystem object containing the specified components, reactions,
            stoichiometry, kinetics, and inequality constraints.
    """

    def __init__(self, component_ids, component_names, axes,
                 reactions, kinetics, stoich=None, stoichiometry=None,
                 inequality=lambda x: None,
                 h_lim=None, x_lim=None, v_lim=None, y_lim=None):
        self.component_ids = component_ids
        self.components = self.component_ids
        self.component_names = component_names
        self.names = self.component_names
        self.axes = axes

        if h_lim is None and x_lim is not None:
            h_lim = x_lim
        elif h_lim is not None and x_lim is not None:
            raise ValueError("Use either h_lim or x_lim, not both")
        if h_lim is None:
            h_lim = [0, 1]
        self.h_lim = h_lim

        if v_lim is None and y_lim is not None:
            v_lim = y_lim
        elif v_lim is not None and y_lim is not None:
            raise ValueError('Use either v_lim or y_lim, not both')
        if v_lim is None:
            v_lim = [0, 1]
        self.v_lim = v_lim

        if 0 not in list(self.axes.values()):
            raise KeyError('Axis #0 (x-axis) must be specified')
        if 1 not in list(self.axes.values()):
            raise KeyError('Axis #1 (y-axis) must be specified')

        self.reactions = reactions

        if stoich is not None and stoichiometry is None:
            self.stoich = stoich
        if stoich is None and stoichiometry is not None:
            self.stoich = stoichiometry
        if stoich is not None and stoichiometry is not None:
            raise ValueError('Specify stoich or stoichiometry, not both')
        if stoich is None and stoichiometry is None:
            raise ValueError('Stoichiometry must be specified')
        if not set(self.reactions).issubset(self.stoich):
            raise KeyError('Stoichiometry must be specified for all reactions')

        self.kinetics = kinetics

        if not set(self.reactions).issubset(self.kinetics):
            raise KeyError('Kinetics must be specified for all reactions')

        self.inequality = inequality

    def __repr__(self):
        rows_stoich = '\n'.join(f'        {rxn}: {s}'
                                for rxn, s in self.stoich.items())
        rows_kinetics = '\n'.join(f'        {rxn}: {k}'
                                  for rxn, k in self.kinetics.items())
        disp_text = (f'Reaction system:\n'
                     f'    component ids:\n\t{self.components}\n'
                     f'    component names:\n\t{self.component_names}\n'
                     f'    axes:\n\t{self.axes}\n'
                     f'    horizontal axis limits:\n\t{self.h_lim}\n'
                     f'    vertical axis limits:\n\t{self.v_lim}\n'
                     f'    reactions:\n\t{self.reactions}\n'
                     f'    stoichiometry:\n{rows_stoich}\n'
                     f'    kinetics:\n{rows_kinetics}\n'
                     f'    inequalities:\n\t{self.inequality}\n')
        return disp_text

    def rate(self, x):
        """
        Rates of formation of state variables at a particular value of the
            state vector x.

        Example:
            system.rate([0.4, 0.3])

        Args:
            x: State vector, which could represent concentration, mole
                fraction, number of moles or partial pressure.

        Returns:
            Array consisting of the rates of formation of the state variables.
        """

        x = np.asarray(x)
        if not np.issubdtype(x.dtype, np.number):
            raise TypeError(
                'x must be an array with integer or float elements'
                )
        if min(x.shape) < 2:
            x_size_error = 'x must be an array with two components'
            raise ValueError(x_size_error)

        X = {'A': 0, 'B': 0}  # X is the concentration vector (or equivalent)
        r_rxn = dict.fromkeys(self.reactions, 0)
        r_comp = dict.fromkeys(self.axes, 0)

        for i in self.components:
            if i in self.axes:
                X[i] = x[self.axes[i]]

        for j in self.reactions:
            r_rxn[j] += self.kinetics[j](X)

        for i in self.components:
            if i in self.axes:
                for j in self.reactions:
                    if i in self.stoich[j]:
                        r_comp[i] += self.stoich[j][i] * r_rxn[j]

        r_comp = np.array(list(r_comp.values()))
        return r_comp

    def inequality_status(self, x):
        """
        Status of inequality constraints at a particular value of the
            state vector x.

        Example:
            system.inequality_status([0.4, 0.3])

        Args:
            x: State vector, which could represent concentration, mole
                fraction, number of moles or partial pressure.

        Returns:
            Array consisting of the statuses of each inequality constraint.
                A value <= 0 indicates the state vector is feasible, whereas
                a value > 0 indicates it is infeasible as per the specified
                constraints.
        """

        x = np.asarray(x)
        if not np.issubdtype(x.dtype, np.number):
            raise TypeError(
                'x must be an array with integer or float elements'
                )
        if min(x.shape) < 2:
            x_size_error = 'x must be an array with two components'
            raise ValueError(x_size_error)

        X = {'A': 0, 'B': 0}  # X is the concentration vector (or equivalent)

        for i in self.components:
            if i in self.axes:
                X[i] = x[self.axes[i]]

        if self.inequality(X) is None:
            inequality_status = np.array(0)
        else:
            inequality_status = np.array(self.inequality(X))
        return inequality_status

    def plot_rate_field(self,
                        ax=None,
                        n_vec=51, n_vec_h=None, n_vec_v=None,
                        inequality_tol=1e-6,
                        arrow_scale=None, arrow_scale_h=None,
                        arrow_scale_v=None,
                        fsize=12, facecolor='white', font=12,
                        **kwargs):

        """
        Plot rate field in concentration space.

        Example:
            system.draw_rate_field(
                n_vec=51, n_vec_h=51, n_vec_v=51, inequality_tol=1e-6,
                arrow_scale=51, arrow_scale_h=51, arrow_scale_v=51,
                fsize=12, facecolor='white', font=12, **kwargs
            )

        Args:
            n_vec: Number of rate vectors along any dimension, defaults to 51.
            n_vec_h: Number of rate vectors along horizontal dimension
                (x-axis). Defaults to 51, can also be set by n_vec.
            n_vec_v: Number of rate vectors along vertical dimension
                (x-axis). Defaults to 51, can also be set by n_vec.
            inequality_tol: Tolerance for any inequalities, defaults to 1e-6.
            arrow_scale: scale of arrow along any dimension, defaults to n_vec.
            arrow_scale_h: Scale of arrow along horizontal dimension (x-axis).
                Defaults to n_vec_x.
            arrow_scale_v: Scale of arrow along vertical dimension (y-axis).
                Defaults to n_vec_y.
            fsize: Figure size, defaults to 12.
            facecolor: Figure background color, defaults to ``white``.
            font: Base font used for axis labels, etc. Defaults to 12.
            **kwargs: Additional keyword arguments passed to
                matplotlib.pyplot.quiver. Common options include ``color``
                and ``linewidth``.

        Returns:
            Figure: Figure object containing the rate field plot.
            Axes: Associated axes object.
        """

        if ax is None:
            fig, ax = plt.subplots(figsize=(fsize, fsize), facecolor=facecolor)
        else:
            fig = ax.figure
        h_lim = self.h_lim
        v_lim = self.v_lim
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(1)
        ax.set_xlim(h_lim)
        ax.set_ylim(v_lim)
        ax.grid(True)

        for i in self.components:
            if i in self.axes:
                if self.axes[i] == 0:
                    ax.set_xlabel(self.names[i], fontsize=font)
                if self.axes[i] == 1:
                    ax.set_ylabel(self.names[i], fontsize=font)

        if n_vec_h is None:
            n_vec_h = n_vec
            arrow_scale_h = n_vec_h
        if n_vec_v is None:
            n_vec_v = n_vec
            arrow_scale_v = n_vec_v

        if arrow_scale is None:
            arrow_scale = n_vec
        else:
            if arrow_scale_h is None:
                arrow_scale_h = arrow_scale
            if arrow_scale_v is None:
                arrow_scale_v = arrow_scale

        # Compute rate vectors
        X = np.linspace(h_lim[0], h_lim[1], n_vec_h)
        Y = np.linspace(v_lim[0], v_lim[1], n_vec_v)

        xx, yy = np.meshgrid(X, Y)
        inequalities = self.inequality_status([xx, yy])
        n_inequalities = np.size(self.inequality_status([0, 0]))

        XY = np.array([xx.ravel(), yy.ravel()])
        rates = self.rate(XY)
        uu = rates[0].reshape(xx.shape)
        vv = rates[1].reshape(yy.shape)

        if n_inequalities == 1:
            if np.any(inequalities != 0):
                uu = np.where(inequalities > inequality_tol, np.nan, uu)
                vv = np.where(inequalities > inequality_tol, np.nan, vv)
        else:
            mask = np.any(inequalities > inequality_tol, axis=0)
            uu = np.where(mask, np.nan, uu)
            vv = np.where(mask, np.nan, vv)

        # Normalize
        mag = np.hypot(uu, vv)
        un, vn = uu, vv
        with np.errstate(invalid='ignore'):
            un = np.where(np.isnan(un), np.nan,
                          np.where(mag > 0,
                                   np.divide(uu, mag), np.nan))
            vn = np.where(np.isnan(vn), np.nan,
                          np.where(mag > 0,
                                   np.divide(vv, mag), np.nan))

        quiver = ax.quiver(X, Y, un, vn, color='#888888', angles='xy',
                           scale=arrow_scale, alpha=0.5, **kwargs)
        # angles='xy' plots from x, y to x+u, y+v

        return fig, ax, quiver

    draw_rate_field = plot_rate_field
    simulate_rate_field = plot_rate_field


ReactiveSystem = ReactionSystem
