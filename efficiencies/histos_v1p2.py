from functools import partial
import ROOT as r
import numpy as np
from utils.functions import stations, wheels
from dtpr.utils.functions import get_unique_locs
from utils.genmuon_functions import analyze_genmuon_showers
from utils.shower_functions import compute_effective_nDigis


histos = dict()

# ----------------------- shower features histos ----------------------- #

def compute__shower_size(shower, method=1):
    if method == 1:
        return shower.max_wire - shower.min_wire
    else:
        # digis = shower.digis
        # if not digis:
        #     return 0
        # wires = [digi.w for digi in shower.digis]
        wires = shower.digis_wire
        IQR = np.percentile(wires, 75) - np.percentile(wires, 25)
        return IQR


for wh in wheels:
    for st in stations:
        histos.update({
            f"showers_size_{wh}_{st}_tp": {
                "type": "distribution",
                "histo" : r.TH1F(f"showers_size_{wh}_{st}_tp_method1", f"W_max - W_min", 100, 0, 100),
                "func"     : lambda reader, wh=wh, st=st: [compute__shower_size(shower) for shower in reader.filter_particles("fwshowers", wh=wh, st=st, is_true_shower=True)],
            },
            f"showers_size_{wh}_{st}_fp": {
                "type": "distribution",
                "histo" : r.TH1F(f"showers_size_{wh}_{st}_fp_method1", f"W_max - W_min", 100, 0, 100),
                "func"     : lambda reader, wh=wh, st=st: [compute__shower_size(shower) for shower in reader.filter_particles("fwshowers", wh=wh, st=st, is_true_shower=False)],
            },
            f"showers_size_{wh}_{st}_tp_method2": {
                "type": "distribution",
                "histo" : r.TH1F(f"showers_size_{wh}_{st}_tp_method2", f"IQR", 100, 0, 100),
                "func"     : lambda reader, wh=wh, st=st: [compute__shower_size(shower, method=2) for shower in reader.filter_particles("fwshowers", wh=wh, st=st, is_true_shower=True)],
            },
            f"showers_size_{wh}_{st}_fp_method2": {
                "type": "distribution",
                "histo" : r.TH1F(f"showers_size_{wh}_{st}_fp_method2", f"IQR", 100, 0, 100),
                "func"     : lambda reader, wh=wh, st=st: [compute__shower_size(shower, method=2) for shower in reader.filter_particles("fwshowers", wh=wh, st=st, is_true_shower=False)],
            },
            f"showers_nDigis_{wh}_{st}_tp": {
                "type": "distribution",
                "histo" : r.TH1F(f"showers_nDigis_{wh}_{st}_tp", f"N Digis", 50, 0, 50),
                # "func"     : lambda reader, wh=wh, st=st: [len({(digi.w, digi.l) for digi in shower.digis}) for shower in reader.filter_particles("fwshowers", wh=wh, st=st, is_true_shower=True)],
                "func": lambda reader, wh=wh, st=st: [compute_effective_nDigis(shower, keys=["digis_wire", "digis_layer"]) for shower in reader.filter_particles("fwshowers", wh=wh, st=st, is_true_shower=True)],
            },
            f"showers_nDigis_{wh}_{st}_fp": {
                "type": "distribution",
                "histo" : r.TH1F(f"showers_nDigis_{wh}_{st}_fp", f"N Digis", 50, 0, 50),
                # "func"     : lambda reader, wh=wh, st=st: [len({(digi.w, digi.l) for digi in shower.digis}) for shower in reader.filter_particles("fwshowers", wh=wh, st=st, is_true_shower=False)],
                "func": lambda reader, wh=wh, st=st: [compute_effective_nDigis(shower, keys=["digis_wire", "digis_layer"]) for shower in reader.filter_particles("fwshowers", wh=wh, st=st, is_true_shower=False)],
            },
            f"showers_nShowers_{wh}_{st}_tp": {
                "type": "distribution",
                "histo" : r.TH1F(f"showers_nShowers_{wh}_{st}_tp", f"N Showers", 50, 0, 50),
                "func"     : lambda reader, wh=wh, st=st: [len(reader.filter_particles("fwshowers", wh=wh, st=st, is_true_shower=True))] if reader.fwshowers else None,
            },
            f"showers_nShowers_{wh}_{st}_fp": {
                "type": "distribution",
                "histo" : r.TH1F(f"showers_nShowers_{wh}_{st}_fp", f"N Showers", 50, 0, 50),
                "func"     : lambda reader, wh=wh, st=st: [len(reader.filter_particles("fwshowers", wh=wh, st=st, is_true_shower=False))]  if reader.fwshowers else None,
            },
            # realshowers
            f"realshowers_nDigis_{wh}_{st}": {
                "type": "distribution",
                "histo" : r.TH1F(f"realshowers_nDigis_{wh}_{st}", f"N Digis in Real Showers", 50, 0, 50),
                "func"     : lambda reader, wh=wh, st=st: [shower.ndigis for shower in reader.realshowers if shower.wh == wh and shower.st == st],
            },
            f"realshowers_type_{wh}_{st}": {
                "type": "distribution",
                "histo" : r.TH1I(f"realshowers_type_{wh}_{st}", f"Type of Real Showers", 4, 1, 5),
                "func"     : lambda reader, wh=wh, st=st: [shower.shower_type for shower in reader.realshowers if shower.wh == wh and shower.st == st],
            },
            f"realshowers_size_{wh}_{st}_method1": {
                "type": "distribution",
                "histo" : r.TH1F(f"realshowers_size_{wh}_{st}_method1", f"Size of Real Showers", 100, 0, 100),
                "func"     : lambda reader, wh=wh, st=st: [compute__shower_size(shower, method=1) for shower in reader.realshowers if shower.wh == wh and shower.st == st],
            },
            f"realshowers_nShowers_{wh}_{st}": {
                "type": "distribution",
                "histo" : r.TH1F(f"realshowers_nShowers_{wh}_{st}", f"N Real Showers", 50, 0, 50),
                "func"     : lambda reader, wh=wh, st=st: [len(reader.filter_particles("realshowers", wh=wh, st=st))] if reader.realshowers else None,
            },
        })

