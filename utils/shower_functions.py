import warnings
import gc
import matplotlib.pyplot as plt
from numpy import ceil, array, ndarray
from pandas import DataFrame
from typing import Tuple, Optional, List, Union
from collections import deque
from dtpr.base import Event, Particle
from dtpr.utils.functions import color_msg, get_unique_locs
import numpy as np
import torch
import torch.nn as nn
import os
import joblib
from sklearn.cluster import DBSCAN


def build_fwshowers(ev: Event, threshold: Optional[List[int]] = None, name: Optional[str] = "fwshowers",
                    debug: Optional[bool] = False, debug_step: Optional[int] = 4, debug_path: Optional[str] = "./results") -> None:
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
        warnings.warn(
            "'digis' is not included in _PARTICLE_TYPES. Please check the config YAML file. "
            "Skipping firmware shower building."
        )
        return

    # Handle missing threshold (keep behavior flexible; adjust defaults if your project expects otherwise)
    if threshold is None:
        # Typical st is 1..4 in many DT-like conventions; you used threshold[st-1]
        # Provide a safe default of zeros (i.e., everything passes) rather than crashing.
        threshold = [8, 8, 8, 8]

    # Fast exit
    if not ev.digis:
        return

    # Workspace arrays
    Has_shower_builder = np.zeros((5, 15, 5, 3), dtype=bool)

    MaxBX = int(max(ev.digis, key=lambda d: d.BX).BX)
    window = 16
    bx_len = MaxBX + window + 1  # +1 for the end-marker at bx+window

    # Diff array for windowed hit accumulation, then cumsum to materialize
    Hit_vector_SL_diff = np.zeros((5, 15, 5, 3, bx_len), dtype=np.int32)

    # Per-wire occupancy in a region (for min/max wire)
    Hits_vector_SL = np.zeros((5, 15, 5, 3, 128), dtype=np.uint8)

    # Hotwire gating: last accepted BX per (region, wire)
    # Sentinel avoids incorrectly rejecting BX=0
    Lastfired_BX = np.full((5, 15, 5, 3, 128), -999, dtype=np.int16)

    # Per-BX hit counts (used to find earliest BX in the shower window)
    Hits_per_Bx = np.zeros((5, 15, 5, 3, MaxBX + 1), dtype=np.int16)

    # Wire profile vs BX for each region (97 wires in your code)
    Hits_profile = np.zeros((5, 15, 5, 3, 97, MaxBX + 1), dtype=np.int16)

    # Track which regions got any accepted digi
    Active_regions: set[tuple[int, int, int, int]] = set()

    # Pre-index digis by region so we don't scan ev.digis for each shower
    # (still filter by BX window later)
    region_to_digis: dict[tuple[int, int, int, int], list] = {}

    # -------------------------
    # First pass: hotwire filter + fill histograms
    # -------------------------
    for digi in ev.digis:
        wh, sc, st, sl = int(digi.wh), int(digi.sc), int(digi.st), int(digi.sl)
        iwh = wh + 2
        isl = sl - 1
        w = int(digi.w)
        bx = int(digi.BX)

        # # Basic bounds safety (optional; remove if you trust inputs and want max speed)
        # if not (0 <= iwh < 5 and 0 <= sc < 15 and 0 <= st < 5 and 0 <= isl < 3):
        #     continue
        # if not (0 <= w < 128):
        #     continue
        # if bx < 0 or bx > MaxBX:
        #     continue

        last = int(Lastfired_BX[iwh, sc, st, isl, w])

        # Hotwire logic: discard if there's already a hit in BX or BX-1 for same (region, wire)
        if last == bx or last == bx - 1:
            continue

        Lastfired_BX[iwh, sc, st, isl, w] = bx
        Active_regions.add((wh, sc, st, sl))

        # Index digis by region for later shower digi attachment
        region_to_digis.setdefault((wh, sc, st, sl), []).append(digi)

        # Fill profiles/counts
        if w < 97:
            Hits_profile[iwh, sc, st, isl, w, bx] += 1
        Hits_per_Bx[iwh, sc, st, isl, bx] += 1
        Hits_vector_SL[iwh, sc, st, isl, w] = 1

        # Range add for windowed hit vector: +1 at bx, -1 at bx+window
        Hit_vector_SL_diff[iwh, sc, st, isl, bx] += 1
        Hit_vector_SL_diff[iwh, sc, st, isl, bx + window] -= 1

    # Materialize 16-wide windowed hit vector for all regions at once
    Hit_vector_SL = np.cumsum(Hit_vector_SL_diff, axis=-1)[..., : MaxBX + 1]

    # -------------------------
    # Second pass: build showers per active region
    # -------------------------
    ish = 0
    showers = []
    for (wh, sc, st, sl) in Active_regions:
        iwh = wh + 2
        isl = sl - 1

        # Guard threshold indexing (your code assumes st starts at 1)
        thr_idx = st - 1
        if thr_idx < 0 or thr_idx >= len(threshold):
            # If station indexing isn't as expected, skip safely
            continue

        vec = Hit_vector_SL[iwh, sc, st, isl, :]
        nhits = int(vec.max())
        if nhits < int(threshold[thr_idx]):
            continue

        Has_shower_builder[iwh, sc, st, isl] = True

        # Find the first BX index with the maximum windowed hit count
        peak = int(np.flatnonzero(vec == nhits)[0])

        # Determine earliest BX in [peak-15, peak] that has any raw hits (Hits_per_Bx > 0)
        lo = max(0, peak - (window - 1))
        hi = peak  # inclusive
        raw_window = Hits_per_Bx[iwh, sc, st, isl, lo : hi + 1]
        rel = np.flatnonzero(raw_window > 0)
        BX = int(lo + rel[0]) if rel.size else None

        # Min/max wire in region
        wire_indices = np.nonzero(Hits_vector_SL[iwh, sc, st, isl])[0]
        min_wire = int(wire_indices.min()) if wire_indices.size else None
        max_wire = int(wire_indices.max()) if wire_indices.size else None

        # Attach digis only from this region and BX window (avoid scanning all digis)
        region_digis = region_to_digis.get((wh, sc, st, sl), [])
        shower_digis = [
            d for d in region_digis if lo <= int(d.BX) <= hi
        ]
        shower_digis_layer = [d.l for d in shower_digis]
        shower_digis_tdc = [d.time for d in shower_digis]

        _shower = Particle(index=ish, wh=wh, sc=sc, st=st, nDigis=nhits, BX=BX, name="Shower")
        _shower.min_wire = min_wire
        _shower.max_wire = max_wire
        _shower.digis = shower_digis
        _shower.digis_tdc= shower_digis_tdc
        _shower.digis_layer = shower_digis_layer
        _shower.sl = sl

        # Shower profile summed over BX window (axis=BX)
        # Your Hits_profile has 97 wires; you used `:` before, keep that:
        _shower.profile = Hits_profile[iwh, sc, st, isl, :, lo : hi + 1].sum(axis=1)

        _shower.matched_tps = []

        showers.append(_shower)
        ish += 1

    setattr(ev, name, showers)

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


