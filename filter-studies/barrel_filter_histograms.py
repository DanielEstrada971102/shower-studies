# Define the histograms container
import ROOT as r
import sys
sys.path.append("..")  # Adjust the path to include the parent directory

from dtpr.utils.functions import stations, get_best_matches, get_unique_locs

# Histogram defined here
# - 

histos = {}

histos.update({
    "shower_showeredgenmuon_tag_eff_pttrend": { # to plot the fraction of showered generator muons that has asociated a shower
        "type": "eff",
        "histoDen": r.TH1D("shower_showeredgenmuon_tag_eff_pttrend_total", r';Showered GenMuon Pt;', 50, 0, 3335),
        "histoNum": r.TH1D("shower_showeredgenmuon_tag_eff_pttrend_num", r';Showered GenMuon Pt;', 50, 0, 3335),
        "func": lambda reader: [gm.pt for gm in reader.genmuons if gm.showered],
        "numdef": lambda reader: [len(getattr(gm, 'matched_showers', [])) > 0 for gm in reader.genmuons if gm.showered],
    },
    "AMTp_showeredgenmuon_tag_eff_pttrend": { # to plot the fraction of AMTp muons that has asociated a shower
    "type": "eff",
    "histoDen": r.TH1D("AMTp_showeredgenmuon_tag_eff_pttrend_total", r';Showered GenMuon Pt;', 50, 0, 3335),
    "histoNum": r.TH1D("AMTp_showeredgenmuon_tag_eff_pttrend_num", r';showered GenMuon Pt;', 50, 0, 3335),
    "func": lambda reader: [gm.pt for gm in reader.genmuons if gm.showered],
    "numdef": lambda reader: [any(len(getattr(tp, 'matched_showers', []))>0 for tp in getattr(gm, 'matched_tps', [])) for gm in reader.genmuons if gm.showered],
    },
    # over all gm
    "shower_genmuon_tag_eff_pttrend_all": {
        "type": "eff",
        "histoDen": r.TH1D("shower_genmuon_tag_eff_pttrend_all_total", r';Showered GenMuon Pt;', 50, 0, 3335),
        "histoNum": r.TH1D("shower_genmuon_tag_eff_pttrend_all_num", r';Showered GenMuon Pt;', 50, 0, 3335),
        "func": lambda reader: [gm.pt for gm in reader.genmuons],
        "numdef": lambda reader: [len(getattr(gm, 'matched_showers', [])) > 0 for gm in reader.genmuons],
    },
    "AMTp_genmuon_tag_eff_pttrend_all": {
        "type": "eff",
        "histoDen": r.TH1D("AMTp_genmuon_tag_eff_pttrend_all_total", r';Showered GenMuon Pt;', 50, 0, 3335),
        "histoNum": r.TH1D("AMTp_genmuon_tag_eff_pttrend_all_num", r';Showered GenMuon Pt;', 50, 0, 3335),
        "func": lambda reader: [gm.pt for gm in reader.genmuons],
        "numdef": lambda reader: [any(len(getattr(tp, 'matched_showers', []))>0 for tp in getattr(gm, 'matched_tps', [])) for gm in reader.genmuons],
    },
})

def get_locs_to_check(reader, station=1):
    loc_ids = ["wh", "sc", "st"]
    fwshowers_locs = get_unique_locs(particles=reader.filter_particles("fwshowers_ff", st=station), loc_ids=loc_ids)
    realshowers_locs = get_unique_locs(particles=reader.filter_particles("realshowers", st=station), loc_ids=loc_ids)

    _gm_seg_locs = get_unique_locs(particles=[seg for gm in reader.genmuons for seg in gm.matched_segments if seg.st==station], loc_ids=["wh", "sc", "st"])
    indexs = fwshowers_locs.union(realshowers_locs).union(_gm_seg_locs)

    return indexs

def compute_tpfptnfn(reader, station=1):
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

    indexs = get_locs_to_check(reader, station=station)

    # with open("output_tpfptnfn.txt", "a") as f:
    for index in indexs:
        wh, sc, st = index
        kargs = {"wh": wh, "sc": sc, "st": st}

        real_showers = reader.filter_particles("realshowers", **kargs)
        fwshowers = reader.filter_particles("fwshowers_ff", **kargs)

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

