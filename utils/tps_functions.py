from dtpr.base import Particle
from mpldts.geometry import STATION_CACHE
import numpy as np

Station = STATION_CACHE.get

def compute_x0(tp: Particle, ref_frame="SL13Center") -> float:
    """
    Compute local position of the AM Trigger Primitive referenced to `ref_frame`. 
    Base computation is done in the Sector Reference frame, where the x position can be computed as:

        x0 = -1 * r_ch * tan(phi) * cos(Dphi) * parent_station.face_orientation_factor

    where r_ch is the radial distance to the center of the chamber,
    Dphi is the delta angle formed between the center of the station and the phi sector ray.
    and parent_station.face_orientation_factor is -1 for (wh<0) or (wh==0 and sc in [1, 4, 5, 8, 9, 12, 13]) and 1 otherwise.
    -1 factor is a consequence of the local station frames being inverted respect to the CMS frame (see https://intrepid-hep.github.io/mplDTs/src/patches/dt_station_patch.html).

    :param tp: The AM Trigger Primitive Particle instance.
    :type tp: Particle
    :param ref_frame: The reference frame to which the local x position should be computed. Available options are ["SL13Center" (default), "Station", "SectorRef"].
    :type ref_frame: str
    :return: The x position of the TP referenced to ref_frame.
    :rtype: float
    """
    parent_station = Station(tp.wh, tp.sc, tp.st)

    x_ch, y_ch, _ = parent_station.global_center

    r_ch = np.sqrt(x_ch**2 + y_ch**2) # radial distance to the center of the chamber
    phi_ch = np.arctan2(y_ch, x_ch) # angle of the chamber center in the CMS frame
    sc = 4 if tp.sc == 13 else 10 if tp.sc == 14 else tp.sc # remap sc 13 and 14 to 4 and 10 for the dphi computation
    dphi = phi_ch - (sc - 1) * np.pi / 6 # 30 degrees per sector

    phi_rad = tp.phi / tp.phires_conv # convert phi to radians

    # The x position in the Sector Reference frame is computed as: ()
    x_0 = -1 * r_ch * np.tan(phi_rad) * np.cos(dphi) * parent_station.face_orientation_factor

    if ref_frame != "SectorRef": # transform to the desired reference frame if needed
        x_0 = parent_station.transformer.transform((x_0, 0, 0), from_frame="SectorRef", to_frame=ref_frame)[0]
        if ref_frame == "SL13Center": # additionally move to SL center if tp.sl != 0 (not correlated)
            x_0 -= parent_station.transformer.transform((0, 0, 0), from_frame=ref_frame, to_frame=f"SL{tp.sl}")[0] if tp.sl != 0 else 0

    return x_0

def compute_psi_local(tp: Particle) -> float:
    """
    Compute the local angle of the AM Trigger Primitive referenced to ref_frame.
    Base computation is done in the Sector Reference frame, where the local angle can be computed as:
        psi_local = -1 * parent_station.face_orientation_factor * (phi + phiB)
    
    where phi and phiB are the angles get from the TP indicating: the position of the TP respect to the center of the phi sector, and the
    bending angle of the TP respect to the phi angle ray respectivly. The parent_station.face_orientation_factor is -1 for (wh<0) or (wh==0 and sc in [1, 4, 5, 8, 9, 12, 13]) and 1 otherwise.
    The -1 factor is consecuence of the fact that local station frames are inverted respect to the CMS frame (see https://intrepid-hep.github.io/mplDTs/src/patches/dt_station_patch.html).

    :param tp: The AM Trigger Primitive Particle instance.
    :type tp: Particle
    :return: The local angle of the TP in degrees.
    :rtype: float
    """
    parent_station = Station(tp.wh, tp.sc, tp.st)

    phi_rad = tp.phi / tp.phires_conv # convert phi to radians
    phiB_rad = tp.phiB / tp.phiBres_conv # convert phiB to radians

    psi_local = -1 * parent_station.face_orientation_factor * (phi_rad + phiB_rad) + np.pi # add pi to point the angle outwards the CMS

    return np.degrees(psi_local)