# ---------------------- study of types of truth shower definitions ----------------------

def set_showered_flags(reader, method=2):
    """
    Set the showered flag for genmuons depending on the method used.
    """
    for gm in reader.genmuons:
        gm.showered = False # ensure the flag is reset

    analyze_genmuon_showers(reader, method=method)
    return reader.genmuons

histos.update({
    "showered_genmuon_meth1_eff": {
        "type": "eff",
        "histoDen" : r.TH1D("showered_genmuon_meth1_total", r';GenMuon Pt;', 50, 0 , 3335),
        "histoNum" : r.TH1D("showered_genmuon_meth1_num", r';GenMuon Pt;', 50, 0 , 3335),
        "func"     : lambda reader: [gm.pt for gm in reader.genmuons],
        "numdef"   : lambda reader: [gm.showered for gm in set_showered_flags(reader, method=1)],
    },
    "showered_genmuon_meth2_eff": {
        "type": "eff",
        "histoDen" : r.TH1D("showered_genmuon_meth2_total", r';GenMuon Pt;', 50, 0 , 3335),
        "histoNum" : r.TH1D("showered_genmuon_meth2_num", r';GenMuon Pt;', 50, 0 , 3335),
        "func"     : lambda reader: [gm.pt for gm in reader.genmuons],
        "numdef"   : lambda reader: [gm.showered for gm in set_showered_flags(reader, method=2)],
    },
    "showered_genmuon_meth3_eff": {
        "type": "eff",
        "histoDen" : r.TH1D("showered_genmuon_meth3_total", r';GenMuon Pt;', 50, 0 , 3335),
        "histoNum" : r.TH1D("showered_genmuon_meth3_num", r';GenMuon Pt;', 50, 0 , 3335),
        "func"     : lambda reader: [gm.pt for gm in reader.genmuons],
        "numdef"   : lambda reader: [gm.showered for gm in set_showered_flags(reader, method=3)],
    },
})



