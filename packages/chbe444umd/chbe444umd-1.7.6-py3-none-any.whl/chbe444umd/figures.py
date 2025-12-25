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
