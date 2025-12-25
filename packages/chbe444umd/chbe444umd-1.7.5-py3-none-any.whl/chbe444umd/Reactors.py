# Reaction Rate Field Plot: Reactors
# Written for CHBE444: Design I, University of Maryland
# (C) Ganesh Sriram, 2025, originally written in MATLAB in 2017
# Licensed under GNU Public License 3.0
# Author contact info: gsriram@umd.edu

import numpy as np
import scipy as sci
import warnings


class ReactorRegistry:
    def __init__(self):
        self._store = {}

    def add(self, reactor):
        name = reactor.name
        self._store[name] = reactor
        setattr(self, name, reactor)

    def __getitem__(self, key):
        return self._store[key]

    def __iter__(self):
        return iter(self._store)  # iterates keys

    def __len__(self):
        return len(self._store)

    def items(self):
        return self._store.items()

    def keys(self):
        return self._store.keys()

    def values(self):
        return self._store.values()

    def __repr__(self):
        if not self._store:
            return "Reactors()"
        lines = ["Reactors("]
        for name, obj in self._store.items():
            lines.append(f"{name}:\n{obj!r}")
        lines.append(")")
        return "\n".join(lines)


reactors = ReactorRegistry()


class Reactor:
    """
    Container for reactor interacting with a reactive system.

    Example:
        pfr1 = Reactor(flow_type='plug', feed=[1, 0], time=5, name='PFR1')

    Args:
        flow_type: Keyword indicating type of flow in the reactor.
            PFR options:  'pfr', 'plug', 'plug flow', 'tube'.
            CSTR options: 'cstr', 'mixed', 'tank', 'stirred tank',
            'continuously stirred tank'.
        feed: Feed coordinates, specified in the same sequence as axis
            components.
        time: Tau limit. The reactor is simulated from tau = 0 up to this time.
            Defaults to 10.
        name: Optional name for the reactor, e.g., 'PFR from fresh feed'.

    Returns:
        Reactor object containing the specified reactor, flow_type, feed and
            tau limit. After the reactor is simulated, the object also contains
            a curve object (Line2D or QuadContourSet), xy coordinates of the
            reactor curve and slopes of tangents along the reactor curve.
    """

    PFR_KEYWORDS = ('pfr', 'plug', 'plug flow', 'tube')
    CSTR_KEYWORDS = ('cstr', 'mixed', 'stirred tank', 'tank',
                     'continuously stirred tank')

    def __init__(self, flow_type, feed, time=10, name='',
                 curve=None, tau=None, x=None, y=None, xy=None,
                 slope_x=None, slope_y=None):
        self.flow_type = flow_type
        self.feed = feed
        self.time = time
        self.name = name
        self.curve = []
        self.tau = np.array([])
        self.x = np.array([])
        self.y = np.array([])
        self.xy = np.array([])
        self.slope_x = np.array([])
        self.slope_y = np.array([])
        self.segment = np.array([])
        self.simulated = False

        if self.flow_type not in self.PFR_KEYWORDS + self.CSTR_KEYWORDS:
            raise ValueError('flow_type does not match PFR or CSTR keywords')

        self.feed = np.asarray(self.feed)
        if not np.issubdtype(self.feed.dtype, np.number):
            feed_type_error = (
                'feed must be an array with integer or float elements'
            )
            raise TypeError(feed_type_error)
        if np.size(self.feed) < 2:
            feed_value_error = 'feed must be an array with two components'
            raise ValueError(feed_value_error)

        if self.time < 0:
            raise ValueError('Reactor time must be nonnegative')

        if reactors is not None:
            reactors.add(self)

    def __repr__(self):
        if np.array(self.tau).size == 0:
            disp_text = (f'Reactor:\n'
                         f'    name:\t{self.name}\n'
                         f'    flow type:\t{self.flow_type}\n'
                         f'    feed:\t{self.feed}')
        else:
            n_tau = np.array(self.tau).size
            disp_text = (f'Reactor:\n'
                         f'    name:\t{self.name}\n'
                         f'    flow type:\t{self.flow_type}\n'
                         f'    feed:\t{self.feed}\n'
                         f'    time:\t{self.time}\n'
                         f'    curve:\tarray of curve objects\n'
                         f'    tau:\t{n_tau}×1 numpy array of tau values\n'
                         f'    x:\t\t{n_tau}×1 numpy array of x values\n'
                         f'    y:\t\t{n_tau}×1 numpy array of y values\n'
                         f'    xy:\t\t{n_tau}×2 numpy array of [x, y] values\n'
                         f'    slope_i:\t{n_tau}×1 numpy arrays of slope data')
        return disp_text

    def simulate(self, system, ax, time_limit=0,
                 n_points=1000, show_feed=False,
                 inequality_tol=1e-6, **kwargs):
        """
        Simulate and plot a reactor.

        Example:
            pfr1.simulate(sysABC, ax, time_limit=20, n_points=1000,
                          show_feed=True)

        Args:
            system: Reaction system operating in the reactor.
            ax: Axes on which the reactor curve is to be plotted.
            time_limit: Tau limit. The reactor is simulated from tau = 0 up to
                this time. Overrides the ``time`` argument of the reactor.
            n_points: Number of integration or calculation points. For PFRs,
                this value equals the exact number of points in the curve.
                For CSTRs, it is the number of points along each dimension for
                which the contour is evaluated. Thus, the exact number of
                points in the CSTR curve will be proportional to, but will
                differ from n_points.
            show_feed: True/False value indicating whether feed should be
                displayed as a point.
            inequality_tol: Tolerance for any inequalities, defaults to 1e-6.
            **kwargs: Additional keyword arguments passed to matplotlib.pyplot.
                Common options include ``linewidth`` for the reactor curve and
                ``marker`` for the feed point(s). Note that PFR curves and
                feeds are always plotted in red (#ff0000), whereas CSTR curves
                and feeds are always plotted in blue (#0000ff).

        Returns:
            Axes passed to the function and an updated reactor object
                containing a curve object (Line2D or QuadContourSet), xy
                coordinates of the reactor curve and slopes of tangents along
                the reactor curve.
        """

        if time_limit < 0:
            raise ValueError('time_limit must be nonnegative')

        if n_points < 0:
            raise ValueError('n_points must be nonnegative')

        if not isinstance(n_points, int):
            raise TypeError('n_points must be an integer')

        if not isinstance(show_feed, bool):
            raise TypeError('show_feed must be Boolean (True or False)')

        # Parse kwargs
        if self.flow_type.lower() in self.PFR_KEYWORDS:
            forced_line_kwargs = {'linestyle': '-', 'color': 'r'}
        elif self.flow_type.lower() in self.CSTR_KEYWORDS:
            forced_line_kwargs = {'linestyle': '-', 'color': 'b'}

        conflict_keys = {'linestyle', 'ls',
                         'color', 'c'}  # may conflict with user's keys
        for k in conflict_keys:  # remove conflicted keys from kwargs
            kwargs.pop(k, None)

        common_keys = {'alpha'}  # shared between point and line

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
        line_kwargs = {**common_kwargs, **forced_line_kwargs, **line_kwargs}

        def ratet(t, x):
            return system.rate(x)

        xF = self.feed
        if np.size(self.feed, 0) != 2:
            raise ValueError('The feed should have exactly 2 coordinates')
        if show_feed:
            ax.plot(xF[0], xF[1], **point_kwargs)

        if self.flow_type.lower() in self.PFR_KEYWORDS:
            if time_limit == 0:
                int_t = self.time
                time_limit = self.time
            else:
                int_t = time_limit

            with np.errstate(all='ignore'):
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', RuntimeWarning)
                    res = sci.integrate.solve_ivp(ratet, [0, int_t], xF,
                                                  method='DOP853',
                                                  dense_output=True)
                    t_vals = np.linspace(0, int_t, n_points)
                    x_vals = res.sol(t_vals)[0]
                    x_uniform = np.linspace(x_vals.min(),
                                            x_vals.max(),
                                            n_points)
                    self.x = x_uniform

                    t_from_x = sci.interpolate.interp1d(
                        x_vals, t_vals, fill_value="extrapolate"
                    )
                    t_uniform = t_from_x(x_uniform)
                    self.tau = t_uniform

                    y_uniform = res.sol(t_uniform)
                    self.y = y_uniform[1, :]
                    self.xy = np.column_stack((self.x, self.y))
                    self.curve = ax.plot(self.x, self.y, **line_kwargs)

                    rates_pfr = np.array([system.rate(p) for p in self.xy])
                    self.slope_x = rates_pfr[:, 0]
                    self.slope_y = rates_pfr[:, 1]
                    self.segment = np.zeros_like(self.x)  # only segment 0
                    self.simulated = True

        if self.flow_type.lower() in self.CSTR_KEYWORDS:
            if time_limit == 0:
                calc_t = self.time
                time_limit = self.time
            else:
                calc_t = time_limit

            h_lim = system.h_lim
            v_lim = system.v_lim
            xx = np.linspace(h_lim[0], h_lim[1], n_points)
            yy = np.linspace(v_lim[0], v_lim[1], n_points)
            X, Y = np.meshgrid(xx, yy)

            def cstrpt(x, y):
                r = system.rate([x, y])
                with np.errstate(all='ignore'):
                    f = y - xF[1] - r[1] / r[0] * (x - xF[0])
                    return f

            self.curve = ax.contour(X, Y, cstrpt(X, Y),
                                    levels=[0], linewidths=0)

            xs, ys, xys = [], [], []
            dxs, dys, segment = [], [], []
            seg_count = 0  # global segment counter

            for level in self.curve.allsegs:
                for seg in level:
                    if seg.size == 0:
                        continue
                    seg_count += 1  # increment counter

                    xy = seg
                    xseg = seg[:, 0]
                    yseg = seg[:, 1]
                    dx = np.gradient(xseg)
                    dy = np.gradient(yseg)

                    xys.append(xy)
                    xs.append(xseg)
                    ys.append(yseg)
                    dxs.append(dx)
                    dys.append(dy)
                    segment.append(seg_count * np.ones_like(xseg))

                    # Add NaN breaks between segments
                    xys.append(np.array([[np.nan, np.nan]]))
                    xs.append(np.array([np.nan]))
                    ys.append(np.array([np.nan]))
                    dxs.append(np.array([np.nan]))
                    dys.append(np.array([np.nan]))
                    segment.append(np.array([seg_count + 0.5]))  # in between

            xy = np.transpose(np.vstack(xys)) if xys else np.empty((2, 0))
            self.x = np.concatenate(xs) if xs else np.array([])
            self.y = np.concatenate(ys) if ys else np.array([])
            self.slope_x = np.concatenate(dxs) if dxs else np.array([])
            self.slope_y = np.concatenate(dys) if dys else np.array([])
            self.segment = np.concatenate(segment) if segment else np.array([])

            with np.errstate(invalid='ignore', divide='ignore'):
                self.tau = np.array(
                    (xy - np.array(xF)[:, None]) /
                    system.rate([xy[0, :], xy[1, :]])
                )[0, :]
                # tau is calculated in duplicate from both axes, so discard one

            # Eliminate points at which tau < 0 or tau > specified time limit
            mask = (self.tau < 0) | (self.tau > calc_t)
            self.x[mask] = np.nan
            self.y[mask] = np.nan
            self.slope_x[mask] = np.nan
            self.slope_y[mask] = np.nan
            self.tau[mask] = np.nan

            # Eliminate points at which CSTR design equation is not satisfied
            # This step should remove any contour artifacts
            tol = 1e-2
            r = system.rate([self.x, self.y])
            dy = np.abs(self.y - xF[1] - self.tau * r[1])
            dx = np.abs(self.x - xF[0] - self.tau * r[0])
            self.x = np.where(dy + dx > tol, np.nan, self.x)
            self.y = np.where(dy + dx > tol, np.nan, self.y)
            self.tau = np.where(dy + dx > tol, np.nan, self.tau)
            self.slope_x = np.where(dx > tol, np.nan, self.slope_x)
            self.slope_y = np.where(dx > tol, np.nan, self.slope_y)

            # Eliminate all nans except those between segments
            # In between segments, self.segment will be 0.5, 1.5, etc.
            mask = ~(
                (np.isnan(self.x) |
                 np.isnan(self.y) |
                 np.isnan(self.tau)) &
                (np.mod(self.segment, 1) == 0)
            )
            self.x = self.x[mask]
            self.y = self.y[mask]
            self.tau = self.tau[mask]
            self.slope_x = self.slope_x[mask]
            self.slope_y = self.slope_y[mask]
            self.segment = self.segment[mask]

            self.xy = np.column_stack((self.x, self.y))
            self.curve = ax.plot(self.x, self.y, **line_kwargs)

            self.simulated = True
        return ax

    def plot_point(self, ax, x=[], y=[], tau=[],
                   annotate=True, annotation='all', **kwargs):
        """
        Locate and plot a point corresponding to a specified value of x, y
            and/or tau on a reactor curve.

        Notes:
            More than one of x, y or tau could be specified.
            If an exact match is not found, the nearest point on the curve
                will be found.
            It may be useful to duplicate the figure first, especially when
                trying out points that are not yet final:

                fig1, ax1 = duplicate_figure(fig)

        Examples:
            pfr1.plot_point(ax1, x=0.6)
            ax1, point, text = pfr1.plot_point(ax1, x=0.6,
                                               ha='right',
                                               va='bottom')
            pfr1.plot_point(ax1, y=0.2, markersize=6, annotate=False)
            cstr1.plot_point(ax1, tau=0.5, ha='left', va='top')
            fig1  # display figure after points are plotted

        Args:
            ax: Axes on which the point should be plotted.
            x, y, tau: Scalars specifying the point. At least one
                must be provided. See notes above.
            annotate (verb): Boolean parameter indicating whether the point
                should be annotated with values of x, y and/or tau.
            annotation (noun): String indicating the type of annotation for
                the point. Options are 'tau', 'x', 'y' 'xy', 'all'. Default
                is 'all'. Not  case-sensitive.
            **kwargs: Additional keyword arguments passed to
                matplotlib.pyplot.plot and  matplotlib.pyplot.text.
                Common options include ``marker`` and ``markersize`` for
                the point and ``fontsize`` (``size``), ``fontstyle``
                (``style``), ``fontweight`` (``weight``),
                ``horizontalalignment`` (``ha``) and
                ``verticalalignment`` (``va``) for the text. Points on PFRs
                are always plotted in red (#ff0000), whereas points on CSTRs
                are always plotted in blue (#0000ff). Points are always
                annotated in black (#000000). Users may change the colors
                and markers by calling:
                    ax1, point, text = reactor.plot_point(...)
                and editing the attributes:
                    point.marker = '+'
                    text.color = 'b'

        Returns:
            Axes: Axes passed to the function.
            Point: Line2D object containing the plotted point.
            Text: If annotate is set to True, text object containing the
                annotation.
        """
        if not self.simulated:
            print('Reactor must be simulated before plotting point(s)')
            return
        else:
            if (
                not np.isscalar(x) and
                not np.isscalar(y) and
                not np.isscalar(tau)
            ):
                raise ValueError(
                    'At least one of x, y or tau should be provided'
                )

            # Parse kwargs
            if self.flow_type in self.PFR_KEYWORDS:
                forced_kwargs = {'color': 'r'}
            elif self.flow_type in self.CSTR_KEYWORDS:
                forced_kwargs = {'color': 'b'}
            forced_point_kwargs = {'marker': 'o'}
            forced_text_kwargs = {'color': 'k'}

            for k in ('color', 'c'):  # conflicted kwarg
                kwargs.pop(k, None)

            common_keys = {'alpha'}

            point_keys = {
                'marker',
                'markersize', 'ms',
                'markerfacecolor', 'mfc',
                'markeredgecolor', 'mec',
                'markeredgewidth', 'mew',
                'fillstyle',
            }

            text_keys = {
                'fontsize', 'fontweight', 'fontstyle',
                'ha', 'va', 'rotation',
                'bbox',
                'family', 'name',
            }

            common_kwargs, point_kwargs, text_kwargs = {}, {}, {}

            for key, value in kwargs.items():
                if key in common_keys:
                    common_kwargs[key] = value
                elif key in point_keys:
                    point_kwargs[key] = value
                elif key in text_keys:
                    text_kwargs[key] = value
                else:
                    pass

            point_kwargs = {**forced_kwargs,
                            **forced_point_kwargs,
                            **common_kwargs,
                            **point_kwargs}
            text_kwargs = {**forced_kwargs,
                           **forced_text_kwargs,
                           **common_kwargs,
                           **text_kwargs}

            mask = (
                ~np.isnan(self.x)
                & ~np.isnan(self.y)
                & ~np.isnan(self.tau))

            xx = self.x[mask]
            yy = self.y[mask]
            tt = self.tau[mask]

            ssr = np.zeros(np.size(xx))
            if np.isscalar(x):
                ssr += (xx - x)**2
            if np.isscalar(y):
                ssr += (yy - y)**2
            if np.isscalar(tau):
                ssr += (tt - tau)**2
            idx = ssr.argmin()

            x = xx[idx]
            y = yy[idx]
            tau = tt[idx]

            label_tau = f' $\\tau=$ {np.round(tau, 3)}'
            label_xy = f'({np.round(x, 3)}, {np.round(y, 3)})'
            label_x = f'x = {np.round(x, 3)}'
            label_y = f'y = {np.round(y, 3)}'
            label_all = label_tau + ', ' + label_xy

            if annotation.lower() == 'tau':
                label = label_tau
            elif annotation.lower() == 'xy':
                label = label_xy
            elif annotation.lower() == 'x':
                label = label_x
            elif annotation.lower() == 'y':
                label = label_y
            elif annotation.lower() == 'all':
                label = label_all
            else:
                raise ValueError(
                    f"Point annotation should be 'tau', 'xy, 'x', 'y'"
                    f"or 'all' (case-insensitive), got '{annotation}'"
                )

            if self.flow_type in self.PFR_KEYWORDS:
                point = ax.plot(x, y, **point_kwargs)
                if annotate:
                    text = ax.text(x, y, label, **text_kwargs)
                    return ax, point, text
                else:
                    return ax, point
            elif self.flow_type in self.CSTR_KEYWORDS:
                point = ax.plot(x, y, **point_kwargs)
                if annotate:
                    text = ax.text(x, y, label, **text_kwargs)
                    return ax, point, text
                else:
                    return ax, point

    def plot_tangent(self, ax, from_point, near_point=[],
                     distance_x=1, distance_h=None,
                     distance_y=1, distance_v=None,
                     tol=1e-2, **kwargs):
        """
        Plot a tangent to a reactor curve from a specified point.

        Notes:
            The tangent could optionally be constrained to touch the curve
                within a specified horizontal or vertical distance from
                another point.
            It may be useful to duplicate the figure first, especially when
                trying out tangents that are not yet final:

                fig1, ax1 = duplicate_figure(fig)

        Example:
            reactor.plot_tangent(ax,
                                 from_point=[1, 0.2],
                                 near_point=[0.4, 0.3],
                                 distance_v=0.05)

        Args:
            ax: Axes on which the tangent should be plotted
            from_point: Point from where tangent should be plotted.
            near_point: Point to which tangent's point of contact should be
                near. Defaults to reactor feed.
            distance_h or distance_x: Horizontal distance from near_point
                to the point of contact. Defaults to 1.
            distance_v or distance_y: Vertical distance from near_point
                to the point of contact. Defaults to 1.
            tol: Tolerance for tangent. Defaults to 1e-2.
            **kwargs: Additional keyword arguments passed to
                matplotlib.pyplot.plot. Common options include ``color``
                (``c``), ``linewidth`` (``lw``) and ``linestyle`` (``ls``).

        Returns:
            Axes: Axes passed to the function.
            Line: If a tangent was found, Line2D object containing the tangent.
        """

        if not self.simulated:
            print('Reactor must be simulated before plotting tangent')
            return
        else:
            if distance_x is None and distance_h is not None:
                distance_x = distance_h
            elif distance_h is not None and distance_x is not None:
                raise ValueError(
                    'Use either distance_h or distance_x, not both'
                )
            if distance_x is None:
                distance_x = 1

            if distance_y is None and distance_v is not None:
                distance_y = distance_v
            elif distance_v is not None and distance_y is not None:
                raise ValueError(
                    "Use either distance_v or distance_y, not both"
                )
            if distance_y is None:
                distance_y = 1

            from_point = np.array(from_point)
            if near_point:
                near_point = np.array(near_point)
            else:
                near_point = self.feed  # defaults to reactor feed

            #  Filter for distance_x, then for distance_y
            d_x = np.abs(self.x - near_point[0])
            xx = np.where(d_x < distance_x, self.x, np.nan)
            yy = np.where(d_x < distance_x, self.y, np.nan)
            sl_x = np.where(d_x < distance_x, self.slope_x, np.nan)
            sl_y = np.where(d_x < distance_x, self.slope_y, np.nan)

            d_y = np.abs(self.y - near_point[1])
            xx = np.where(d_y < distance_y, xx, np.nan)
            yy = np.where(d_y < distance_y, yy, np.nan)
            sl_x = np.where(d_y < distance_y, sl_x, np.nan)
            sl_y = np.where(d_y < distance_y, sl_y, np.nan)

            angle_point_to_reactor = np.atan2(yy - from_point[1],
                                              xx - from_point[0])
            angle_tangent = np.atan2(sl_y, sl_x)
            delta = angle_point_to_reactor - angle_tangent

            if delta.any():
                sin_delta = np.abs(np.sin(delta))
                xx = xx[~np.isnan(sin_delta)]
                yy = yy[~np.isnan(sin_delta)]
                sin_delta = sin_delta[~np.isnan(sin_delta)]

                idx = sin_delta.argmin()
                if sin_delta[idx] < tol:
                    (line,) = ax.plot((from_point[0], xx[idx]),
                                      (from_point[1], yy[idx]), **kwargs)
                    return ax, line
                else:
                    print(
                        f'Tangent to {self.name} not found from '
                        f'{from_point} within tolerance'
                        )
                    return ax, None
            else:
                print(f'Tangent to {self.name} not found from '
                      f'{from_point} within tolerance'
                      )
                return ax, None


