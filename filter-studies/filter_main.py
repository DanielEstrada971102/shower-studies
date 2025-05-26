import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from mpldts.geometry.transforms import TransformManager
from mpldts.geometry import Station
from mpldts.patches import DTStationPatch
from dtpr.base import NTuple
from dtpr.utils.functions import color_msg, get_unique_locs
from dtpr.utils.config import RUN_CONFIG
from filter_matching_functions import  ray_rect_matching


# ----------- Auxiliary functions and variables ---------------
cell_patch_kwargs = {"facecolor": "none", "edgecolor": "none"}

_built_stations = {}
_built_stations_patches = {}
_built_transform_managers = {}

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
    # built/get the trigger primitive transform manager, since TPs ref frame is in the middle of the 
    # super layers, we need to build the transformation to put in the Station frame
    if (station.wheel, station.sector, station.number) in _built_transform_managers:
        _tps_transform_manager = _built_transform_managers[(station.wheel, station.sector, station.number)]
    else:
        _tps_transform_manager = TransformManager("TPsFrame")
        _tps_transform_manager.add("Station", "CMS", transformation_matrix=station.transformer.get_transformation("Station", "CMS"))

        mid_SLs_center = (np.array(station.super_layer(1).local_center) + np.array(station.super_layer(3).local_center)) / 2

        TStSLsC = mid_SLs_center # tranlation vector to move the center of the super layers to the origin in Station frame

        _tps_transform_manager.add("TPsFrame", "Station", translation_vector=TStSLsC)
        _built_transform_managers[(station.wheel, station.sector, station.number)] = _tps_transform_manager


    if tp.quality >= 6:
        # get the middle z in Station cords
        _local_tp_z = _tps_transform_manager.transform([0, 0, 0], from_frame="TPsFrame", to_frame="Station")[2] 
    else:
        # get the z coordinate of the super layer
        _local_tp_z = station.super_layer(tp.sl).local_center[2] 

    # get the x coordinate of the trigger primitive in Station cords
    _local_tp_x = _tps_transform_manager.transform([tp.posLoc_x, 0, 0], from_frame="TPsFrame", to_frame="Station")[0] 

    _local_tp_center = np.array([_local_tp_x, 0, _local_tp_z])
    # print(f"TP center in local cords: {_local_tp_center}")
    tp_center = _tps_transform_manager.transform(_local_tp_center, "Station", "CMS") # transform to CMS frame
    # print(f"TP center in CMS cords: {tp_center} -> {station.global_center}")

    _dx = -1* np.sin(np.radians(tp.psi)) # tal vez en lugar de usar psi, deberia usar dirLoc_phi?
    _dz = np.cos(np.radians(tp.psi))
    _local_tp_dir = np.array([_dx, 0, _dz]) # direction vector in local cords
    # print(f"TP direction in local cords: {_local_tp_dir}")
    tp_dir = _tps_transform_manager.transform(_local_tp_dir, "TPsFrame", "CMS")
    tp_dir = tp_dir / np.linalg.norm(tp_dir) # normalize the direction vector
    # print(f"TP direction in CMS cords: {tp_dir}")

    return tp_center, tp_dir

def get_rectangle(dt, shower):
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

def _analyzer(ev, showers, tps, debug=False, plot=False):
    """Analyze showers and TPs for a given event, optionally plotting results."""
    _checked_stations = set()

    if plot:
        _built_stations_patches.clear()
        fig, ax = plt.subplots(1, 1, figsize=(6, 6))
        make_plot = False

    for shower in showers:
        wh, sc, st = shower.wh, shower.sc, shower.st
        # to avoid analyzing the same station multiple times
        if (wh, sc, st) in _checked_stations:
            debug_print(color_msg(f"Already analyzed station {wh} {sc} {st}", color="red", return_str=True), debug)
            continue
        _checked_stations.add((wh, sc, st))

        if plot:
            make_plot = True

        # to avoid building the same station multiple times
        _dt = build_station(wh, sc, st)

        # get the rectangle for the shower
        _rect = get_rectangle(_dt, shower)

        if plot:
            plot_rectangle(ax, _rect)
            build_station_patch(_dt, ax)

        for _tp in tps:
            # get the trigger primitive station
            wh, sc, st = _tp.wh, _tp.sc, _tp.st
            _seg_dt = build_station(wh, sc, st)
            if plot:
                build_station_patch(_seg_dt, ax)

            tp_center, tp_dir = get_p_d_from_tp(_tp, _seg_dt)
            tp_color = "k"
            # match the trigger primitive with the rectangle
            if ray_rect_matching(tp_center[:-1], tp_dir[:-1], _rect[:, :-1]):
                if getattr(_tp, "matched_showers", None) is not None:
                    _tp.matched_showers.append(shower)
                else:
                    setattr(_tp, "matched_showers", [shower])
                debug_print(color_msg(f"TP: {_tp.index} match with shower: {shower.index}", color="purple", return_str=True), debug)
                tp_color = "r"
            if plot:
                ax.arrow(*tp_center[:-1], *(20*tp_dir[:-1]), color=tp_color)
                ax.annotate(f"TP{_tp.index}", xy=tp_center[:-1], textcoords="offset points", xytext=(0, 10), ha='center', color=tp_color)

    if plot and make_plot: 
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
        _analyzer(ev, showers, tps, debug, plot)

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
        barrel_filter_analyzer(ev)#, only4true_showers=True, debug=True, plot=True)
        if any(tp for tp in ev.tps if getattr(tp, "matched_showers", None)):
            print(f"Event {ev.index} has matched TPs with showers")

if __name__ == "__main__":
    main()