def build_real_showers(
        ev: Event, 
        threshold: Union[Optional[int], Optional[list]]= 8,
        include_sl2 = False, Filtersimhits:Optional[bool] = True,
        resultColName: Optional[str] = "realshowers",\
        simhits2use: Optional[str] = "simhits",
        digis2use: Optional[str] = "digis",
        types2analyze: Optional[List[int]] = [1, 2, 3, 4],
        debug: Optional[bool] = False) -> None:
    """
    Build real showers based on simhit information.
    
    :param ev: The event containing simhits to process
    :type ev: Event
    :param threshold: The threshold for shower building
    :type threshold: Optional[int]
    :param Filtersimhits: Whether to filter simhits based on corresponding digis
    :type Filtersimhits: Optional[bool]
    :param resultColName: The name of the column to store the realshowers
    :type resultColName: Optional[str]
    :param debug: Whether to enable debugging outputs
    :type debug: bool
    :return: None, modifies the event by adding realshowers attribute
    :rtype: None
    """

    if not hasattr(ev, simhits2use):
        warnings.warn(f"'{simhits2use}' is not included in _PARTICLE_TYPES. Please check the config YAML file. Skipping real shower building.")
        return

    setattr(ev, resultColName, [])  # initialize the realshowers list in the event
    
    if isinstance(threshold, list):
        if len(threshold) != 4:
            raise ValueError("Threshold list must have 4 elements corresponding to stations 1-4.")
    else:
        threshold = [threshold] * 4  # if a single int is provided, use it for all stations

    simhits_locs = get_unique_locs(particles=getattr(ev, simhits2use), loc_ids=["wh", "sc", "st", "sl"])
    digis_locs = get_unique_locs(particles=getattr(ev, digis2use), loc_ids=["wh", "sc", "st", "sl"])
    indexs = simhits_locs.union(digis_locs)

    for wh, sc, st, sl in indexs:
        if sl == 2 and not include_sl2:
            continue
        simhits_sdf = DataFrame([simhit.__dict__ for simhit in getattr(ev, simhits2use) if simhit.wh == wh and simhit.sc == sc and simhit.st == st and simhit.sl == sl])
        digis_sdf = DataFrame([digi.__dict__ for digi in getattr(ev, digis2use) if digi.wh == wh and digi.sc == sc and digi.st == st and digi.sl == sl])

        # Filter simhits to only include those that have a corresponding digi at the same (l, w) location
        if Filtersimhits:
            if not simhits_sdf.empty and not digis_sdf.empty:
                # Create sets of (l, w) coordinates for efficient lookup
                digi_coords = set(zip(digis_sdf['l'], digis_sdf['w']))
                simhits_sdf = simhits_sdf[simhits_sdf.apply(lambda row: (row['l'], row['w']) in digi_coords, axis=1)]
            elif digis_sdf.empty:
                # If there are no digis, clear simhits_sdf as there are no matching coordinates
                simhits_sdf = DataFrame()

        thr = threshold[st-1] 
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
            spread = max(simhits_sdf["w"]) - min(simhits_sdf["w"]) >= 2 #simhits_sdf["w"].std()**2 > 1
            # are duplicated matched segments
            matched_segments = [seg for gm in ev.genmuons for seg in getattr(gm, 'matched_segments', [])]
            if matched_segments:
                are_duplicated_segments = len(matched_segments) > len(get_unique_locs(matched_segments, loc_ids=["wh", "sc", "st"]))
            else:
                are_duplicated_segments = False # -- for G4 DTNtuples there are no segments

            if pass_thr:
                if debug: color_msg(f'spread: {spread} --> {simhits_sdf["w"].std()**2}', "purple", indentLevel=2)
                if 1 in types2analyze and are_muons_hits and are_electron_hits and spread:
                    shower_type = 1
                elif 2 in types2analyze and are_electron_hits and spread:
                    shower_type = 2
                elif 3 in types2analyze and are_duplicated_segments:
                    shower_type = 3
                else:
                    continue
                _build_shower = True

        elif not digis_sdf.empty:
            digis_sdf = digis_sdf[["l", "w"]].drop_duplicates()
            # conditions...
            pass_thr = len(digis_sdf) >= thr
            # hits are spread out in the chamber
            d = max(digis_sdf["w"]) - min(digis_sdf["w"])
            spread = d > 4 and d < 10
            if 4 in types2analyze and len(digis_sdf) >= thr and spread:
                shower_type = 4
                _build_shower = True
        
        if _build_shower:
            _realshowers_coll = getattr(ev, resultColName)
            _index = _realshowers_coll[-1].index + 1 if _realshowers_coll else 0
            _shower = Particle(index=_index, wh=wh, sc=sc, st=st, name="Shower") 
            _shower.shower_type = shower_type
            _shower.sl = sl
            _shower.nsimhits = len(simhits_sdf.drop_duplicates(["l", "w"])) if not simhits_sdf.empty else 0
            _shower.ndigis = len(digis_sdf.drop_duplicates(["l", "w"])) if not digis_sdf.empty else 0
            _shower.min_wire = int(min(simhits_sdf["w"].min(), digis_sdf["w"].min())) if not simhits_sdf.empty and not digis_sdf.empty else (int(simhits_sdf["w"].min()) if not simhits_sdf.empty else int(digis_sdf["w"].min()))
            _shower.max_wire = int(max(simhits_sdf["w"].max(), digis_sdf["w"].max())) if not simhits_sdf.empty and not digis_sdf.empty else (int(simhits_sdf["w"].max()) if not simhits_sdf.empty else int(digis_sdf["w"].max()))
            _realshowers_coll.append(_shower)
            if debug:
                color_msg(
                    f'Realshower detected in (wh, sc, st, sl): ({wh}, {sc}, {st}, {sl}) - type: {shower_type}',
                    "green",
                    indentLevel=2,
                )