def common_tangent(ax, reactor1, reactor2,
                   near_point=[], distance_x=None, distance_h=None,
                   distance_y=None, distance_v=None, tol=1e-2,
                   **kwargs):
    """
    Plots a common tangent to a pair of reactors, if one exists.

    Example:
        common_tangent(ax, reactor1, reactor2, near_point=[0.4, 0.3],
        distance_h=0.3, tol=1e-2, **kwargs)

    Args:
        ax: Axes on which the tangent is to be plotted.
        reactor1, reactor2: Reactors, which should already be simulated.
        near_point: Point to which tangent's point of contact should be
            near. Defaults to reactor feed.
        distance_h or distance_x: Horizontal distance from near_point
            to the point of contact. Defaults to 1.
        distance_v or distance_y: Vertical distance from near_point
            to the point of contact. Defaults to 1.
        tol: Tolerance for tangent. Defaults to 1e-2.
        **kwargs: Additional keyword arguments passed to
            matplotlib.pyplot.plot. Common options include ``color``
            (``c``), ``linewidth`` (``lw``) and ``linestyle`` (``ls``).

    Returns:
        Axes: Axes passed to the function.
        Line: If a common tangent was found, Line2D object containing the
            tangent.
    """
    if (not reactor1.simulated) or (not reactor2.simulated):
        print('Both reactors must be simulated before plotting common tangent')
        return
    else:
        if distance_x is None and distance_h is not None:
            distance_x = distance_h
        elif distance_h is not None and distance_x is not None:
            raise ValueError("Use either distance_h or distance_x, not both")
        if distance_x is None:
            distance_x = 1

        if distance_y is None and distance_v is not None:
            distance_y = distance_v
        elif distance_v is not None and distance_y is not None:
            raise ValueError("Use either distance_v or distance_y, not both")
        if distance_y is None:
            distance_y = 1

        if near_point:
            near_point = np.array(near_point)
        else:
            near_point = reactor1.feed  # defaults to first reactor's feed

        # Remove feed points
        x1 = reactor1.x[1:]
        y1 = reactor1.y[1:]
        m1 = reactor1.slope_y[1:] / reactor1.slope_x[1:]
        x2 = reactor2.x[1:]
        y2 = reactor2.y[1:]
        m2 = reactor2.slope_y[1:] / reactor2.slope_x[1:]

        #  Filter for distance_x, then for distance_y
        d_x = np.abs(x1 - near_point[0])
        x1 = np.where(d_x < distance_x, x1, np.nan)
        y1 = np.where(d_x < distance_x, y1, np.nan)
        m1 = np.where(d_x < distance_x, m1, np.nan)
        d_y = np.abs(y1 - near_point[1])
        x1 = np.where(d_y < distance_y, x1, np.nan)
        y1 = np.where(d_y < distance_y, y1, np.nan)
        m1 = np.where(d_y < distance_y, m1, np.nan)

        d_x = np.abs(x2 - near_point[0])
        x2 = np.where(d_x < distance_x, x2, np.nan)
        y2 = np.where(d_x < distance_x, y2, np.nan)
        m2 = np.where(d_x < distance_x, m2, np.nan)
        d_y = np.abs(y2 - near_point[1])
        x2 = np.where(d_y < distance_y, x2, np.nan)
        y2 = np.where(d_y < distance_y, y2, np.nan)
        m2 = np.where(d_y < distance_y, m2, np.nan)

        x1 = x1[~np.isnan(x1)]
        y1 = y1[~np.isnan(y1)]
        m1 = m1[~np.isnan(m1)]
        x2 = x2[~np.isnan(x2)]
        y2 = y2[~np.isnan(y2)]
        m2 = m2[~np.isnan(m2)]

        X1 = x1[:, None]
        Y1 = y1[:, None]
        M1 = m1[:, None]
        X2 = x2[None, :]
        Y2 = y2[None, :]
        M2 = m2[None, :]

        dx = X2 - X1
        dy = Y2 - Y1

        # Avoid division by zero
        invalid = np.isclose(dx, 0.0)
        slope_line = np.empty_like(dx)
        slope_line[~invalid] = dy[~invalid] / dx[~invalid]
        slope_line[invalid] = np.nan

        # Mismatch between line slope and each curve's local slope
        err1 = M1 - slope_line  # curve 1 slope vs line slope
        err2 = M2 - slope_line  # curve 2 slope vs line slope

        # Total squared error
        err = err1**2 + err2**2
        err[invalid] = np.inf

        # Best indices
        flat_idx = np.argmin(err)
        i_best, j_best = np.unravel_index(flat_idx, err.shape)

        if tol < np.inf and err[i_best, j_best] > tol:
            print("No common tangent found within tolerance")
            return
        else:
            line = ax.plot([x1[i_best], x2[j_best]],
                           [y1[i_best], y2[j_best]], **kwargs)
            return ax, line


