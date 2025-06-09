# Define the histograms container
import ROOT as r

# Histogram defined here
# - tps_q<6_MB1
# - tps_q<6_MB2
# - tps_q<6_MB3
# - tps_q<6_MB4
# - tps_q>6_MB1
# - tps_q>6_MB2
# - tps_q>6_MB3
# - tps_q>6_MB4
# - showers_MB1
# - showers_MB2
# - showers_MB3
# - showers_MB4
# - showers_true_MB1
# - showers_true_MB2
# - showers_true_MB3
# - showers_true_MB4
# - tps_match_showers_MB1
# - tps_match_showers_MB2
# - tps_match_showers_MB3
# - tps_match_showers_MB4
# - matched_tps_MB1
# - matched_tps_MB2
# - matched_tps_MB3
# - matched_tps_MB4


histos = {}

def tp_match_true_shower(tp):
    """Check if a trigger primitive matches a true shower."""
    return any(shower.is_true_shower for shower in tp.matched_showers)

for st in range(1, 5):
    histos.update({
        # just to inspect...
        f"tps_q<6_MB{st}": {
            "type": "distribution",
            "histo": r.TH1D(f"tps_q<6_MB{st}", r';Wheel;\# AM TPs', 5, -2.5, 2.5),
            "func": lambda reader: [tp.wh for tp in reader.tps if tp.quality < 6 and tp.st == st],
        },
        f"tps_q>6_MB{st}": {
            "type": "distribution",
            "histo": r.TH1D(f"tps_q>6_MB{st}", r';Wheel;\# AM TPs', 5, -2.5, 2.5),
            "func": lambda reader: [tp.wh for tp in reader.tps if tp.quality >= 6 and tp.st == st],
        },
        f"showers_MB{st}": {
            "type": "distribution",
            "histo": r.TH1D(f"shower_MB{st}", r';Wheel;\# showers', 5, -2.5, 2.5),
            "func": lambda reader: [shower.wh for shower in reader.fwshowers if shower.st == st],
        },
        f"showers_true_MB{st}": {
            "type": "distribution",
            "histo": r.TH1D(f"shower_true_MB{st}", r';Wheel;\# true showers', 5, -2.5, 2.5),
            "func": lambda reader: [shower.wh for shower in reader.fwshowers if shower.st == st and shower.is_true_shower],
        },
        # ------ Filter histograms ------
        f"tps_match_showers_MB{st}": { # ratio between TPs that match a shower and all TPs
            "type" : "eff",
            "histoDen" : r.TH1D(f"tps_match_showers_MB{st}_AM_total", r';Wheel;', 5, -2.5 , 2.5),
            "histoNum" : r.TH1D(f"tps_match_showers_MB{st}_AM_num", r';Wheel;', 5, -2.5 , 2.5),
            "func"     : lambda reader: [tp.wh for tp in reader.tps if tp.st == st],
            "numdef"   : lambda reader: [len(getattr(tp, "matched_showers", [])) > 0 for tp in reader.tps if tp.st == st],
        },
        f"matched_tps_MB{st}": { # ratio between TPs that match a true shower and all TPs that match a shower
            "type" : "eff",
            "histoDen" : r.TH1D(f"matched_tps_MB{st}_AM_total", r';Wheel;', 5, -2.5 , 2.5),
            "histoNum" : r.TH1D(f"matched_tps_MB{st}_AM_num", r';Wheel;', 5, -2.5 , 2.5),
            "func"     : lambda reader: [tp.wh for tp in reader.tps if tp.st == st and len(getattr(tp, "matched_showers", []))>0],
            "numdef"   : lambda reader: [tp_match_true_shower(tp) for tp in reader.tps if tp.st == st and len(getattr(tp, "matched_showers", []))>0],
        },
        f"at_least_oneTP_for_real_shower_MB{st}": {
            "type": "eff",
            "histoDen": r.TH1D(f"at_least_oneTP_for_real_shower_MB{st}_AM_total", r';Wheel;', 5, -2.5, 2.5),
            "histoNum": r.TH1D(f"at_least_oneTP_for_real_shower_MB{st}_AM_num", r';Wheel;', 5, -2.5, 2.5),
            "func": lambda reader: [shower.wh for shower in reader.filter_particles("fwshowers", st = st, is_true_shower = True)],
            "numdef": lambda reader: [any(shower in getattr(tp, "matched_showers", []) for tp in reader.tps if tp.wh == shower.wh) for shower in reader.filter_particles("fwshowers", st = st, is_true_shower = True)],
        }
    })