def build_real_showers_by_clustering(
        ev: Event,
        threshold: Union[Optional[int], Optional[list[int]]] = 8,
        include_sl2: bool = False,
        resultColName: Union[Optional[str], str] = "realshowers",
        eps: Union[Optional[float], Optional[list[float]]] = 1.5, 
        min_samples: Union[Optional[int], Optional[list[int]]] = 4,
        digis2use: Union[Optional[str], str] = "digis",
        debug: Optional[bool] = False
        ) -> None:
    """
    Build real showers based ONLY on digi information using DBSCAN clustering.
    Focuses purely on detecting any dense cluster with hits >= threshold.
    """

    if not hasattr(ev, digis2use):
        warnings.warn(f"'{digis2use}' is not included in the event. Skipping real shower building.")
        return

    setattr(ev, resultColName, [])

    if isinstance(threshold, list):
        if len(threshold) != 4:
            raise ValueError("Threshold list must have 4 elements corresponding to stations 1-4.")
    else:
        threshold = [threshold] * 4

    if isinstance(eps, list):
        if len(eps) != 4:
            raise ValueError("Eps list must have 4 elements corresponding to stations 1-4.")
    else:
        eps = [eps] * 4

    if isinstance(min_samples, list):
        if len(min_samples) != 4:
            raise ValueError("min_samples list must have 4 elements corresponding to stations 1-4.")
    else: 
        min_samples = [min_samples] * 4

    # Obtenemos las localizaciones únicas basadas solo en digis
    digis_locs = get_unique_locs(particles=getattr(ev, digis2use, []), loc_ids=["wh", "sc", "st", "sl"])

    for wh, sc, st, sl in digis_locs:
        if sl == 2 and not include_sl2:
            continue

        # Filtrar digis en esta cámara/supercapa
        digis_filtrados = ev.filter_particles(digis2use, wh=wh, sc=sc, st=st, sl=sl)
        if not digis_filtrados:
            continue

        digis_sdf = DataFrame([digi.__dict__ for digi in digis_filtrados])
        digis_sdf = digis_sdf[["l", "w"]].drop_duplicates()

        # Si el número total de digis en la capa no alcanza  el threshold, no perdemos tiempo ejecutando DBSCAN.
        if len(digis_sdf) < threshold[st-1]:
            continue

        # --- FASE DBSCAN ---
        X = digis_sdf[["l", "w"]].values

        # Scale integer indices to physical dimensions (in cm)
        # X[:, 0] is Layer (1.3 cm) and X[:, 1] is Wire (4.2 cm)
        X_physical = X * np.array([1.3, 4.2])
        
        # 2.Use a physical eps. 
        # 5.0 cm allows for adjacent and diagonal cell connections
        physical_eps = 4.2 * eps[st - 1]  # Scale by eps factor for tuning sensitivity (e.g., 1.5 means 1.5 wires distance in physical space) 
        
        # Run DBSCAN on the physical coordinates
        db = DBSCAN(eps=physical_eps, min_samples=min_samples[st - 1]).fit(X_physical)
        labels = db.labels_

        unique_labels = set(labels) - {-1}

        _build_shower = False
        max_cluster_size = 0
        final_min_w, final_max_w = 0, 0

        # Iteramos sobre los clusters encontrados buscando superar el Threshold
        for label in unique_labels:
            cluster_mask = (labels == label)
            cluster_elements = X[cluster_mask]
            cluster_size = len(cluster_elements)

            # Si este cluster específico tiene >= 8 hits
            if cluster_size >= threshold[st - 1]:
                _build_shower = True
                
                # Si en una misma cámara hay varios clusters grandes, guardamos 
                # las propiedades del más masivo.
                if cluster_size > max_cluster_size:
                    max_cluster_size = cluster_size
                    cluster_wires = cluster_elements[:, 1]
                    final_min_w, final_max_w = int(cluster_wires.min()), int(cluster_wires.max())

        # --- CONSTRUCCIÓN DEL OBJETO SHOWER ---
        if _build_shower:
            _realshowers_coll = getattr(ev, resultColName)
            _index = _realshowers_coll[-1].index + 1 if _realshowers_coll else 0
            
            _shower = Particle(index=_index, wh=wh, sc=sc, st=st, name="Shower") 
            _shower.shower_type = 10  # ID para cluster denso (>= threshold)
            _shower.sl = sl
            _shower.nsimhits = 0      # Solo usamos digis
            _shower.ndigis = int(max_cluster_size)
            _shower.min_wire = final_min_w
            _shower.max_wire = final_max_w
            
            _realshowers_coll.append(_shower)
            
            if debug:
                color_msg(
                    f'Realshower (DBSCAN) detected in (wh, sc, st, sl): ({wh}, {sc}, {st}, {sl}) '
                    f'- size: {max_cluster_size} hits - wire span: [{final_min_w}, {final_max_w}]',
                    "green",
                    indentLevel=2,
                )


