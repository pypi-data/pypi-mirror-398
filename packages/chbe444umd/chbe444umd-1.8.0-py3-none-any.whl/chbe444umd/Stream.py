# Heat Integration: Stream Definition and Pinch Analysis by TI Method
# Written for CHBE444: Design I, University of Maryland
# (C) Ganesh Sriram, 2025, originally written in MATLAB in 2017
# Licensed under GNU Public License 3.0
# Author contact info: gsriram@umd.edu

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import Literal

StreamKind = Literal['hot', 'cold']


@dataclass
class Stream:
    """
    Container for a stream in a heat integration problem.

    Examples:
        H1 = Stream(name='H1', kind='hot', T_source=180, T_target=60, H=360)
        C1 = Stream(name='C1', kind='cold', T_source=20, T_target=135, H=230)

    Args:
        name: A descriptive name for the stream.
        kind: Kind (type) of stream. Options are ``hot`` and ``cold``.
        T_source: Source temperature (°C).
        T_target: Target temperature (°C).
        H: Enthalpy requirement (kW). Either one of ``H`` or ``C`` must be
            specified.
        C: Extensive heat capacity (kW/°C). Either one of ``H`` or ``C``
            must be specified.
        h: Individual film heat transfer coefficient (J/(s m^2 °C)). Defaults
            to 1.0 J/(s m^2 °C).

    Returns:
        A Stream object containing the specified properties of the stream.
    """

    name: str
    kind: StreamKind
    T_source: float
    T_target: float
    # Enthalpy requirement
    H: float | None = field(
        default=None,
        repr=lambda v: f'{float(v):.1f}' if v is not None else 'None'
    )
    # Extensive heat capacity
    C: float | None = field(
        default=None,
        repr=lambda v: f'{float(v):.2f}' if v is not None else 'None'
    )
    # Film heat transfer coefficient
    h: float | None = field(
        default=None,
        repr=lambda v: f'{float(v):.2f}' if v is not None else 'None'
    )

    def __post_init__(self):
        if self.C is None and self.H is None:
            raise ValueError(
                'Either extensive heat capacity (C) or enthalpy '
                'requirement (H) must be specified for a stream'
            )
        elif self.C is None:
            self.C = float(self.H / np.abs(self.T_source - self.T_target))
        elif self.H is None:
            self.H = float(self.C * np.abs(self.T_source - self.T_target))
        else:
            self.C = float(self.H / np.abs(self.T_source - self.T_target))
            print(
                "Both H and C are specified; overriding C with calculated "
                f"value (= {self.C})"
            )
            pass

        if self.h is None:
            self.h = 1


