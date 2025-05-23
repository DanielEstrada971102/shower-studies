import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

from mpldts.geometry import Station
from mpldts.patches import DTStationPatch
from dtpr.base import NTuple
from dtpr.utils.functions import color_msg
from dtpr.utils.config import RUN_CONFIG
from filter_matching_functions import  ray_rect_matching
from functools import partial

cell_patch_kwargs = {"facecolor": "none", "edgecolor": "none"}

_built_stations = {}

def get_p_d_from_tp(tp, station):
    # compute the center of the trigger primitive in the CMS frame
    if tp.quality >= 6: # correlated tps -> reference frame is the station
        sl1_center = station.super_layer(1).local_center
        sl3_center = station.super_layer(3).local_center
        _local_tp_z = (sl1_center[2] + sl3_center[2] ) / 2 # middle of the two super layers
        _transformer = partial(station.transformer.transform, from_frame="Station", to_frame="CMS")
    else: # uncorrelated tps -> reference frame is its super layer
        _local_tp_z = station.super_layer(tp.sl).local_center[2]
        _transformer = partial(station.super_layer(tp.sl).transformer.transform, from_frame="SuperLayer", to_frame="CMS")

    _local_tp_center = np.array([tp.posLoc_x, 0, _local_tp_z])
    tp_center = _transformer(_local_tp_center)

    # compute the direction of the trigger primitive in the CMS frame
    # -1 to point outside the CMS IP
    _dx = -1* np.sin(np.radians(tp.dirLoc_phi)) 
    _dz = np.cos(np.radians(tp.dirLoc_phi))
    tp_dir = _transformer(np.array([_dx, 0, _dz]))
    tp_dir = tp_dir / np.linalg.norm(tp_dir) # normalize the direction vector

    return tp_center, tp_dir


def filter_analyzer(ev, showers, tps):
    _checked_stations = set()

    # LINES for plotting will be marked with ^^^, comment to do not plot
    fig, ax = plt.subplots(1, 1, figsize=(6, 6)) # ^^^
    make_plot = False # ^^^

    for shower in showers:
        wh, sc, st = shower.wh, shower.sc, shower.st
        # to avoid analyzing the same station multiple times
        if (wh, sc, st) in _checked_stations:
            print(f"Already analyzed station {wh} {sc} {st}")
            continue
        _checked_stations.add((wh, sc, st))

        _tps = [tp for tp in tps if tp.wh == wh and (tp.st != st or tp.sc != sc)] # dont considere tps in the same station 

        if not _tps:
            print(f"No tps near the shower")
            continue

        make_plot = True # ^^^

        # to avoid building the same station multiple times
        if (wh, sc, st) in _built_stations:
            _dt = _built_stations[(wh, sc, st)]
        else:
            _dt = Station(wheel=wh, sector=sc, station=st)
            _built_stations[(wh, sc, st)] = _dt

        _x_center, _y_center, _z_center = _dt.local_center
        _width, _height, _ = _dt.bounds

        # build the rectangle
        _rect = np.array([
            [_x_center - _width / 2, 0, _z_center - _height / 2], # y component set to 0 -> 2D problem in ZX plane in local cords
            [_x_center + _width / 2, 0,  _z_center - _height / 2],
            [_x_center + _width / 2, 0, _z_center + _height / 2],
            [_x_center - _width / 2, 0, _z_center + _height / 2], 
            [_x_center - _width / 2, 0, _z_center - _height / 2]
        ])
        # move the rectangle to the global coordinates
        _rect = _dt.transformer.transform(_rect, from_frame="Station", to_frame="CMS")

        poly = Polygon(_rect[:, :2], closed=True, color='r', alpha=0.9) # ^^^
        ax.add_patch(poly) # ^^^
        DTStationPatch(station=_dt, faceview="phi", local=False, axes=ax, cells_kwargs=cell_patch_kwargs) # ^^^

        _built_stations_patches = {}
        for _tp in _tps:
            # get the trigger primitive station
            wh, sc, st = _tp.wh, _tp.sc, _tp.st
            if (wh, sc, st) in _built_stations:
                _seg_dt = _built_stations[(wh, sc, st)]
            else:
                _seg_dt = Station(wheel=wh, sector=sc, station=st)
                _built_stations[(wh, sc, st)] = _seg_dt

            if not (wh, sc, st) in _built_stations_patches:
                DTStationPatch(station=_seg_dt, faceview="phi", local=False, axes=ax, cells_kwargs=cell_patch_kwargs) # ^^^
                if _tp.sl == 0:
                    x, y, z = _seg_dt.global_center
                    ax.scatter(x, y, color="blue", s=10)
                else:
                    x, y, z = _seg_dt.super_layer(_tp.sl).global_center
                    ax.scatter(x, y, color="green", s=10)
            tp_center, tp_dir = get_p_d_from_tp(_tp, _seg_dt)
            color = "k"
            # check if the tp intersects with the rectangle - delete z component since it XY plane analysis
            if ray_rect_matching(tp_center[:-1], tp_dir[:-1], _rect[:, :-1]):
                # if mathc, add the shower to the tp mathed showers list
                if getattr(_tp, "matched_showers", None) is not None:
                    _tp.matched_showers.append(shower)
                else:
                    setattr(_tp, "matched_showers", [shower])
                color = "r"

            ax.arrow(*tp_center[:-1], *(20*tp_dir[:-1]), color=color)
            ax.annotate(f"TP{_tp.index}", xy=tp_center[:-1], textcoords="offset points", xytext=(0, 10), ha='center', color=color)
            

    if make_plot:
        ax.set_xlim(-800, 800)
        ax.set_ylim(-800, 800)
        plt.show()

    plt.close(fig)

def event_divider(ev):
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
        showers = [
            shower for shower in ev.filter_particles("fwshowers", is_true_shower=True) 
            if shower.sc in neighbors_sec
        ]
        # get the Trigger Primitives
        tps = [tp for tp in ev.tps if tp.sc in neighbors_sec]

        if not showers:
            print(f"BF{sector} has no showers")
            continue
        else:
            print(f"BF{sector} has {len(showers)} showers")
        if input(color_msg("Do you want to analyze this event?", color="yellow", return_str=True)) == "n":
            continue
        color_msg("Analyzing...", color="yellow")
        filter_analyzer(ev, showers, tps)

def main():
    RUN_CONFIG.change_config_file("run_config.yaml")

    ntuple = NTuple("../../ZprimeToMuMu_M-6000_TuneCP5_14TeV-pythia8/ZprimeToMuMu_M-6000_PU200/250312_131631/0000/DTDPGNtuple_12_4_2_Phase2Concentrator_thr6_Simulation_99.root")

    for ev in ntuple.events:
        if ev.fwshowers and any([shower.is_true_shower for shower in ev.fwshowers]):
            color_msg(f"Event: {ev.index}", color="green")
            event_divider(ev)
            input(color_msg("Press Enter to continue...", color="yellow", return_str=True))

if __name__ == "__main__":
    main()