def convexify(ax, boundaries, **kwargs):
    """ Plots the convex hull of a given set of curves (boundaries), which
    could be reactors or line objects.

    Example:
        convexify(ax, boundaries, alpha=0.2, **kwargs)

    Args:
        ax: axes of the figure on which the AR is to be plotted
        boundaries: list containing reactor objects and line objects

    Returns:
        Axes: Axes passed to the function.
        Hull: ConvexHull containing mathematical description of the hull.
    """

    reactors_simulated = True
    for boundary in boundaries:
        if isinstance(boundary, Reactor):
            if not boundary.simulated:
                reactors_simulated = False
    if reactors_simulated is False:
        print('All reactors must be simulated before convexifying')
        return
    else:
        # Parse kwargs
        common_keys = {'color', 'c', 'alpha'}

        line_keys = {
            'linestyle', 'ls',
            'linewidth', 'lw',
            'drawstyle',
            'dash_capstyle',
            'dash_joinstyle',
            'solid_capstyle',
            'solid_joinstyle',
            'antialiased',
            'marker',
            'markersize', 'ms',
            'markerfacecolor', 'mfc',
            'markeredgecolor', 'mec',
            'markeredgewidth', 'mew',
            'fillstyle',
        }

        fill_keys = {
            'edgecolor',
            'facecolor',
            'linewidth',
            'linestyle',
            'hatch',
            'antialiased',
            'rasterized',
            'path_effects',
        }

        common_kwargs, line_kwargs, fill_kwargs = {}, {}, {}

        for key, value in kwargs.items():
            if key in common_keys:
                common_kwargs[key] = value
            elif key in line_keys:
                line_kwargs[key] = value
            elif key in fill_keys:
                fill_kwargs[key] = value
            else:
                pass

        line_kwargs = {**common_kwargs, **line_kwargs}
        fill_kwargs = {**common_kwargs, **fill_kwargs}

        pts_list = []
        for boundary in boundaries:
            if isinstance(boundary, Reactor):
                xy = boundary.xy
            else:
                xy = np.column_stack((boundary.get_xdata(),
                                      boundary.get_ydata()))
            pts_list.append(xy)
        pts = np.vstack(pts_list)
        pts = pts[~np.isnan(pts).any(axis=1)]  # remove NaNs and duplicates
        pts = np.unique(pts, axis=0)

        hull = sci.spatial.ConvexHull(pts)
        hull_xy = pts[hull.vertices]
        ax.plot(hull_xy[:, 0], hull_xy[:, 1], **line_kwargs)  # hull boundary
        ax.fill(hull_xy[:, 0], hull_xy[:, 1], **fill_kwargs)  # hull
        return ax, hull