def analyze_fwshowers(ev: Event, showers2use_name: str = "fwshowers", realshowers2use_name: str = "realshowers") -> None:
    """
    Determine if firmware showers are real by comparing with real showers.
    
    :param ev: The event containing fwshowers and realshowers to analyze
    :type ev: Event
    :return: None, modifies each fwshower by adding is_true_shower attribute
    :rtype: None
    """
    if not hasattr(ev, showers2use_name) or not hasattr(ev, realshowers2use_name):
        warnings.warn(f"Either '{showers2use_name}' or '{realshowers2use_name}' are not included in _PARTICLE_TYPES. Please check the config YAML file. Skipping shower analysis.")
        return

    for shower in getattr(ev, showers2use_name):   
        wh, sc, st , sl = shower.wh, shower.sc, shower.st, shower.sl
        if ev.filter_particles(realshowers2use_name, wh=wh, sc=sc, st=st, sl=sl):
            shower.is_true_shower = True
        else:
            shower.is_true_shower = False

nn_cache = {}

def drop_fwshowers(ev: Event, showers2use_name: str = "fwshowers") -> None:
    """
    Drop firmware showers that are predicted as not real by the NN filter.
    
    :param ev: The event containing fwshowers to filter
    :type ev: Event
    :return: None, modifies the event by removing fwshowers that are predicted as not real
    :rtype: None
    """
    if not hasattr(ev, showers2use_name):
        raise AttributeError(f"ERROR: '{showers2use_name}' attribute not found in event. Please check the config YAML file and ensure that the shower builder is correctly configured to create '{showers2use_name}'.")
    showers = getattr(ev, showers2use_name)
    if not showers:
        return

    _shower_model = None
    _scaler = None

    if not nn_cache:
        # Load shower discriminator model
        _model_path = os.path.join(os.path.dirname(__file__), 'shower_discriminator.pth')
        _scaler_path = os.path.join(os.path.dirname(__file__), 'scaler.pkl')

        if not os.path.exists(_model_path):
            raise FileNotFoundError(f"ERROR: shower_discriminator.pth NOT FOUND at {_model_path}. NN filtering cannot be applied!")

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

        nn_cache['model'] = _shower_model
        nn_cache['scaler'] = _scaler
    else:
        _shower_model = nn_cache.get('model')
        _scaler = nn_cache.get('scaler')

    if _shower_model is None:
        raise RuntimeError("ERROR: Shower discriminator model failed to load. NN filtering cannot be applied!")

    showers_to_keep = []

    for _shower in showers:
        profile_np = np.array(_shower.profile).astype(np.float32).reshape(1, -1)
        profile_scaled = _scaler.transform(profile_np) if _scaler else profile_np  # If scaler failed to load, use unscaled features (not recommended)
        x = torch.tensor(profile_scaled, dtype=torch.float32)
        with torch.no_grad():
            logits = _shower_model(x)
            prob = torch.sigmoid(logits).item()
        _shower.prediction_value = prob
        _shower.isnot_dropped = prob > 0.5
        if _shower.isnot_dropped:
            showers_to_keep.append(_shower)

    setattr(ev, showers2use_name, showers_to_keep)


