import numpy as np
import matplotlib.pyplot as plt
from pandas import DataFrame
from matplotlib import colors
from matplotlib.patches import Polygon
from mpldts.geometry import Station, AMDTSegments
from mpldts.patches import DTStationPatch, AMDTSegmentsPatch
from dtpr.base import NTuple
from dtpr.utils.functions import color_msg, get_unique_locs
from dtpr.utils.config import RUN_CONFIG
from filter_matching_functions import  ray_rect_matching, ray_seg_matching

# ----------- Auxiliary functions and variables ---------------
cell_patch_kwargs = {"facecolor": "none", "edgecolor": "none"}
cmap = colors.ListedColormap(["k", "r"]) 
cmap.set_under('none')  # Set color for values below the minimum
segs_norm = colors.BoundaryNorm(boundaries=[0, 1, 2], ncolors=2, clip=True)

segs_kwargs = {
    "cmap": cmap,
    "norm": segs_norm,
}

_built_stations = {}
_built_stations_patches = {}

def build_station(wh, sc, st):
    """Build or retrieve a Station object for given wheel, sector, station."""
    key = (wh, sc, st)
    if key in _built_stations:
        return _built_stations[key]
    _dt = Station(wheel=wh, sector=sc, station=st)
    _built_stations[key] = _dt
    return _dt

def build_station_patch(station, ax):
    """Build or retrieve a DTStationPatch for given station."""
    key = station.wheel, station.sector, station.number
    if key in _built_stations_patches:
        return _built_stations_patches[key]
    _patch = DTStationPatch(station=station, faceview="phi", local=False, axes=ax, cells_kwargs=cell_patch_kwargs)
    _built_stations_patches[key] = _patch
    return _patch

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

def debug_print(msg, debug):
    if debug:
        print(msg)

def should_analyze_event(debug):
    if not debug:
        return True
    resp = input(color_msg("Do you want to analyze this event?", color="yellow", return_str=True))
    return resp.strip().lower() != "n"

# ------------------------------------

def get_p_d_from_tp(tp, station):
    """Get the position and direction of a trigger primitive in CMS coordinates."""

    _am_tp = AMDTSegments( # this class encapsulates the TPs reference frame transformations
        parent=station, 
        segs_info={
            "index": tp.index,
            "sl": tp.sl,
            "angle": getattr(tp, "dirLoc_phi"),
            "position": getattr(tp, "posLoc_x"),
        }
    )[0]

    tp_center = _am_tp.global_center
    tp_dir = _am_tp.global_direction

    return tp_center, tp_dir


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

def get_shower_segment(dt, shower, version=1):
    """
    Get the segment representing the shower in CMS coordinates.
    """
    if version == 1: # compute using the wires profile
        # dump profile to wires numbers
        wires = [wn for wn, nh in enumerate(shower.wires_profile) for _ in range(nh)]
        q75, q25 = map(int, np.percentile(wires, [75, 25]))
        # use only the wires in the range [q25, q75]
        wires = sorted([wire for wire in wires if wire >= q25 and wire <= q75])

        first_shower_cell = dt.super_layer(shower.sl).layer(2).cell(wires[0])
        last_shower_cell = dt.super_layer(shower.sl).layer(2).cell(wires[-1])
    if version == 2: # compute using max and min wire numbers
        first_shower_cell = dt.super_layer(shower.sl).layer(2).cell(shower.min_wire)
        last_shower_cell = dt.super_layer(shower.sl).layer(2).cell(shower.max_wire)

    return np.array([first_shower_cell.global_center, last_shower_cell.global_center]) # a, b