# --------------------------- Stud of showers classification ----------------------------

def get_locs_to_check(reader, station=1, opt=1, by_sl=False):
    loc_ids = ["wh", "sc", "st", "sl"] if by_sl else ["wh", "sc", "st"]
    if opt == 3:
        indexs = get_unique_locs(particles=reader.filter_particles("digis", st=station), loc_ids=loc_ids)
        return indexs

    fwshowers_locs = get_unique_locs(particles=reader.filter_particles("fwshowers", st=station), loc_ids=loc_ids)
    realshowers_locs = get_unique_locs(particles=reader.filter_particles("realshowers", st=station), loc_ids=loc_ids)

    if opt == 1: #every chamber with showers, and traversed by genmuons
        _gm_seg_locs = get_unique_locs(particles=[seg for gm in reader.genmuons for seg in gm.matched_segments if seg.st==station], loc_ids=["wh", "sc", "st"])
        if by_sl:
            gm_seg_locs = set()
            for wh, sc, st in _gm_seg_locs:
                gm_seg_locs.add((wh, sc, st, 1)) # sl 1
                gm_seg_locs.add((wh, sc, st, 3)) # sl 3
        else:
            gm_seg_locs = _gm_seg_locs
        indexs = fwshowers_locs.union(realshowers_locs).union(gm_seg_locs)

    if opt == 2: #every chamber which any shower
        indexs = fwshowers_locs.union(realshowers_locs)

    return indexs

def compute_tpfptnfn(reader, station=1, opt=1, by_sl=False):
    """
    Classifies true positives, false positives, true negatives, and false negatives based on fwshowers and realshowers.

    Args:
        reader (object): The reader object containing fwshowers and realshowers.

    Returns:
        tuple: A tuple containing the wheel number and a classification code:
            0 - True Positive (TP)
            1 - False Positive (FP)
            2 - True Negative (TN)
            3 - False Negative (FN)
    """
    output = []

    indexs = get_locs_to_check(reader, station=station, opt=opt, by_sl=by_sl)

    # with open("output_tpfptnfn.txt", "a") as f:
    for index in indexs:
        if by_sl:
            wh, sc, st, sl = index
            kargs = {"wh": wh, "sc": sc, "st": st, "sl": sl}
        else:
            wh, sc, st = index
            kargs = {"wh": wh, "sc": sc, "st": st}

        real_showers = reader.filter_particles("realshowers", **kargs)
        fwshowers = reader.filter_particles("fwshowers", **kargs)

        if real_showers:
            if fwshowers:
                # f.write(f"{reader.iev} {" ".join([str(val) for val in kargs.values()])} tp\n")
                output.append((wh, 0)) # true positive
            else:
                # f.write(f"{reader.iev} {" ".join([str(val) for val in kargs.values()])} fn\n")
                output.append((wh, 3)) # false negative
        else:
            if fwshowers:
                # f.write(f"{reader.iev} {" ".join([str(val) for val in kargs.values()])} fp\n")
                output.append((wh, 1)) # false positive
            else:
                # f.write(f"{reader.iev} {" ".join([str(val) for val in kargs.values()])} tn\n")
                output.append((wh, 2)) # true negative

    return output

for st in stations:
    histos.update({ # conf maps
        "shower_tpfptnfn_MB" + str(st): {
        "type": "distribution2d",
        "histo": r.TH2D(f"shower_tpfptnfn_MB{st}", r';Wheel; [TP, FP, TN, FN]', 5, -2.5, 2.5, 4, 0, 4),
        "func": lambda reader, st=st: [bin for bin in compute_tpfptnfn(reader, station=st) ]
        },
    })