def drop_showers_by_thresholds(ev: Event, thresholds: list[int], showers2use_name: str = "fwshowers") -> None:
    """
        NOT USE AS A PREPROCESSOR, IF ANY PARTICLE HAS REFERENCE TO THE SHOWER OBJECT, THIS FUNCTION WILL NOT DELETE THE SHOWER OBJECT IN THAT REFERENCE, BUT JUST DROP THE SHOWER FROM THE SHOWER COLLECTION.
    Drop showers that do not meet a required threshold by station type
    
    :param ev: The event containing showers to filter
    :type ev: Event
    :param thresholds: A list of property thresholds for each station (e.g., [9, 8, 8, 7])
    :type thresholds: list[int]
    :return: None, modifies the event by removing showers that do not meet the thresholds
    :rtype: None
    """
    if not hasattr(ev, showers2use_name):
        raise AttributeError(f"ERROR: '{showers2use_name}' attribute not found in event. Please check the config YAML file and ensure that the shower builder is correctly configured to create '{showers2use_name}'.")
    
    if thresholds is None:
        warnings.warn("No thresholds provided for drop_shower_by_thresholds. No showers will be dropped.")
        return
    if not isinstance(thresholds, list):
        warnings.warn("Thresholds must be provided as a list of integers corresponding to stations 1-4. No showers will be dropped.")
        return
    if len(thresholds) != 4:
        warnings.warn("Thresholds list must have 4 elements corresponding to stations 1-4.")
        return

    showers = getattr(ev, showers2use_name)
    showers_to_keep = []
    for shower in showers:
        if shower.nDigis >= thresholds[shower.st - 1]:
            showers_to_keep.append(shower)    
    setattr(ev, showers2use_name, showers_to_keep)


