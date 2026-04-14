import warnings
import gc
import matplotlib.pyplot as plt
from numpy import ceil, array, ndarray
from pandas import DataFrame
from typing import Tuple, Optional, List
from collections import deque
from dtpr.base import Event, Particle
from dtpr.utils.functions import color_msg, create_outfolder, get_unique_locs
import numpy as np
import torch
import torch.nn as nn
import os

# Load shower discriminator model
import joblib

_model_path = os.path.join(os.path.dirname(__file__), 'shower_discriminator.pth')
_scaler_path = os.path.join(os.path.dirname(__file__), 'scaler.pkl')

_shower_model = None
_scaler = None


if os.path.exists(_model_path):
    class _ShowerNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.network = nn.Sequential(
                nn.Linear(97, 128), nn.ReLU(), nn.Dropout(0.3),
                nn.Linear(128, 64), nn.ReLU(), nn.Dropout(0.3),
                nn.Linear(64, 32), nn.ReLU(),
                nn.Linear(32, 1)
            )
        def forward(self, x):
            return self.network(x)

    _shower_model = _ShowerNet()
    _shower_model.load_state_dict(torch.load(_model_path, map_location='cpu'))
    _shower_model.eval()

    # Load scaler
    if os.path.exists(_scaler_path):
        _scaler = joblib.load(_scaler_path)
    else:
        warnings.warn("WARNING: scaler.pkl NOT FOUND. NN filtering will produce meaningless output!")



