import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np


def plot_station_wheel_profile(profile, ax=None, errors=None, **kwargs):
    """
    Plot or add on a Matplotlib axis a station-wheel profile.

    The input can be either a flat array with 20 values or a 4x5 array, where
    the first dimension is the station (MB1 to MB4) and the second dimension
    is the wheel (-2 to +2). The helper flattens the values internally and
    draws them at the fixed wheel positions used by the station-wheel layout.

    Axis decorations such as the MB labels, vertical separator lines, and the
    CMS label are added only once per axes, so the same axis can safely be
    reused to overlay multiple profiles.

    Styling can be customized with:
    - ``plot_kwargs``: forwarded to ``ax.errorbar`` for the profile markers and error bars.
    - ``st_labels_kwargs``: forwarded to ``ax.text`` for the MB labels.
    - ``vlines_kwargs``: forwarded to ``ax.axvline`` for the station separators.
    - ``cms_label_kwargs``: forwarded to ``hep.cms.label``.
    - ``tick_params_kwargs``: forwarded to ``ax.tick_params``.
    - ``xlabel_kwargs``: forwarded to ``ax.set_xlabel``.
    - ``figsize``: figure size used when ``ax`` is not provided.

    Parameters
    ----------
    profile : array-like
        Profile values shaped as either ``(20,)`` or ``(4, 5)``.
    ax : matplotlib.axes.Axes, optional
        Axis to draw on. If omitted, a new figure and axis are created.
    errors : array-like, optional
        Error values shaped as either ``(20,)`` or ``(4, 5)``.
    **kwargs : dict
        Additional styling and layout options.

    Returns
    -------
    fig, ax
        The figure and axis containing the plot.
    """
    def flatten_profile(a):
        if isinstance(a, list):
            a = np.array(a)
        if a.shape == (4, 5):
            return a.flatten()
        elif a.shape == (20,):
            return a
        else:
            raise ValueError("Profile should be a 20 size 1D array or a 4x5 array.")
    profile_vals = flatten_profile(profile)
    if errors is not None:
        error_vals = flatten_profile(errors)
    else:
        error_vals = np.zeros_like(profile_vals)

    tick_positions = [0, 1, 2, 3, 4, 5.5, 6.5, 7.5, 8.5, 9.5, 11.0, 12.0, 13.0, 14.0, 15.0, 16.5, 17.5, 18.5, 19.5, 20.5]

    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6) if 'figsize' not in kwargs else kwargs.pop('figsize'))
    else:
        fig = ax.figure

    plot_kwargs = kwargs.pop('plot_kwargs', {"marker": "o", "elinewidth": 1, "capsize": 0})

    ax.errorbar(
            tick_positions, profile_vals,
            yerr=error_vals,
            **plot_kwargs
    )

    if not getattr(ax, '_plot_station_wheel_profile_decorated', False):
        ax._plot_station_wheel_profile_decorated = True

        ax.set_xticks(tick_positions)
        tick_labels = ['-2', '-1', '0', '1', '2'] * 4 # 4 times for 4 stations
        ax.set_xticklabels(tick_labels)

        ax.set_ylim(kwargs.pop('ylim', (0, 1.1)))

        # Station Labels
        st_labels_kwargs = kwargs.pop('st_labels_kwargs', {"fontweight": "bold", "ha": "center"})
        vlines_kwargs = kwargs.pop('vlines_kwargs', {"color": "black", "linestyle": "--", "alpha": 0.5})
        st_label_y = kwargs.pop('st_label_y', 0.65)
        for st in range(4):
            center = (st * 5.5) + 2
            ax.text(center, ax.get_ylim()[0] + (ax.get_ylim()[1] * st_label_y), f"MB{st + 1}", **st_labels_kwargs)
            if st < 3:
                ax.axvline((st * 5.5) + 4.75, **vlines_kwargs)

        ax.set_xlabel("Wheel", **kwargs.pop('xlabel_kwargs', {}))
        ax.tick_params(axis='both', which='major', **kwargs.pop('tick_params_kwargs', {}))

        cms_label_kwargs = kwargs.pop('cms_label_kwargs', {"text": "(private work)", "data": False, "rlabel": "PU200"})

        hep.cms.label(ax=ax, **cms_label_kwargs)

    return fig, ax