def compute_effective_nDigis(shower, keys: list[str]) -> int:
    """
    Compute the effective nDigis for a shower by counting unique digis based on specified keys.
    
    :param shower: The shower object containing digis to analyze
    :type shower: Particle
    :param keys: The keys to consider for determining effective nDigis (e.g., ['l', 'w'])
    :type keys: list[str]
    :return: The effective nDigis count
    :rtype: int
    """
    if any(not hasattr(shower, key) for key in keys):
        raise AttributeError(f"ERROR: Shower does not have the required keys {keys} to compute effective nDigis. Please check the shower object and ensure it has the necessary attributes.")
    
    shower_digis = DataFrame({key: getattr(shower, key) for key in keys})
    dropped_duplicates = shower_digis.drop_duplicates()
    return len(dropped_duplicates)

def drop_showers_by_effective_nDigis(
        ev: Event,
        keys: list[str],
        threshold: Union[Optional[int], Optional[list[int]]],
        showers2use_name: str = "fwshowers",
        ) -> None:
    """
    NOT USE AS A PREPROCESSOR, IF ANY PARTICLE HAS REFERENCE TO THE SHOWER OBJECT, THIS FUNCTION WILL NOT DELETE THE SHOWER OBJECT IN THAT REFERENCE, BUT JUST DROP THE SHOWER FROM THE SHOWER COLLECTION.
    Drop showers that do not meet a required effective nDigis threshold, where effective nDigis are the digis after drop duplicates bythe keys indicated.

    :param ev: The event containing showers to filter
    :type ev: Event
    :param keys: The keys to consider for determining effective nDigis (e.g., ['l', 'w'])
    :type keys: list[str]
    :param showers2use_name: The name of the shower collection to filter
    :type showers2use_name: str
    :param threshold: The effective nDigis threshold to apply
    :type threshold: Optional[int]
    :return: None, modifies the event by removing showers that do not meet the effective nDigis threshold
    :rtype: None
    """
    if not hasattr(ev, showers2use_name):
        raise AttributeError(f"ERROR: '{showers2use_name}' attribute not found in event. Please check the config YAML file and ensure that the shower builder is correctly configured to create '{showers2use_name}'.")
    
    if threshold is None:
        warnings.warn("No threshold provided for drop_showers_by_effective_nDigis. No showers will be dropped.")
        return
    if isinstance(threshold, list):
        if len(threshold) != 4:
            warnings.warn("Threshold list must have 4 elements corresponding to stations 1-4. No showers will be dropped.")
            return
    elif isinstance(threshold, int):
        threshold = [threshold] * 4
    
    showers = getattr(ev, showers2use_name)
    if not showers:
        return
    if any(not hasattr(showers[-1], key) for key in keys):
        raise AttributeError(f"ERROR: Showers have not the required keys {keys} to compute effective nDigis. Please check the shower objects and ensure they have the necessary attributes.")

    showers_to_keep = []

    for shower in showers:
        effective_nDigis = compute_effective_nDigis(shower, keys)
        if effective_nDigis >= threshold[shower.st - 1]:
            showers_to_keep.append(shower)

    setattr(ev, showers2use_name, showers_to_keep)