def build_fwshowers(ev: Event, threshold: Optional[List[int]] = None, debug: Optional[bool] = False, 
                   debug_step: Optional[int] = 4, use_NN_filter: Optional[bool] = True, debug_path: Optional[str] = "./results") -> None:
    """
    Emulate the behavior of shower reconstruction in FPGA firmware.
    
    :param ev: The event containing digis to process
    :type ev: Event
    :param threshold: The threshold for shower building
    :type threshold: Optional[int]
    :param debug: Whether to enable debugging outputs
    :type debug: bool
    :param debug_step: The step interval for creating debug plots
    :type debug_step: int
    :param debug_path: The path to save debug plots
    :type debug_path: str
    :return: None, modifies the event by adding fwshowers attribute
    :rtype: None
    """
    if not hasattr(ev, "digis"):
            warnings.warn("'digis' is not included in _PARTICLE_TYPES. Please check the config YAML file. Skipping firmware shower building.")
            return
    #prepare the event to store the showers
    Has_shower_builder=np.zeros((5,15,5,3), dtype=bool)

    setattr(ev, "fwshowers", [])    
    Active_regions=[]  
    MaxBX=max(ev.digis, key=lambda d: d.BX, default=None).BX  
    Hit_vector_SL = np.zeros((5, 15, 5, 3, int(MaxBX+1)), dtype=int)
    Hits_vector_SL = np.zeros((5, 15, 5, 3, 128), dtype=int)
    Lastfired_BX = np.zeros((5, 15, 5, 3, 128), dtype=int)
    hit_BX= np.zeros((5, 15, 5, 3, int(MaxBX+1)), dtype=int)
    Hits_per_Bx= np.zeros((5, 15, 5, 3, int(MaxBX+1)), dtype=int)
    Hits_profile = np.zeros((5, 15, 5, 3, 97, int(MaxBX+1)), dtype=int)
    shower_profile= np.zeros(96, dtype=int)  # to store the shower profile for debug plots
    if ev.digis!=[]:
        for digi in ev.digis:
            wh, sc, st, sl = digi.wh, digi.sc, digi.st, digi.sl   
            #Hotwire_logic;
            if Lastfired_BX[wh+2, sc, st, sl-1, digi.w]!=digi.BX and Lastfired_BX[wh+2, sc, st, sl-1, digi.w]!=digi.BX+1 :  # SL index adjusted to 0,1,2 
                Lastfired_BX[wh+2, sc, st, sl-1, digi.w]=digi.BX
                Active_regions.append((wh, sc, st, sl))
                Hits_profile[wh+2, sc, st, sl-1, digi.w, int(digi.BX)] += 1  # SL index adjusted to 0,1,2
                Hits_per_Bx[wh+2, sc, st, sl-1, int(digi.BX)] += 1  # SL index adjusted to 0,1,2
                Hit_vector_SL[wh+2, sc, st, sl-1, int(digi.BX):int(digi.BX)+16] += 1  # SL index adjusted to 0,1,2
                hit_BX[wh+2, sc, st, sl-1, int(digi.BX)] = int(digi.BX) # array to store the value of the BX
                Hits_vector_SL[wh+2, sc, st, sl-1, digi.w] = 1  # SL index adjusted to 0,1,2
    ish=0        

    for active_region in set(Active_regions):
        #process_layer
        wh, sc, st, sl = active_region
        if  Hit_vector_SL[wh+2, sc, st, sl-1, :].max() >= threshold[st-1]:  # SL index adjusted to 0,1,2
            
            Has_shower_builder[wh+2, sc, st, sl-1] = True
            #maxhits
            nhits=Hit_vector_SL[wh+2, sc, st, sl-1, :].max()
            peak= np.where(Hit_vector_SL[wh+2, sc, st, sl-1, :] == nhits)[0][0] # Get the first index of the peak
            BXs_in_shower=hit_BX[wh+2, sc, st, sl-1, peak-16:peak+1]
            BX=min(BXs_in_shower[BXs_in_shower>0]) if BXs_in_shower[BXs_in_shower>0].size>0 else None
            Hits_inShower=Hits_per_Bx[wh+2, sc, st, sl-1, peak-16:peak+1]
            average_BX_hits=sum((BXs_in_shower*Hits_inShower))/sum(Hits_inShower) if sum(Hits_inShower)>0 else None
            Mehtod1_BX=int(np.mean(BXs_in_shower[BXs_in_shower > 0][:4])) if (BXs_in_shower[BXs_in_shower > 0].size > 0) else None
            Method2_BX = int(np.mean(np.concatenate([BXs_in_shower[BXs_in_shower > 0][:2], BXs_in_shower[BXs_in_shower > 0][-2:]]))) if (BXs_in_shower[BXs_in_shower > 0].size > 0) else None
            # Find non-zero indices in Hits_vector_SL for this region
            wire_indices = np.nonzero(Hits_vector_SL[wh+2, sc, st, sl-1])[0]
            min_wire = int(wire_indices.min()) if wire_indices.size > 0 else None
            max_wire = int(wire_indices.max()) if wire_indices.size > 0 else None  
            digis=[]
            for hits in ev.digis:
                if hits.wh==wh and hits.sc==sc and hits.st==st and hits.sl==sl and hits.BX>=peak-16 and hits.BX<=peak:
                    digis.append(hits)
            _shower = Particle(index=ish, wh=wh, sc=sc, st=st, nDigis=nhits, BX=BX, name="Shower")
            _shower.average_BX_hits = average_BX_hits
            _shower.min_wire = min_wire
            _shower.digis = digis
            _shower.max_wire = max_wire       
            _shower.shower_profile = Hits_profile[wh+2, sc, st, sl-1, :, peak-16:peak+1].sum(axis=1)  # SL index adjusted to 0,1,2
            _shower.sl = sl
            _shower.BXM1=Mehtod1_BX
            _shower.BXM2=Method2_BX
            _shower.matched_tps = []  # Initialize matched_tps
            if use_NN_filter and _shower_model is not None and _scaler is not None:
                # reshape to (1, 97) and scale
                profile_np = _shower.shower_profile.astype(np.float32).reshape(1, -1)
                profile_scaled = _scaler.transform(profile_np)
                # convert to torch tensor
                x = torch.tensor(profile_scaled, dtype=torch.float32)
                # model prediction
                with torch.no_grad():
                    logits = _shower_model(x)
                    prob = torch.sigmoid(logits).item()
                _shower.prediction_value = prob
                _shower.isnot_dropped = prob > 0.5

            else:
                # fallback: no NN, never drop shower
                _shower.prediction_value = None
                _shower.isnot_dropped = True                            
        
            ev.fwshowers.append(_shower)

