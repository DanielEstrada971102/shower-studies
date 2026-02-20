from dtpr.base import Particle
from dtpr.utils.functions import append_to_matched_list
from numpy import cos, arccos, arctan2, pi, degrees
from typing import Optional
from mpldts.geometry.station import STATION_CACHE

Station = STATION_CACHE.get

def match_offline_AMtp(segment: Particle, tp: Particle, max_dPhi: Optional[float] = 0.1) -> None:
    """
    Match an offline segment to an AM trigger primitive based on dPhi.

    :param segment: The segment to match.
    :type segment: Particle
    :param tp: The trigger primitive to match.
    :type tp: Particle
    :param max_dPhi: The maximum dPhi for matching.
    :type max_dPhi: float
    :return: None, modifies the segment and tp by adding matched objects to their lists
    :rtype: None
    """
    if any([not hasattr(segment, key) for key in ['wh', 'sc', 'st', 'phi']]):
        raise AttributeError("Segment must have 'wh', 'sc', 'st', 'phi', and 'phires_conv' attributes.")
    if any([not hasattr(tp, key) for key in ['wh', 'sc', 'st', 'phi', 'phires_conv', 'BX']]):
        raise AttributeError("Trigger primitive must have 'wh', 'sc', 'st', 'phi', 'phires_conv', and 'BX' attributes.")

    seg_sc = segment.sc
    if seg_sc == 13: 
        seg_sc = 4
    elif seg_sc == 14:
        seg_sc = 10

    tp_sc = tp.sc
    if tp_sc == 13: 
        tp_sc = 4 
    elif tp_sc == 14: 
        tp_sc = 10

    # Match only if TP and segment are in the same chamber
    if tp.wh == segment.wh and tp_sc == seg_sc and tp.st == segment.st:
        # In this case, they are in the same chamber: match dPhi
        # -- Use a conversion factor to express phi in radians
        trigGlbPhi = tp.phi / tp.phires_conv + pi / 6 * (tp.sc - 1)
        dphi = abs(arccos(cos(segment.phi - trigGlbPhi)))
        matches = dphi < max_dPhi and tp.BX == 0 # <--- deberia haber un dBX?
        if matches:
            append_to_matched_list(segment, 'matched_tps', tp)
            append_to_matched_list(tp, 'matched_segments', segment)

            if hasattr(segment, 'matched_genmuons'):
                for gm in segment.matched_genmuons:
                    append_to_matched_list(gm, 'matched_tps', tp)
                    append_to_matched_list(tp, 'matched_genmuons', gm)

def compute_offseg_psi(segment: Particle) -> float:
    """
    Compute the psi angle for an offline segment.

    :param segment: The segment for which to compute psi.
    :type segment: Particle
    :return: The computed psi angle in degrees.
    :rtype: float
    """
    
    parent = Station(wh=segment.wh, sc=segment.sc, st=segment.st)
    y_sl1 = parent.super_layer(1).local_center[2]
    y_sl3 = parent.super_layer(3).local_center[2]
    x_sl1 = segment.pos_locx_sl1
    x_sl3 = segment.pos_locx_sl3
    psi = arctan2(x_sl3 - x_sl1, -1 * (y_sl3 - y_sl1))
    return degrees(psi)