from dtpr.utils.functions import stations
import ROOT as r

# Histograms defined here...
# - fwshower_rate_goodBX_MB1
# - fwshower_rate_goodBX_MB2
# - fwshower_rate_goodBX_MB3
# - fwshower_rate_goodBX_MB4
# - fwshower_rate_allBX_MB1
# - fwshower_rate_allBX_MB2
# - fwshower_rate_allBX_MB3
# - fwshower_rate_allBX_MB4

histos= {}

def get_showers_rate(reader, station, goodbx=True):
    return [
        shower
        for shower in reader.filter_particles("fwshowers", st=station)
        if (shower.BX == 20 if goodbx else 1)
    ]

# ------------------------------ Shower rates -------------------------------

for st in stations:
    histos.update({
        f"fwshower_rate_goodBX_MB{st}": { # ----- good BX -----
            "type": "distribution",
            "histo": r.TH1D(f"Rate_goodBX_MB{st}_FwShower", r';Wheel; Events', 5, -2.5, 2.5),
            "func": lambda reader, st=st: [
                shower.wh for shower in get_showers_rate(reader, station=st, goodbx=True)
            ],
        },
        f"fwshower_rate_allBX_MB{st}": { # ----- all BX -----
            "type": "distribution",
            "histo": r.TH1D(f"Rate_allBX_MB{st}_FwShower", r';Wheel; Events', 5, -2.5, 2.5),
            "func": lambda reader, st=st: [
                shower.wh for shower in get_showers_rate(reader, station=st, goodbx=False)
            ],
        },
    })
