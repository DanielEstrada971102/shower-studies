import numpy as np
import matplotlib.pyplot as plt
from pandas import DataFrame
from matplotlib import colors
from matplotlib.patches import Polygon
from mpldts.geometry import AMDTSegments
from mpldts.geometry.station import STATION_CACHE
from mpldts.patches import DTStationPatch, MultiDTSegmentsPatch
from dtpr.base import NTuple
from dtpr.utils.functions import color_msg, get_unique_locs
from dtpr.base.config import RUN_CONFIG
from filter_matching_functions import  ray_rect_matching, ray_seg_matching
from functools import partial, cache

# ----------- Auxiliary functions and variables ---------------
cell_patch_kwargs = {"facecolor": "none", "edgecolor": "none"}
cmap = colors.ListedColormap(["k", "r"]) 
cmap.set_under('none')  # Set color for values below the minimum
segs_norm = colors.BoundaryNorm(boundaries=[0, 1, 2], ncolors=2, clip=True)

segs_kwargs = {
    "cmap": cmap,
    "norm": segs_norm,
}

# Cache for built Station objects to avoid redundant constructions
Station = STATION_CACHE.get 
_built_stations_patches = {}

BF_neighbor_sectors = {}
for sector in range(1, 13):
    neighbors_sec = [
        (sector - 1) if (sector - 1) >= 1 else 12,
        sector,
        (sector + 1) if (sector + 1) < 13 else 1
    ]
    if sector in [3, 4, 5]:
        neighbors_sec.append(13)
    if sector in [9, 10, 11]:
        neighbors_sec.append(14)
    BF_neighbor_sectors[f"BF{sector}"] = neighbors_sec


def plot_rectangle(ax, rect, color='r', alpha=0.2):
    """Plot a rectangle (polygon) on the given axes."""
    poly = Polygon(rect[:, :2], closed=True, color=color, alpha=alpha)
    ax.add_patch(poly)
    return poly

def plot_shower_segment(ax, segment, color='g'):
    """Plot a segment representing the shower on the given axes."""
    x1, y1, _ = segment[0]
    x2, y2, _ = segment[1]
    ax.plot([x1, x2], [y1, y2], color=color, linewidth=3)

def make_plot(things_to_plot):
    """Create a plot with DT stations, showers, and TPs."""
    if not all(things_to_plot.values()):
        color_msg("Nothing to plot, skipping...", color="yellow", indentLevel=1)
        return
    fig, ax = plt.subplots(1, 1, figsize=(6, 6))
    _built_stations_patches.clear()  # Clear previous patches to avoid duplicates

    if things_to_plot["dts"]:
        for dt in things_to_plot["dts"].values():
            key = dt.wheel, dt.sector, dt.number
            if key not in _built_stations_patches:
                DTStationPatch(station=dt, faceview="phi", local=False, axes=ax, cells_kwargs=cell_patch_kwargs)
    if things_to_plot["showers"]:
        for shower in things_to_plot["showers"]:
            # plot_rectangle(ax, shower)
            plot_shower_segment(ax, shower)
    if things_to_plot["tps"]:
        MultiDTSegmentsPatch(
            segments=things_to_plot["tps"], axes=ax, faceview="phi", local=False, vmap="matched", segs_kwargs=segs_kwargs
        )
    ax.set_xlim(-800, 800)
    ax.set_ylim(-800, 800)
    ax.set_aspect('equal', adjustable='box')
    plt.show()
    plt.close(fig)

# ------------------------------------

def get_shower_rectangle(dt, shower, version=1):
    """
    Get the rectangle (polygon) representing the shower in CMS coordinates. Shower is not used
    at the moment, but in theory it should be used to define the size of the rectangle.
    """
    #  D _________ C
    #   |         |
    #   |_________|
    #  A           B
    _x_center, _y_center, _z_center = dt.local_center
    _width, _height, _ = dt.bounds

    # build the rectangle
    _rect = np.array([
        # y component set to 0 -> 2D problem in ZX plane in local cords
        [_x_center - _width / 2, 0, _z_center - _height / 2], # A
        [_x_center + _width / 2, 0,  _z_center - _height / 2], # B
        [_x_center + _width / 2, 0, _z_center + _height / 2], # C
        [_x_center - _width / 2, 0, _z_center + _height / 2], # D
        [_x_center - _width / 2, 0, _z_center - _height / 2] # A (to close the rectangle)
    ])
    # move the rectangle to the global coordinates
    rect = dt.transformer.transform(_rect, from_frame="Station", to_frame="CMS")
    return rect

