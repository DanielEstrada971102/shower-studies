
wheels = [-2, -1, 0, 1, 2]
stations = [1, 2, 3, 4]

histos = {}

for wh in wheels:
    for st in stations:
        histos.update({
            f"realshowers_type_wh{wh}_st{st}": {
                "type" : "root-draw",
                "draw": "realshower_type >> realshowers_type_wh{wh}_st{st}(50,0,50)".format(wh=wh, st=st),
                "selection": "ph2Shower_wheel=={wh} && ph2Shower_station=={st}".format(wh=wh, st=st),
                "option": "goff"
            },
        })