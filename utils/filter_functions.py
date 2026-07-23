from functools import partial

import matplotlib.pyplot as plt
import numpy as np
from dtpr.base import Event
from dtpr.utils.functions import append_to_matched_list, color_msg, get_unique_locs
from utils.shower_functions import get_shower_segment, get_shower_rectangle
from mpldts.geometry.station import STATION_CACHE
from mpldts.geometry import AMDTSegments

Station = STATION_CACHE.get


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


def ray_seg_matching(p, d, a, b):
    """
    Check if the ray defined by point p and direction d intersects with the segment defined by the points a and b.

    :param p: Point from which the ray starts.
    :type p: numpy.ndarray(shape=(2,))
    :param d: Direction of the ray.
    :type d: numpy.ndarray(shape=(2,))
    :param a: Start point of the segment.
    :type a: numpy.ndarray(shape=(2,))
    :param b: End point of the segment.
    :type b: numpy.ndarray(shape=(2,))
    :return: True if the ray intersects with the segment, False otherwise.
    :rtype: bool
    .. note:: The function uses Cramer's rule to solve the system of equations that determines the intersection point.
    """
    p= np.array(p) if not isinstance(p, np.ndarray) else p
    d = np.array(d) if not isinstance(d, np.ndarray) else d
    a = np.array(a) if not isinstance(a, np.ndarray) else a
    b = np.array(b) if not isinstance(b, np.ndarray) else b

    v1 = b - a
    v2 = p - a

    # cramer's rule
    denom = np.linalg.det(np.array([v1, -d]).T)
    if denom == 0:
        # The ray and the segment are parallel
        return False
    u = np.linalg.det(np.array([v2, -d]).T) / denom
    t = np.linalg.det(np.array([v1, v2]).T) / denom

    if 0 <= u <= 1:
        return True
    return False


def ray_rect_matching(p, d, verts):
    """
    Check if the ray defined by point p and direction d intersects with the rectangle defined by its 4 vertices.

    :param p: Point from which the ray starts.
    :type p: numpy.ndarray(shape=(2,))
    :param d: Direction of the ray.
    :type d: numpy.ndarray(shape=(2,))
    :param verts: Vertices of the rectangle.
    :type verts: numpy.ndarray(shape=(4, 2))
    :return: True if the ray intersects with the rectangle, False otherwise.
    :rtype: bool

    .. note:: The function checks for intersection with each segment of the rectangle.
    """
    if any(ray_seg_matching(p, d, verts[i], verts[(i + 1) % len(verts)]) for i in range(len(verts))):
        return True
    return False

def get_projection(vect, plane="xy"):
    """
    Get the correct coordinates to make the 2D matching
    :param vect: 3D vector to project.
    :type vect: numpy.ndarray(shape=(3,))
    :param plane: Plane to project onto. Can be "xy" or "zr".
    :type plane: str
    """
    if plane == "xy":
        return vect[0], vect[1]
    elif plane == "zr":
        return vect[2], np.sqrt(vect[0] ** 2 + vect[1] ** 2)

def match_tp_to_shower(segment, shower, shower_geometry="segment"):
    """Match AM TP to a given shower"""
    if shower_geometry!="segment":
        raise DeprecationWarning("The 'rectangle' shower geometry is deprecated. Please use 'segment' instead.")

    if (segment.sl ==2 and shower.sl != 2) or (segment.sl != 2 and shower.sl == 2):
        raise ValueError("Cannot match a SL2 TP to a non-SL2 shower and vice versa.")

    plane = "zr" if shower.sl == 2 else "xy"  # use zr plane for SL2 showers, xy plane for others

    # get the position and direction of the TP
    if plane == "xy":
        p = segment.global_center[:-1] # CHECK IF SEGMENT ARE WELL DEFINED IN THETA
        d = segment.global_direction[:-1]
        a = shower[0:, :-1]
        b = shower[1:, :-1]
    elif plane == "zr":
        s_x, s_y, s_z = segment.global_center
        p = np.array([s_z, np.sqrt(s_x ** 2 + s_y ** 2)])
        d_x, d_y, d_z = segment.global_direction
        d = np.array([d_z, np.sqrt(d_x ** 2 + d_y ** 2)])
        _shower = np.c_[shower, np.sqrt(shower[:, 0]**2 + shower[:, 1]**2)]  # add the radial coordinate to the shower points
        a = _shower[0:, [2, 3]]  # use z and r 
        b = _shower[1:, [2, 3]]  

    # Check if the ray from TP intersects with the shower segment
    return ray_seg_matching(p, d, a, b)