shower_classes = {
    "tp": 1,
    "tp_matched_amtp": 2,
    "tp_matched_amtp_highpt": 3,
    "tp_matched_amtp_not_highpt": 4,
    "tp_matched_amtp_showeredmuon": 5,
    "tp_matched_amtp_not_showeredmuon": 6,
    "tp_not_matched_amtp": 7,
    "tp_not_matched_amtp_highpt": 8,
    "tp_not_matched_amtp_not_highpt": 9,
    "tp_not_matched_amtp_showeredmuon": 10,
    "tp_not_matched_amtp_not_showeredmuon": 11,
    "fp": 12,
    "fp_matched_amtp": 13,
    "fp_matched_amtp_highpt": 14,
    "fp_matched_amtp_not_highpt": 15,
    "fp_matched_amtp_showeredmuon": 16,
    "fp_matched_amtp_not_showeredmuon": 17,
    "fp_not_matched_amtp": 18,
    "fp_not_matched_amtp_highpt": 19,
    "fp_not_matched_amtp_not_highpt": 20,
    "fp_not_matched_amtp_showeredmuon": 21,
    "fp_not_matched_amtp_not_showeredmuon": 22,
}

def showers_classification(event, station=None, include_SL=False):
    if station is None:
        showers = event.fwshowers
    else:
        showers = [shower for shower in event.fwshowers if shower.st == station]

    if not include_SL:
        showers = [shower for shower in showers if shower.sl != 2]

    output = []
    for shower in showers:
        key = "tp" if shower.is_true_shower else "fp"
        output.append(shower_classes[key])
        key = f"{key}_matched_amtp" if shower.matched_tps else f"{key}_not_matched_amtp"
        output.append(shower_classes[key])
        key_1 = f"{key}_highpt" if shower.is_highpt_shower else f"{key}_not_highpt"
        output.append(shower_classes[key_1])
        # Remove the '_highpt' or '_not_highpt' part for the last key
        key_2 = f"{key}_showeredmuon" if shower.comes_from_showered_genmuon else f"{key}_not_showeredmuon"
        output.append(shower_classes[key_2])

    return output

for st in stations:
    histos.update({
        f"showers_classification_MB{st}": {
            "type": "distribution",
            "histo": r.TH1D(f"showers_classification_MB{st}", r';Shower Class;', 22, 0.5, 22.5),
            "func": lambda reader, st=st: showers_classification(reader, station=st),
        },
    })

# ---- filter results -----------------
histos.update({
    "shower_filter_highpt_tag_eff_all": {
        "type": "eff",
        "histoDen": r.TH1D("shower_filter_highpt_tag_eff_all_total", r';GenMuon Pt;', 333, 0,3330),
        "histoNum": r.TH1D("shower_filter_highpt_tag_eff_all_num", r';GenMuon Pt;', 333, 0, 3330),
        "func": lambda reader: [gm.pt for gm in reader.genmuons if gm.showered],
        "numdef": lambda reader: [len(getattr(gm, 'matched_showers', [])) > 0 for gm in reader.genmuons if gm.showered],
    },
    "shower_filter_highpt_tag_eff_tp": { # to plot the fraction of showered generator muons that has asociated a shower
        "type": "eff",
        "histoDen": r.TH1D("shower_filter_highpt_tag_eff_tp_total", r';Showered GenMuon Pt;', 333, 0, 3330),
        "histoNum": r.TH1D("shower_filter_highpt_tag_eff_tp_num", r';Showered GenMuon Pt;', 333, 0, 3330),
        "func": lambda reader: [gm.pt for gm in reader.genmuons if gm.showered],
        "numdef": lambda reader: [any(shower.is_true_shower for shower in getattr(gm, 'matched_showers', [])) for gm in reader.genmuons if gm.showered],
    },
    "shower_filter_highpt_tag_eff_fp": {
        "type": "eff",
        "histoDen": r.TH1D("shower_filter_highpt_tag_eff_fp_total", r';Non-showered GenMuon Pt;', 333, 0, 3330),
        "histoNum": r.TH1D("shower_filter_highpt_tag_eff_fp_num", r';Non-showered GenMuon Pt;', 333, 0, 3330),
        "func": lambda reader: [gm.pt for gm in reader.genmuons if gm.showered],
        "numdef": lambda reader: [ bool(getattr(gm, 'matched_showers', [])) and all(not shower.is_true_shower for shower in getattr(gm, 'matched_showers', [])) for gm in reader.genmuons if gm.showered],
    }, 
})