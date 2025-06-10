# Define the histograms container
import ROOT as r

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