def showers_tps_analyze_matching(
    showers: list,
    tps: list,
    **matching_kwargs):

    showers2use = [shower for shower in showers]

    if not showers2use:
        return

    only_phi = matching_kwargs.get("only_phi", False)

    for shower in showers2use:
        if only_phi and shower.sl==2:
            continue # skip showers in SL2 if only_phi Analysis is True

        wh, sc, st = shower.wh, shower.sc, shower.st

        if shower.sl !=2:
            tps2use = [tp for tp in tps if tp.sl != 2 and tp.wh == wh and tp.sc != sc and tp.st != st] # Just take TPs from the same wheel as the shower, but different chamber
        else:
            tps2use = [tp for tp in tps if tp.sl == 2 and tp.sc == sc and tp.wh !=wh and tp.st != st] # Just take TPs from the same sector as the shower, but different chamber

        if not tps2use:
            continue

        # get the geometrical representation for the shower
        shower_geometry2use = matching_kwargs.get("shower_geometry", "segment") # by default use the shower segment
        
        if shower_geometry2use == "rectangle":
            raise DeprecationWarning("The 'rectangle' shower geometry is deprecated. Please use 'segment' instead.")
            shower_geo = get_shower_rectangle(shower)
        elif shower_geometry2use == "segment":
            shower_geo = get_shower_segment(
                shower,
                version=matching_kwargs.get("shower_seg_version", 2), # by default use the shower segment version 2
                cover_full_cells=matching_kwargs.get("cover_full_cells", False) # by default do not cover the full cells
            )
        else:
            raise ValueError(f"Invalid shower_geometry: {shower_geometry2use}. Must be 'rectangle' or 'segment'.")

        def get_tp_info(tp):
            """
            Get the information of a tp, needed to build its geometrical representation.
            """
            parent_dt = Station(tp.wh, tp.sc, tp.st) # parent station of the TP
            return {
                "parent": parent_dt,
                "index": tp.index,
                "sl": tp.sl,
                "angle": getattr(tp, "dirLoc_phi"),
                "position": getattr(tp, "posLoc_x"),
                "tp_obj": tp,  # store the TP object for later use
            }

        tps_geo = AMDTSegments(segs_info=[get_tp_info(tp) for tp in tps2use])

        # match TPs to the shower
        match_results = map(partial(match_tp_to_shower, shower=shower_geo), tps_geo.segments)

        for matched, _tp_seg in zip(match_results, tps_geo.segments):
            if not matched:
                continue
            # Add the TP to the shower matched TPs
            append_to_matched_list(shower, 'matched_tps', _tp_seg.tp_obj)
            # Add the shower to the TP matched showers
            append_to_matched_list(_tp_seg.tp_obj, 'matched_showers', shower)


def barrel_filter_showers_tps_matcher(
    ev: Event, 
    debug: bool = False,
    plot: bool = False,
    filter_kwargs: dict|None = None,
    matching_kwargs: dict|None = {
        "shower_seg_version": 2,
        "cover_full_cells": False
    },
    showers2use_name: str = "fwshowers",
    tps2use_name: str = "tps"):
    """
    Divide event into Barrel Filter (BF) sectors and perform the matching of showers and TPs within each sector.

    :param ev: Event object containing showers and TPs.
    :type ev: Event
    :param filter_kwargs: Keyword arguments for filtering showers.
    :type filter_kwargs: dict|None
    :param matching_kwargs: Keyword arguments for matching showers and TPs.
    :type matching_kwargs: dict|None
    :param debug: If True, print debug information.
    :type debug: bool
    :param plot: If True, generate plots for the analysis.
    :type plot: bool
    :param showers2use_name: Name of the attribute in the event object that contains showers.
    :type showers2use_name: str
    :param tps2use_name: Name of the attribute in the event object that contains TPs.
    :type tps2use_name: str
    """

    # simple filter in case only true showers are needed, or to avoid analyzing events without showers
    _showers = ev.filter_particles(showers2use_name, **filter_kwargs) if filter_kwargs is not None else getattr(ev, showers2use_name)

    if not _showers:
        if debug:
            color_msg("No showers found in the event", color="red", indentLevel=1)
        return

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

        tps = [
            tp for tp in getattr(ev, tps2use_name)
            if tp.sc in neighbors_sec # Just take TPs from the sectors that lives in the BF sector
        ]
        if not tps:
            if debug:
                color_msg(f"No tps near the shower", indentLevel=1)
            continue
        if debug:
            color_msg(f"BF{sector} has {len(tps)} TPs to analyze", indentLevel=1)
            color_msg("Analyzing matching...", color="yellow", indentLevel=1)

        # Only showers and TPs that are in the BF sector are analyzed
        showers_tps_analyze_matching(showers, tps, **matching_kwargs)