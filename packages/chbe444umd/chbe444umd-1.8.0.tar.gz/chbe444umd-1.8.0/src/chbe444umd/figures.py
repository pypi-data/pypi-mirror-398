# Figure Duplication
# Written for CHBE444: Design I, University of Maryland
# (C) Ganesh Sriram, 2025
# Licensed under GNU Public License 3.0
# Author contact info: gsriram@umd.edu

import pickle


def duplicate_figure(fig):
    """
    Duplicates a figure.

    Example:
        fignew, axnew = duplicate(fig)

    Args:
        fig: A previously created figure object.

    Returns:
        A figure object that is a duplicate of the original figure and a
            corresponding axes object.
    """
    pkl = pickle.dumps(fig)  # serialize figure
    fignew = pickle.loads(pkl)  # deserialize into fignew
    axnew = fignew.axes[0]
    return fignew, axnew