def shower_eff_func_after_filter(reader, station=1):
    # creader = deepcopy(reader)
    # delete the showers that do not have matched tps
    setattr(reader, "fwshowers_ff", [shower for shower in reader.fwshowers if len(getattr(shower, 'matched_tps', [])) > 0])
    return [wh for wh, *_a in get_locs_to_check(reader, station=station)]

def shower_eff_numdef_after_filter(reader, station=1):
    # creader = deepcopy(reader)
    # delete the showers that do not have matched tps
    if not hasattr(reader, 'fwshowers_ff'):
        setattr(reader, "fwshowers_ff", [shower for shower in reader.fwshowers if len(getattr(shower, 'matched_tps', [])) > 0])
    return [(cls == 0 or cls == 2) for _, cls in compute_tpfptnfn(reader, station=station)]

def get_showers_rate_afterfilter(reader, station, goodbx=True):
    return [
        shower
        for shower in reader.filter_particles("fwshowers", st=station)
        if (shower.BX == 20 if goodbx else 1) and len(getattr(shower, 'matched_tps', [])) > 0
    ]

def am_eff_func_after_filter(reader, station):
    return [seg.wh for seg in get_best_matches(reader, station=station)]

def am_eff_numdef_after_filter(reader, station):
    # creader = deepcopy(reader)
    # delete the tp that do not live in a station with shower
    output = []
    for seg in get_best_matches(reader, station=station):
        if not hasattr(seg, 'matched_tps'):
            output.append(False)
            continue
        # remove tps that are not in the same wheel, sector and station as the shower
        seg.matched_tps_ff = [tp for tp in seg.matched_tps if (tp.wh, tp.sc, tp.st) not in get_unique_locs(particles=reader.fwshowers, loc_ids=["wh", "sc", "st"])]
        if len(seg.matched_tps_ff) > 0:
            output.append(True)
        else:
            output.append(False)
    return output

def get_tps_rate_after_filter(reader, station, goodbx=True):
    return [
        tp
        for tp in reader.filter_particles("tps", st=station)
        if (tp.BX == 0 if goodbx else 1) and (tp.wh, tp.sc, tp.st) not in get_unique_locs(particles=reader.fwshowers, loc_ids=["wh", "sc", "st"])
    ]