def _process_superlayer(ev_BXs: List[int], digis_df: DataFrame, threshold: int) -> Tuple[bool, int, int, ndarray]:
    """
    Detect a shower in a superlayer by counting hits following firmware rules.
    
    :param ev_BXs: The set of BXs (bunch crossings) in the event
    :type ev_BXs: List[int]
    :param digis_df: The dataframe containing digi information
    :type digis_df: DataFrame
    :param threshold: The threshold for shower detection
    :type threshold: int
    :return: Tuple containing (shower detected flag, maximum hit count, BX of max hits, hit history)
    :rtype: Tuple[bool, int, int, ndarray]
    """
    wires_buff = deque()  # Use deque such as FIFO
    num_hits_last_16Bxs = deque(maxlen=16)  # Use deque to count hits, in BXs larger than 16 it will start to delete elements
    showered = False
    num_hits_history = []

    min_bx, max_bx = min(ev_BXs), max(ev_BXs)
    hot_w = set()  # hot wires is reset each two BXs

    for bx in range(min_bx, max_bx + 1):
        if (bx - min_bx) % 2 == 0:
            hot_w.clear()  # reset hot wires every two BXs

        wires_buff.extend((w, bx) for w in digis_df.loc[digis_df["BX"] == bx, "w"])  # hits of this bx

        # Remove hits older than 4 BXs
        while wires_buff and bx - wires_buff[0][1] > 4:
            wires_buff.popleft()

        hits_counter = 0
        for _ in range(8):  # Just count until reaching 8 wires.
            if not wires_buff:
                break
            w, _ = wires_buff.popleft()
            if w in hot_w:  # if the wire is already hot from previous BX, ignore it
                continue
            hot_w.add(w)
            hits_counter += 1  # count hits

        num_hits_last_16Bxs.append(hits_counter)
        num_hits_history.append([bx, sum(num_hits_last_16Bxs)])  # this is just to debug producing plots
        if sum(num_hits_last_16Bxs) >= threshold:
            showered = True

    num_hits_history = array(num_hits_history)
    nHits = num_hits_history[:, 1].max()
    sBX = num_hits_history[num_hits_history[:, 1] == nHits][0, 0]
    return showered, nHits, sBX, num_hits_history