def get_shower_segment(dt, shower, version=1, cover_full_cells=True):
    """
    Get the segment representing the shower in CMS coordinates.
    """
    if version == 1: # compute using the wires profile
        # dump profile to wires numbers
        try:
            wires = [wn for wn, nh in enumerate(shower.wires_profile) for _ in range(nh)]
            q75, q25 = map(int, np.percentile(wires, [75, 25]))
            # use only the wires in the range [q25, q75]
            wires = sorted([wire for wire in wires if wire >= q25 and wire <= q75 ])
            wires[-1] = wires[-1] + 1 if wires[-1] == wires[0] else wires[-1]

            first_wire = wires[0] if wires[0] >= dt.super_layer(shower.sl).layer(2)._first_cell_id else dt.super_layer(shower.sl).layer(2)._first_cell_id
            last_wire = wires[-1] if wires[-1] <= dt.super_layer(shower.sl).layer(2)._last_cell_id else dt.super_layer(shower.sl).layer(2)._last_cell_id
            first_shower_cell = dt.super_layer(shower.sl).layer(2).cell(first_wire)
            last_shower_cell = dt.super_layer(shower.sl).layer(2).cell(last_wire)
        except:
            first_wire = shower.min_wire
            last_wire = shower.max_wire
            first_shower_cell = dt.super_layer(shower.sl).layer(2).cell(first_wire)
            last_shower_cell = dt.super_layer(shower.sl).layer(2).cell(last_wire)
    if version == 2: # compute using max and min wire numbers
        first_wire = shower.min_wire
        last_wire = shower.max_wire
        first_shower_cell = dt.super_layer(shower.sl).layer(2).cell(first_wire)
        second_shower_cell = dt.super_layer(shower.sl).layer(2).cell(first_wire+1)
        last_shower_cell = dt.super_layer(shower.sl).layer(2).cell(last_wire)

    # Build segment from cell centers, optionally expanding to full-cell coverage
    a = np.array(first_shower_cell.global_center)
    b = np.array(last_shower_cell.global_center)
    c = np.array(second_shower_cell.global_center)
    d=((second_shower_cell.global_center)[0]-(first_shower_cell.global_center)[0],(second_shower_cell.global_center)[1]-(first_shower_cell.global_center)[1],(second_shower_cell.global_center)[2]-(first_shower_cell.global_center)[2])
    if cover_full_cells:
        a = a + d 
        b = b - d
    return np.array([a, b]) # a, b

def match_tp_to_shower(segment, shower):
    """Match AM TP to a given shower"""
    # rect = shower[:, :-1] # <-- match the trigger primitive with the rectangle
    a, b = shower[0, :-1], shower[1, :-1] # <-- match the trigger primitive with segment
    p, d = segment.global_center[:-1], segment.global_direction[:-1]  # get the position and direction of the TP
    # Check if the ray from TP intersects with the shower segment
    # return ray_rect_matching(p, d, rect)
    return ray_seg_matching(p, d, a, b)

def _analyzer(showers, tps, shower_seg_version=2, debug=False, plot=False, cover_full_cells=False):
    """Analyze showers and TPs for a given event, optionally plotting results."""
    if plot:
        _things_to_plot = {"dts": {}, "showers": [], "tps": None}

    for shower in showers:
        wh, sc, st = shower.wh, shower.sc, shower.st

        _tps2use = [tp for tp in tps if tp.wh == wh and tp.st!= st] # Just take TPs from the same wheel as the shower, but different station
        if not _tps2use:
            continue  # skip if no TPs in the same wheel as the shower --> THIS DEFINES THAT THIS MATCHING IS LIMITED TO THE PHI VIEW

        # to avoid building the same station multiple times
        _dt = Station(wh, sc, st)
        if plot and (wh, sc, st) not in _things_to_plot["dts"]:
            _things_to_plot["dts"][(wh, sc, st)] = _dt

        # get the rectangle for the shower
        # _rect = get_shower_rectangle(_dt, shower)
        _shower_seg = get_shower_segment(_dt, shower, version=shower_seg_version,cover_full_cells=cover_full_cells)

        if plot:
            # _things_to_plot["showers"].append(_rect)
            _things_to_plot["showers"].append(_shower_seg)

        # build dicts with tps information
        _tps_info = []
        for _tp in _tps2use:
            _parent_dt = Station(_tp.wh, _tp.sc, _tp.st)
            _tps_info.append({
                "parent": _parent_dt,  # parent station of the TP
                "index": _tp.index,
                "sl": _tp.sl,
                "angle": getattr(_tp, "dirLoc_phi"),
                "position": getattr(_tp, "posLoc_x"),
                "tp_obj": _tp,  # store the TP object for later use
            })
            if plot and (_tp.wh, _tp.sc, _tp.st) not in _things_to_plot["dts"]:
                _things_to_plot["dts"][(_tp.wh, _tp.sc, _tp.st)] = _parent_dt

        _tps_geo = AMDTSegments(segs_info=_tps_info) # geometrically objects that allow to get global coordinates of TPs

        # match TPs to the shower
        match_results = map(partial(match_tp_to_shower, shower=_shower_seg), _tps_geo.segments)

        for matched, _tp_seg in zip(match_results, _tps_geo.segments):
            if plot:
                _tp_seg.matched = int(matched)  # store the match result for plotting
            if not matched:
                continue
            # Add the TP to the shower matched TPs
            if _tp_seg.tp_obj not in shower.matched_tps:
                shower.matched_tps.append(_tp_seg.tp_obj)
            # Add the shower to the TP matched showers
            if shower not in _tp_seg.tp_obj.matched_showers:
                _tp_seg.tp_obj.matched_showers.append(shower)
            if debug:
                color_msg(f"TP: {_tp_seg.tp_obj.index} match with shower: {shower.index}", color="purple", indentLevel=2)

        if plot:
            _things_to_plot["tps"] = _tps_geo
    if plot:
        make_plot(_things_to_plot)