def _analyzer(showers, tps, debug=False, plot=False):
    """Analyze showers and TPs for a given event, optionally plotting results."""
    if plot:
        _built_stations_patches.clear()
        fig, ax = plt.subplots(1, 1, figsize=(6, 6))
        make_plot = False

    for shower in showers:
        wh, sc, st = shower.wh, shower.sc, shower.st

        if plot:
            make_plot = True

        # to avoid building the same station multiple times
        _dt = build_station(wh, sc, st)

        # get the rectangle for the shower
        # _rect = get_shower_rectangle(_dt, shower)
        _shower_seg = get_shower_segment(_dt, shower, version=2)

        if plot:
            # plot_rectangle(ax, _rect)
            plot_shower_segment(ax, _shower_seg)
            build_station_patch(_dt, ax)

        _tps_to_plot = []
        for _tp in tps:
            # get the trigger primitive station
            wh, sc, st = _tp.wh, _tp.sc, _tp.st
            _seg_dt = build_station(wh, sc, st)
            if plot:
                build_station_patch(_seg_dt, ax)

            tp_center, tp_dir = get_p_d_from_tp(_tp, _seg_dt)
            tp_color = "k"
            
            # if ray_rect_matching(tp_center[:-1], tp_dir[:-1], _rect[:, :-1]): # <-- match the trigger primitive with the rectangle
            if ray_seg_matching(tp_center[:-1], tp_dir[:-1], _shower_seg[0, :-1], _shower_seg[1, :-1]): # <-- match the trigger primitive with segment
                if _tp not in shower.matched_tps:
                    shower.matched_tps.append(_tp)
                if shower not in _tp.matched_showers:
                    _tp.matched_showers.append(shower)
                debug_print(color_msg(f"TP: {_tp.index} match with shower: {shower.index}", color="purple", return_str=True), debug)
                tp_color = "r"
            if plot:
                _tps_to_plot.append({
                    "wh": _tp.wh,
                    "sc": _tp.sc,
                    "st": _tp.st,
                    "index": _tp.index,
                    "sl": _tp.sl,
                    "angle": getattr(_tp, "dirLoc_phi"),
                    "position": getattr(_tp, "posLoc_x"),
                    "matched": 0 if tp_color == "k" else 1,
                })

    if plot and make_plot: 
        for (wh, sc, st), _tps_info in DataFrame(_tps_to_plot).groupby(["wh", "sc", "st"]):
            _segs = AMDTSegments(parent=build_station(wh, sc, st), segs_info=_tps_info[["index", "sl", "angle", "position", "matched"]])
            _segs_patch = AMDTSegmentsPatch(
                segments=_segs, axes=ax, faceview="phi", local=False, vmap="matched", segs_kwargs=segs_kwargs
            )
        ax.set_xlim(-800, 800)
        ax.set_ylim(-800, 800)
        plt.show()
        plt.close(fig)

def event_divider(ev, only4true_showers=False, debug=False, plot=False):
    """Divide event into sectors and analyze showers/TPs for each sector."""
    # first divide the problem as a BF board can see (3 adjacent sectors and all wheels)
    for sector in range (1, 13):
        neighbors_sec = [
            (sector - 1) if (sector - 1) >= 1 else 12,
            sector,
            (sector + 1) if (sector + 1) < 13 else 1
        ]
        if sector in [3, 4, 5]:
            neighbors_sec.append(13)
        if sector in [9, 10, 11]:
            neighbors_sec.append(14)

        # get the showers
        if only4true_showers:
            showers = [
                shower for shower in ev.filter_particles("fwshowers", is_true_shower=True)
                if shower.sc in neighbors_sec
            ]
        else:
            showers = [
                shower for shower in ev.fwshowers
                if shower.sc in neighbors_sec
            ]

        if not showers:
            debug_print(f"BF{sector} has no showers", debug)
            continue
        debug_print(f"BF{sector} has {len(showers)} showers", debug)

        showers_locs = get_unique_locs(showers, ["wh", "sc", "st"])
        # get the Trigger Primitives
        # ignore tps that live in the chamber of the shower
        tps = [tp for tp in ev.tps if tp.sc in neighbors_sec and (tp.wh, tp.sc, tp.st) not in showers_locs]
        if not tps:
            debug_print(f"No tps near the shower", debug)
            continue
        debug_print(f"BF{sector} has {len(tps)} TPs to analyze", debug)

        if not should_analyze_event(debug):
            continue
        debug_print(color_msg("Analyzing...", color="yellow", return_str=True), debug)
        _analyzer(showers, tps, debug, plot)

def barrel_filter_analyzer(ev, only4true_showers=False, debug=False, plot=False):
    """Run the barrel filter analyzer for a single event."""
    if only4true_showers:
        showers = [
            shower for shower in ev.filter_particles("fwshowers", is_true_shower=True)
        ]
    else:
        showers = [
            shower for shower in ev.fwshowers
        ]
    if showers:
        debug_print(color_msg(f"Event {ev.index}", color="green", return_str=True), debug)
        event_divider(ev, only4true_showers, debug, plot)
        if debug:
            input(color_msg("Press Enter to continue...", color="yellow", return_str=True))

def main():
    """Main entry point for running the filter analysis."""
    RUN_CONFIG.change_config_file("run_config.yaml")
    ntuple = NTuple("../../ZprimeToMuMu_M-6000_TuneCP5_14TeV-pythia8/ZprimeToMuMu_M-6000_PU200/250312_131631/0000/DTDPGNtuple_12_4_2_Phase2Concentrator_thr6_Simulation_99.root")
    for ev in ntuple.events:
        barrel_filter_analyzer(ev, only4true_showers=True, debug=True, plot=True)
        if any(tp for tp in ev.tps if getattr(tp, "matched_showers", None)):
            print(f"Event {ev.index} has matched TPs with showers")

if __name__ == "__main__":
    main()