def build_real_showers(ev: Event, threshold: Optional[int] = None,Filtersimhits:Optional[bool] = True, debug: Optional[bool] = False) -> None:
    """
    Build real showers based on simhit information.
    
    :param ev: The event containing simhits to process
    :type ev: Event
    :param threshold: The threshold for shower building
    :type threshold: Optional[int]
    :param Filtersimhits: Whether to filter simhits based on corresponding digis
    :type Filtersimhits: Optional[bool]
    :param debug: Whether to enable debugging outputs
    :type debug: bool
    :return: None, modifies the event by adding realshowers attribute
    :rtype: None
    """

    if not hasattr(ev, "simhits"):
        warnings.warn("'simhits' is not included in _PARTICLE_TYPES. Please check the config YAML file. Skipping real shower building.")
        return

    ev.realshowers = []
    thr = 8 if threshold is None else threshold

    simhits_locs = get_unique_locs(particles=ev.simhits, loc_ids=["wh", "sc", "st", "sl"])
    digis_locs = get_unique_locs(particles=ev.digis, loc_ids=["wh", "sc", "st", "sl"])
    indexs = simhits_locs.union(digis_locs)

    for wh, sc, st, sl in indexs:
        simhits_sdf = DataFrame([simhit.__dict__ for simhit in ev.filter_particles("simhits", wh=wh, sc=sc, st=st, sl=sl)])
        digis_sdf = DataFrame([digi.__dict__ for digi in ev.filter_particles("digis", wh=wh, sc=sc, st=st, sl=sl)])
        
        # Filter simhits to only include those that have a corresponding digi at the same (l, w) location
        if Filtersimhits:
            if not simhits_sdf.empty and not digis_sdf.empty:
                # Create sets of (l, w) coordinates for efficient lookup
                digi_coords = set(zip(digis_sdf['l'], digis_sdf['w']))
                simhits_sdf = simhits_sdf[simhits_sdf.apply(lambda row: (row['l'], row['w']) in digi_coords, axis=1)]
            elif digis_sdf.empty:
                # If there are no digis, clear simhits_sdf as there are no matching coordinates
                simhits_sdf = DataFrame()
        
        



        _build_shower = False

        if not simhits_sdf.empty:
            simhits_sdf = simhits_sdf[["l", "w", "particle_type"]].drop_duplicates()
            # conditions...
            # pass the threshold of hits
            pass_thr = len(simhits_sdf.drop_duplicates(["l", "w"])) >= thr
            # at least 3 muon hits
            are_muons_hits = len(simhits_sdf.loc[simhits_sdf["particle_type"].abs() == 13]) >= 3
            # at least 1 electron hit
            are_electron_hits = len(simhits_sdf.loc[simhits_sdf["particle_type"].abs() == 11]) > 0
            # hits are spread out in the chamber
            spread = simhits_sdf["w"].std()**2 > 1
            # are duplicated matched segments
            matched_segments = [seg for gm in ev.genmuons for seg in getattr(gm, 'matched_segments', [])]
            if matched_segments:
                are_duplicated_segments = len(matched_segments) > len(get_unique_locs(matched_segments, loc_ids=["wh", "sc", "st"]))
            else:
                are_duplicated_segments = False # -- for G4 DTNtuples there are no segments

            if pass_thr:
                if debug: color_msg(f'spread: {spread} --> {simhits_sdf["w"].std()**2}', "purple", indentLevel=2)
                if are_muons_hits and are_electron_hits and spread:
                    shower_type = 1
                elif are_electron_hits and spread:
                    shower_type = 2
                elif are_duplicated_segments:
                    shower_type = 3
                else:
                    continue
                _build_shower = True

        # elif not digis_sdf.empty:
        #     digis_sdf = digis_sdf[["l", "w"]].drop_duplicates()
        #     # conditions...
        #     pass_thr = len(digis_sdf) >= thr
        #     # hits are spread out in the chamber
        #     std_ = digis_sdf["w"].std()**2
        #     spread = std_ > 1 and std_ < 5
        #     if debug: color_msg(f'spread: {spread} --> {std_}', "purple", indentLevel=2)
        #     if debug: color_msg(f'iqr: {digis_sdf["w"].quantile(0.25)}, {digis_sdf["w"].quantile(0.75)}', "purple", indentLevel=2)
        #     if len(digis_sdf) >= thr and spread:
        #         shower_type = 4
        #         _build_shower = True
        
        if _build_shower:
            _index = ev.realshowers[-1].index + 1 if ev.realshowers else 0
            _shower = Particle(index=_index, wh=wh, sc=sc, st=st, name="Shower") 
            _shower.shower_type = shower_type
            _shower.sl = sl
            _shower.nsimhits = len(simhits_sdf.drop_duplicates(["l", "w"])) if not simhits_sdf.empty else 0
            _shower.ndigis = len(digis_sdf.drop_duplicates(["l", "w"])) if not digis_sdf.empty else 0
            _shower.min_wire = int(min(simhits_sdf["w"].min(), digis_sdf["w"].min())) if not simhits_sdf.empty and not digis_sdf.empty else (int(simhits_sdf["w"].min()) if not simhits_sdf.empty else int(digis_sdf["w"].min()))
            _shower.max_wire = int(max(simhits_sdf["w"].max(), digis_sdf["w"].max())) if not simhits_sdf.empty and not digis_sdf.empty else (int(simhits_sdf["w"].max()) if not simhits_sdf.empty else int(digis_sdf["w"].max()))
            ev.realshowers.append(_shower)
            if debug:
                color_msg(
                    f'Realshower detected in (wh, sc, st, sl): ({wh}, {sc}, {st}, {sl}) - type: {shower_type}',
                    "green",
                    indentLevel=2,
                )

def analyze_fwshowers(ev: Event) -> None:
    """
    Determine if firmware showers are real by comparing with real showers.
    
    :param ev: The event containing fwshowers and realshowers to analyze
    :type ev: Event
    :return: None, modifies each fwshower by adding is_true_shower attribute
    :rtype: None
    """
    if not hasattr(ev, "fwshowers") or not hasattr(ev, "realshowers"):
        warnings.warn("Either 'fwshowers' or 'realshowers' are not included in _PARTICLE_TYPES. Please check the config YAML file. Skipping shower analysis.")
        return

    for shower in ev.fwshowers:   
        wh, sc, st , sl = shower.wh, shower.sc, shower.st, shower.sl
        if ev.filter_particles("realshowers", wh=wh, sc=sc, st=st, sl=sl):
            shower.is_true_shower = True
        else:
            shower.is_true_shower = False