histos.update({
    "tps_x_MB1": {
        "type": "distribution",
        "histo": r.TH1D("tps_x_MB1", r';x [cm];\# AM TPs', 100, -250, 250),
        "func": lambda reader: [tp.posLoc_x for tp in reader.tps if tp.st == 1],
    },
})

histos.update({
    "showered_genmuon_pt_eff": { # to plot the fraction of generator muons that showered acording to the PT value
        "type": "eff",
        "histoDen": r.TH1D("showered_genmuon_pt_eff_total", r';GenMuon Pt;', 50, 0, 3335),
        "histoNum": r.TH1D("showered_genmuon_pt_eff_num", r';GenMuon Pt;', 50, 0, 3335),
        "func": lambda reader: [gm.pt for gm in reader.genmuons],
        "numdef": lambda reader: [gm.showered for gm in reader.genmuons],
    }
})

histos.update({
    "shower_showeredgenmuon_tag_eff_pttrend": { # to plot the fraction of showered generator muons that has asociated a shower
        "type": "eff",
        "histoDen": r.TH1D("shower_showeredgenmuon_tag_eff_pttrend_total", r';Showered GenMuon Pt;', 50, 0, 3335),
        "histoNum": r.TH1D("shower_showeredgenmuon_tag_eff_pttrend_num", r';Showered GenMuon Pt;', 50, 0, 3335),
        "func": lambda reader: [gm.pt for gm in reader.genmuons if gm.showered],
        "numdef": lambda reader: [len(getattr(gm, 'matched_showers', [])) > 0 for gm in reader.genmuons if gm.showered],
    }
})

for st in range(1, 5):
    histos.update({
        f"shower_matchAmTP_eff_MB{st}": {
            "type": "eff",
            "histoDen": r.TH1D(f"shower_matchAmTP_eff_MB{st}_total", r';Wheel;', 5, -2.5, 2.5),
            "histoNum": r.TH1D(f"shower_matchAmTP_eff_MB{st}_num", r';Wheel;', 5, -2.5, 2.5),
            "func": lambda reader: [shower.wh for shower in reader.fwshowers if shower.st == st],
            "numdef": lambda reader: [len(getattr(shower, 'matched_tps', [])) > 0 for shower in reader.fwshowers if shower.st == st],
        },
        f"shower_matchHighPtmuon_eff_MB{st}": {
            "type": "eff",
            "histoDen": r.TH1D(f"shower_matchHighPtmuon_eff_MB{st}_total", r';Wheel;', 5, -2.5, 2.5),
            "histoNum": r.TH1D(f"shower_matchHighPtmuon_eff_MB{st}_num", r';Wheel;', 5, -2.5, 2.5),
            "func": lambda reader: [shower.wh for shower in reader.fwshowers if shower.st == st],
            "numdef": lambda reader: [shower.is_highpt_shower for shower in reader.fwshowers if shower.st == st],
        },
        f"shower_matchshoweredgenmuon_eff_MB{st}": {
            "type": "eff",
            "histoDen": r.TH1D(f"shower_matchshoweredgenmuon_eff_MB{st}_total", r';Wheel;', 5, -2.5, 2.5),
            "histoNum": r.TH1D(f"shower_matchshoweredgenmuon_eff_MB{st}_num", r';Wheel;', 5, -2.5, 2.5),
            "func": lambda reader: [shower.wh for shower in reader.fwshowers if shower.st == st],
            "numdef": lambda reader: [shower.comes_from_showered_genmuon for shower in reader.fwshowers if shower.st == st],
        }
    })