for st in stations:
    histos.update({ 
        # ----- efficiency after filter
        "fwshower_eff_afterfilter_MB" + str(st): {
            "type": "eff",
            "histoDen": r.TH1D(f"Fwshower_eff_afterfilter_MB{st}_total", r';Wheel; Events', 5, -2.5, 2.5),
            "histoNum": r.TH1D(f"Fwshower_eff_afterfilter_MB{st}_num", r';Wheel; Events', 5, -2.5, 2.5),
            "func": lambda reader, st=st: shower_eff_func_after_filter(reader, station=st),
            "numdef": lambda reader, st=st: shower_eff_numdef_after_filter(reader, station=st),
        },
        # rates after filter
        f"fwshower_rate_afterfilter_goodBX_MB{st}": { # ----- good BX -----
            "type": "distribution",
            "histo": r.TH1D(f"FWshower_Rate_afterfilter_goodBX_MB{st}_FwShower", r';Wheel; Events', 5, -2.5, 2.5),
            "func": lambda reader, st=st: [
                shower.wh for shower in get_showers_rate_afterfilter(reader, station=st, goodbx=True)
            ],
        },
        f"fwshower_rate_afterfilter_allBX_MB{st}": { # ----- all BX -----
            "type": "distribution",
            "histo": r.TH1D(f"FWshower_Rate_afterfilter_allBX_MB{st}_FwShower", r';Wheel; Events', 5, -2.5, 2.5),
            "func": lambda reader, st=st: [
                shower.wh for shower in get_showers_rate_afterfilter(reader, station=st, goodbx=False)
            ],
        },
        # AM recoveries
        f"AMTpshowered_AMTps_eff_MB{st}": {
            "type": "eff",
            "histoDen": r.TH1D(f"AMTpshowered_AMTps_eff_MB{st}_total", r';Wheel;', 5, -2.5, 2.5),
            "histoNum": r.TH1D(f"AMTpshowered_AMTps_eff_MB{st}_num", r';Wheel;', 5, -2.5, 2.5),
            "func": lambda reader: [tp.wh for tp in reader.tps if tp.st == st],
            "numdef": lambda reader: [any(gm.showered for gm in tp.matched_genmuons) for tp in reader.tps if tp.st == st],
        },
        f"AMTpshoweredtagged_AMTps_eff_MB{st}": {
            "type": "eff",
            "histoDen": r.TH1D(f"AMTpshoweredtagged_AMTps_eff_MB{st}_total", r';Wheel;', 5, -2.5, 2.5),
            "histoNum": r.TH1D(f"AMTpshoweredtagged_AMTps_eff_MB{st}_num", r';Wheel;', 5, -2.5, 2.5),
            "func": lambda reader: [tp.wh for tp in reader.tps if tp.st == st],
            "numdef": lambda reader: [any(gm.showered for gm in tp.matched_genmuons) and tp.matched_showers for tp in reader.tps if tp.st == st],
        },
        # AM efficiencies after filter
        f"seg_eff_afterfilter_MB{st}": {  
            "type": "eff",
            "histoDen": r.TH1D(f"AMEff_afterfilter_MB{st}_AM_total", r';Wheel; Events', 5, -2.5, 2.5),
            "histoNum": r.TH1D(f"AMEff_afterfilter_MB{st}_AM_num", r';Wheel; Events', 5, -2.5, 2.5),
            "func": lambda reader, st=st: am_eff_func_after_filter(reader, station=st), 
            "numdef": lambda reader, st=st: am_eff_numdef_after_filter(reader, station=st), 
        },
        # AM rates after filter
        f"AM_rate_afterfilter_goodBX_MB{st}": { # ----- good BX -----
            "type": "distribution",
            "histo": r.TH1D(f"AM_Rate_afterfilter_goodBX_MB{st}_AM", r';Wheel; Events', 5, -2.5, 2.5),
            "func": lambda reader, st=st: [
                tp.wh for tp in get_tps_rate_after_filter(reader, station=st, goodbx=True)
            ],
        },
        f"AM_rate_afterfilter_allBX_MB{st}": { # ----- all BX -----
            "type": "distribution",
            "histo": r.TH1D(f"AM_Rate_afterfilter_allBX_MB{st}_AM", r';Wheel; Events', 5, -2.5, 2.5),
            "func": lambda reader, st=st: [
                tp.wh for tp in get_tps_rate_after_filter(reader, station=st, goodbx=False)
            ],
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

def showers_classification(event, station=None):
    if station is None:
        showers = event.fwshowers
    else:
        showers = [shower for shower in event.fwshowers if shower.st == station]

    output = []
    for shower in showers:
        key = "tp" if shower.is_true_shower else "fp"
        output.append(shower_classes[key])
        key = f"{key}_matched_amtp" if shower.matched_tps else f"{key}_not_matched_amtp"
        output.append(shower_classes[key])
        key = f"{key}_highpt" if shower.is_highpt_shower else f"{key}_not_highpt"
        output.append(shower_classes[key])
        # Remove the '_highpt' or '_not_highpt' part for the last key
        key = f"{key.rsplit('_', 1)[0]}_showeredmuon" if shower.comes_from_showered_genmuon else f"{key.rsplit('_not', 1)[0]}_not_showeredmuon"
        output.append(shower_classes[key])

    return output

histos.update({
    "showers_classification": {
        "type": "distribution",
        "histo": r.TH1D("showers_classification", r';Shower Class;', 22, 0.5, 22.5),
        "func": lambda reader: showers_classification(reader, station=None),
    },
})
for st in stations:
    histos.update({
        f"showers_classification_MB{st}": {
            "type": "distribution",
            "histo": r.TH1D(f"showers_classification_MB{st}", r';Shower Class;', 22, 0.5, 22.5),
            "func": lambda reader, st=st: showers_classification(reader, station=st),
        },
    })
