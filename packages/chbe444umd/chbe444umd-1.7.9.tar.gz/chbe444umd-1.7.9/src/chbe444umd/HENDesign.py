# Heat Integration: Stream Definition and Pinch Analysis by TI Method
# Written for CHBE444: Design I, University of Maryland
# (C) Ganesh Sriram, 2025, originally written in MATLAB in 2017
# Licensed under GNU Public License 3.0
# Author contact info: gsriram@umd.edu

from __future__ import annotations

import pandas as pd
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .Stream import Stream  # type checking: avoids circular imports


@dataclass
class HENDesign:
    """
    Container for HEN Design.

    Examples:

    Args:

    Returns:

    """

    n_stages: int  # 0: heaters, 1-k, process stream HX, k+1: coolers
    streams: list[Stream] = field(default_factory=list)
    # Q exchanged between hot stream i and cold stream j in stage k
    Q_exchange: Optional[pd.DataFrame] = None
    # Hot stream temperatures while entering each stage
    T_hot_streams: Optional[pd.DataFrame] = None
    # Cold stream temperatures while leaving each stage
    T_cold_streams: Optional[pd.DataFrame] = None