def pinch_analysis(streams, DT_min=10, disp=True, GCC=False,
                   fsize=6, font=12, facecolor='white', decimals=2):
    """
    Perform pinch analysis by temperature interval (TI) method.

    Examples:
        perform_pinch_analysis([H1, H2, C1, C2], DT_min=10,
                               disp=False, GCC=False)

        TI, fig, ax = perform_pinch_analysis([H1, H2, C1, C2], DT_min=20,
                                             disp=True, GCC=True)
        display(TI)
        fig

    Args:
        streams: A list of previously created Stream objects.
        DT_min: Minimum approach temperature. Defaults to 10 °C.
        disp: True/False value that determines whether stream data will be
            displayed before performing pinch analysis. Defaults to True.
        GCC: True/False value that determines whether GCC will be drawn.
            Defaults to False.
        fsize: Figure size. Defaults to 6.
        font: Base font. Defaults to 12.
        facecolor: Background color of plot. Defaults to ``white``.
        decimals: Number of decimals used for rounding the columns containing
            stream heat capacities. Other columns are not rounded. Defaults
            to 2.

    Returns:
        A pandas DataFrame containing the results of the pinch analysis
            and if requested, a figure containing the GCC.
    """

    if disp is True:
        df = pd.DataFrame(data={
            'Name': [stream.name for stream in streams],
            'Type': [stream.kind for stream in streams],
            'T_source (°C)': [stream.T_source for stream in streams],
            'T_target (°C)': [stream.T_target for stream in streams],
            'H (kW)': [stream.H for stream in streams],
            'C (kW/°C)': [stream.C for stream in streams]
        })
        print('Stream data:')
        print(df)
        print('\nDesign specs:')
        print(f'\tΔTmin = {DT_min} °C\n')

    hot_streams = [stream for stream in streams if stream.kind == 'hot']
    cold_streams = [stream for stream in streams if stream.kind == 'cold']

    # Use list comprehension to process temperature lists
    T_hot = [
        *(stream.T_source for stream in hot_streams),
        *(stream.T_target for stream in hot_streams)
    ]
    T_hot_adj = [T - DT_min for T in T_hot]
    T_cold = [
        *(stream.T_source for stream in cold_streams),
        *(stream.T_target for stream in cold_streams)
    ]
    T_list = [*T_hot_adj, *T_cold]  # combine
    T_list = list(set(T_list))  # merge duplicates
    T_list.sort(reverse=True)  # sort in descending order

    T_upper = np.array(T_list[:-1])
    T_lower = np.array(T_list[1:])

    intervals = (
        T_upper.astype(str) + ' °C' + ' to ' + T_lower.astype(str) + ' °C'
    )

    # Create pandas dataframe
    TI = pd.DataFrame({
        'T_upper': T_upper,
        'T_lower': T_lower
        }, index=intervals)

    TI.columns = pd.MultiIndex.from_arrays(
        (['T_upper', 'T_lower'], ['°C', '°C'])
    )

    T_upper = np.array(T_list[:-1])
    T_lower = np.array(T_list[1:])
    D_T = T_upper - T_lower
    D_C = np.zeros_like(T_upper, dtype=float)

    # Net heat capacity and residual enthalpy for each temperature interval
    for stream in streams:
        if stream in hot_streams:
            adj = DT_min
            C = stream.C  # hot streams have positive C
        elif stream in cold_streams:
            adj = 0
            C = -stream.C  # cold streams have negative C

        stream_T_upper = max(stream.T_source, stream.T_target)
        stream_T_lower = min(stream.T_source, stream.T_target)
        stream_T_range = (
            (stream_T_upper - adj >= T_upper) &
            (stream_T_lower - adj <= T_lower)
        )

        Ccol = np.zeros_like(T_upper, dtype=float)
        Ccol[stream_T_range] = C
        D_C += Ccol  # add stream heat capacity to net heat capacity column

        Cstr = np.round(Ccol, decimals=decimals).astype(str)
        TI[stream.name, 'kW/°C'] = (
            ['' if float(s) == 0.0 else s for s in Cstr]
        )  # add column for stream

    D_H = D_C * D_T  # net enthalpy

    # Add new columns to dataframe
    TI['ΔT', '°C'] = D_T
    TI['ΔC', 'kW/°C'] = D_C
    TI['ΔH', 'kW'] = D_H

    # Calculate residual and adjusted enthalpies
    TI['Residual ΔH', 'kW'] = TI['ΔH'].cumsum()  # residual enthalpy

    TI.loc['-'] = ['', ''] + [''] * len(streams) + ['', '', '', 0]
    idx = TI.index.tolist()
    idx.insert(0, idx.pop(idx.index('-')))
    TI = TI.reindex(idx)  # add top row

    TI['Adjusted ΔH', 'kW'] = (
        TI['Residual ΔH', 'kW'] - min(TI['Residual ΔH', 'kW'])
    )  # adjusted enthalpy

    # Grand composite curve
    if GCC is True:
        fig, ax = plt.subplots(
            figsize=(fsize, fsize), facecolor=facecolor
        )

        GCC_y = TI['T_lower', '°C'].to_numpy()
        GCC_y[0] = TI['T_upper', '°C'].to_numpy()[1]
        GCC_x = TI['Adjusted ΔH', 'kW'].to_numpy()

        ax.plot(GCC_x, GCC_y, 'k-')
        ax.set_xlabel('H (kW)', fontsize=font)
        ax.set_ylabel('T (°C)', fontsize=font)

    if GCC is True:
        return TI, fig, ax
    else:
        return TI


determine_pinch = find_pinch = perform_pinch_analysis = pinch_analysis
implement_TI = implement_TI_method = pinch_analysis