def barrel_filter_analyzer(ev, only4true_showers=False, shower_seg_version=2, debug=False, plot=False,cover_full_cells=False, showers2use_name="fwshowers"):
    """Divide event into sectors and analyze showers/TPs for each sector."""
    # simple filter in case only true showers are needed, or to avoid analyzing events without showers
    _showers = ev.filter_particles(showers2use_name, is_true_shower=True) if only4true_showers else getattr(ev, showers2use_name)
    if not _showers:
        if debug:
            color_msg("No showers found in the event", color="red", indentLevel=1)
        return None

    # first divide the problem as a BF board can see (3 adjacent sectors and all wheels)
    for sector in range (1, 13):
        neighbors_sec = BF_neighbor_sectors[f"BF{sector}"]

        # get the showers
        showers = [shower for shower in _showers if shower.sc in neighbors_sec]

        if not showers:
            if debug:
                color_msg(f"BF{sector} has no showers", indentLevel=1)
            continue
        if debug:
            color_msg(f"BF{sector} has {len(showers)} showers", indentLevel=1)

        showers_locs = get_unique_locs(showers, ["wh", "sc", "st"])
        # get the Trigger Primitives
        # ignore tps that live in the chamber of the shower
        tps = [
            tp for tp in ev.tps 
            if tp.sc in neighbors_sec # Just take TPs from the sectors that lives in the BF sector
        ]
        if not tps:
            if debug:
                color_msg(f"No tps near the shower", indentLevel=1)
            continue
        if debug:
            color_msg(f"BF{sector} has {len(tps)} TPs to analyze", indentLevel=1)

        if debug and input(color_msg("Do you want to analyze this sectors?", color="yellow", indentLevel=1, return_str=True)).strip().lower() == "n":
            continue
        if debug:
            color_msg("Analyzing...", color="yellow", indentLevel=1)
        _analyzer(showers, tps, shower_seg_version, debug, plot, cover_full_cells=cover_full_cells) # this only analyze in Phi view

def main():
    """Main entry point for running the filter analysis."""
    import os
    RUN_CONFIG.change_config_file(
        os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "run_config.yaml"
            )
        )
    )
    ntuple = NTuple(os.path.abspath(
        os.path.abspath(
            os.path.join(\
                os.path.dirname(__file__), 
                "../ntuples/DTDPGNtuple_12_4_2_Phase2Concentrator_thr6_Simulation_99.root",
            )
        )
    ))
    debug = True  # Set to True to enable debug mode
    only4true_showers = False  # Set to True to analyze only true showers
    plot = True  # Set to True to enable plotting

    for i, ev in enumerate(ntuple.events):
        if ev is None:
            continue
        if debug:
            color_msg(f"Event {ev.index}", color="green")
        # if ev.number == 3915:
        #     print(ev)
        #     for tp in ev.tps:
        #         print(tp)
        #     for shower in ev.fwshowers:
        #         print(shower)
        if barrel_filter_analyzer(ev, only4true_showers=only4true_showers, debug=debug, plot=plot) is None:
            continue
        if debug:
            input(color_msg("Press Enter to continue...", color="yellow", return_str=True))

if __name__ == "__main__":
    main()

    