wheels = [-2, -1, 0, 1, 2]
stations = [1, 2, 3, 4]

histos = dict()

# genmuon histos
histos.update({
    "gen_pt": {
        "type" : "root-draw",
        "draw": "gen_pt>>gen_pt(4000,0,4000)",
        "option": "goff"
    },
    "gen_eta": {
        "type" : "root-draw",
        "draw": "gen_eta>>gen_eta(500,-10,10)",
        "option": "goff"
    },
    "gen_phi": {
        "type" : "root-draw",
        "draw": "gen_phi>>gen_phi(500,10,10)",
        "option": "goff"
    },
})

# ----------------------- shower features histos ----------------------- #
for wh in wheels:
    for st in stations:
        histos.update({
            f"nshowers_wh{wh}_st{st}": {
                "type" : "root-draw",
                "draw": "Length$(ph2Shower_wheel)>>nshowers_wh{wh}_st{st}(100,0,100)".format(wh=wh, st=st),
                "selection": "ph2Shower_wheel=={wh} && ph2Shower_station=={st}".format(wh=wh, st=st),
                "option": "goff"
            },
            f"nshowers_wh{wh}_st{st}_noSL2": {
                "type" : "root-draw",
                "draw": "Length$(ph2Shower_wheel)>>nshowers_wh{wh}_st{st}_noSL2(100,0,100)".format(wh=wh, st=st),
                "selection": "ph2Shower_wheel=={wh} && ph2Shower_station=={st} && ph2Shower_superlayer!=2".format(wh=wh, st=st),
                "option": "goff"
            },
            f"nshowers_wh{wh}_st{st}_goodBX": {
                "type" : "root-draw",
                "draw": "Length$(ph2Shower_wheel)>>nshowers_wh{wh}_st{st}_goodBX(100,0,100)".format(wh=wh, st=st),
                "selection": "ph2Shower_wheel=={wh} && ph2Shower_station=={st} && ph2Shower_BX==20".format(wh=wh, st=st),
                "option": "goff"
            },
            f"nshowers_wh{wh}_st{st}_goodBX_noSL2": {
                "type" : "root-draw",
                "draw": "Length$(ph2Shower_wheel)>>nshowers_wh{wh}_st{st}_goodBX_noSL2(100,0,100)".format(wh=wh, st=st),
                "selection": "ph2Shower_wheel=={wh} && ph2Shower_station=={st} && ph2Shower_BX==20 && ph2Shower_superlayer!=2".format(wh=wh, st=st),
                "option": "goff"
            },
            f"showerBx_wh{wh}_st{st}": {
                "type" : "root-draw",
                "draw": "ph2Shower_BX>>showerBx_wh{wh}_st{st}(100,0,100)".format(wh=wh, st=st),
                "selection": "ph2Shower_wheel=={wh} && ph2Shower_station=={st}".format(wh=wh, st=st),
                "option": "goff"
            },
            f"showerNdigis_wh{wh}_st{st}": {
                "type" : "root-draw",
                "draw": "ph2Shower_ndigis>>showerNdigis_wh{wh}_st{st}(100,0,100)".format(wh=wh, st=st),
                "selection": "ph2Shower_wheel=={wh} && ph2Shower_station=={st}".format(wh=wh, st=st),   
                "option": "goff"
            },
            f"showerSize_wh{wh}_st{st}": {
                "type" : "root-draw",
                "draw": "ph2Shower_max_wire - ph2Shower_min_wire >>showerSize_wh{wh}_st{st}(100,0,100)".format(wh=wh, st=st),
                "selection": "ph2Shower_wheel=={wh} && ph2Shower_station=={st}".format(wh=wh, st=st),   
                "option": "goff"
            },
        })

# ----------------------- AM tps features histos ----------------------- #
for wh in wheels:
    for st in stations:
        for q in [-1, 1, 2, 3, 4, 6, 7, 8]:
            histos.update({
                # AM tps -phi features histogra
                f"nAMtps_phi_wh{wh}_st{st}_q{q}": {
                    "type" : "root-draw",
                    "draw": "ph2TpgPhiEmuAm_nTrigs>>nAMtps_phi_wh{wh}_st{st}_q{q}(100,0,100)".format(wh=wh, st=st, q=q),
                    "selection": "ph2TpgPhiEmuAm_wheel=={wh} && ph2TpgPhiEmuAm_station=={st} && ph2TpgPhiEmuAm_quality=={q}".format(wh=wh, st=st, q=q),
                    "option": "goff"
                },
                f"nAMtps_phi_goodBX_wh{wh}_st{st}_q{q}": {
                    "type" : "root-draw",
                    "draw": "ph2TpgPhiEmuAm_nTrigs>>nAMtps_phi_goodBX_wh{wh}_st{st}_q{q}(100,0,100)".format(wh=wh, st=st, q=q),
                    "selection": "ph2TpgPhiEmuAm_wheel=={wh} && ph2TpgPhiEmuAm_station=={st} && ph2TpgPhiEmuAm_quality=={q} && ph2TpgPhiEmuAm_BX==20".format(wh=wh, st=st, q=q),
                    "option": "goff"
                },
                f"AMtps_superlayer_wh{wh}_st{st}_q{q}": {
                    "type" : "root-draw",
                    "draw": "ph2TpgPhiEmuAm_superLayer>>AMtps_superlayer_wh{wh}_st{st}_q{q}(4,0,4)".format(wh=wh, st=st, q=q),
                    "selection": "ph2TpgPhiEmuAm_wheel=={wh} && ph2TpgPhiEmuAm_station=={st} && ph2TpgPhiEmuAm_quality=={q}".format(wh=wh, st=st, q=q),
                    "option": "goff"
                },
                f"AMtps_BX_wh{wh}_st{st}_q{q}": {
                    "type" : "root-draw",
                    "draw": "ph2TpgPhiEmuAm_BX>>AMtps_BX_wh{wh}_st{st}_q{q}(100,0,100)".format(wh=wh, st=st, q=q),
                    "selection": "ph2TpgPhiEmuAm_wheel=={wh} && ph2TpgPhiEmuAm_station=={st} && ph2TpgPhiEmuAm_quality=={q}".format(wh=wh, st=st, q=q),
                    "option": "goff"
                },
                f"AMtps_phi_wh{wh}_st{st}_q{q}": {
                    "type" : "root-draw",
                    "draw": "ph2TpgPhiEmuAm_phi>>AMtps_phi_wh{wh}_st{st}_q{q}(131074,-65537,65537)".format(wh=wh, st=st, q=q),
                    "selection": "ph2TpgPhiEmuAm_wheel=={wh} && ph2TpgPhiEmuAm_station=={st} && ph2TpgPhiEmuAm_quality=={q}".format(wh=wh, st=st, q=q),
                    "option": "goff"
                },
                f"AMtps_phiB_wh{wh}_st{st}_q{q}": {
                    "type" : "root-draw",
                    "draw": "ph2TpgPhiEmuAm_phiB>>AMtps_phiB_wh{wh}_st{st}_q{q}(8194,-4097,4097)".format(wh=wh, st=st, q=q),
                    "selection": "ph2TpgPhiEmuAm_wheel=={wh} && ph2TpgPhiEmuAm_station=={st} && ph2TpgPhiEmuAm_quality=={q}".format(wh=wh, st=st, q=q),
                    "option": "goff"
                },
                f"AMtps_posLocx_wh{wh}_st{st}_q{q}": {
                    "type" : "root-draw",
                    "draw": "ph2TpgPhiEmuAm_posLoc_x>>AMtps_posLocx_wh{wh}_st{st}_q{q}(2000,-1000,1000)".format(wh=wh, st=st, q=q),
                    "selection": "ph2TpgPhiEmuAm_wheel=={wh} && ph2TpgPhiEmuAm_station=={st} && ph2TpgPhiEmuAm_quality=={q}".format(wh=wh, st=st, q=q),
                    "option": "goff"
                },
                f"AMtps_dirLocphi_wh{wh}_st{st}_q{q}": {
                    "type" : "root-draw",
                    "draw": "ph2TpgPhiEmuAm_dirLoc_phi>>AMtps_dirLocphi_wh{wh}_st{st}_q{q}(720,-360,360)".format(wh=wh, st=st, q=q),
                    "selection": "ph2TpgPhiEmuAm_wheel=={wh} && ph2TpgPhiEmuAm_station=={st} && ph2TpgPhiEmuAm_quality=={q}".format(wh=wh, st=st, q=q),
                    "option": "goff"
                },
                # -------- only available for extended dataformat
                f"AMtps_phiCMSSW_wh{wh}_st{st}_q{q}": {
                    "type" : "root-draw",
                    "draw": "ph2TpgExtPhiEmuAm_phiCMSSW>>AMtps_phiCMSSW_wh{wh}_st{st}_q{q}(131074,-65537,65537)".format(wh=wh, st=st, q=q),
                    "selection": "ph2TpgExtPhiEmuAm_wheel=={wh} && ph2TpgExtPhiEmuAm_station=={st} && ph2TpgExtPhiEmuAm_quality=={q}".format(wh=wh, st=st, q=q),
                    "option": "goff"
                },
                f"AMtps_phiBCMSSW_wh{wh}_st{st}_q{q}": {
                    "type" : "root-draw",
                    "draw": "ph2TpgExtPhiEmuAm_phiBCMSSW>>AMtps_phiBCMSSW_wh{wh}_st{st}_q{q}(8194,-4097,4097)".format(wh=wh, st=st, q=q),
                    "selection": "ph2TpgExtPhiEmuAm_wheel=={wh} && ph2TpgExtPhiEmuAm_station=={st} && ph2TpgExtPhiEmuAm_quality=={q}".format(wh=wh, st=st, q=q),
                    "option": "goff"
                },
                # AM tps -theta features histograms
                f"nAMtps_theta_wh{wh}_st{st}_q{q}": {
                    "type" : "root-draw",
                    "draw": "ph2TpgThetaEmuAm_nTrigs>>nAMtps_theta_wh{wh}_st{st}_q{q}(100,0,100)".format(wh=wh, st=st, q=q),
                    "selection": "ph2TpgThetaEmuAm_wheel=={wh} && ph2TpgThetaEmuAm_station=={st} && ph2TpgThetaEmuAm_quality=={q}".format(wh=wh, st=st, q=q),
                    "option": "goff"
                },
                f"nAMtps_theta_goodBX_wh{wh}_st{st}_q{q}": {
                    "type" : "root-draw",
                    "draw": "ph2TpgThetaEmuAm_nTrigs>>nAMtps_theta_goodBX_wh{wh}_st{st}_q{q}(100,0,100)".format(wh=wh, st=st, q=q),
                    "selection": "ph2TpgThetaEmuAm_wheel=={wh} && ph2TpgThetaEmuAm_station=={st} && ph2TpgThetaEmuAm_quality=={q} && ph2TpgThetaEmuAm_BX==20".format(wh=wh, st=st, q=q),
                    "option": "goff"
                },
                f"AMtps_theta_z_wh{wh}_st{st}_q{q}": {
                    "type" : "root-draw",
                    "draw": "ph2TpgThetaEmuAm_z>>AMtps_theta_z_wh{wh}_st{st}_q{q}(131074,-65537,65537)".format(wh=wh, st=st, q=q),
                    "selection": "ph2TpgThetaEmuAm_wheel=={wh} && ph2TpgThetaEmuAm_station=={st} && ph2TpgThetaEmuAm_quality=={q}".format(wh=wh, st=st, q=q),
                    "option": "goff"
                },
                f"AMtps_theta_k_wh{wh}_st{st}_q{q}": {
                    "type" : "root-draw",
                    "draw": "ph2TpgThetaEmuAm_k>>AMtps_theta_k_wh{wh}_st{st}_q{q}(131074,-65537,65537)".format(wh=wh, st=st, q=q),
                    "selection": "ph2TpgThetaEmuAm_wheel=={wh} && ph2TpgThetaEmuAm_station=={st} && ph2TpgThetaEmuAm_quality=={q}".format(wh=wh, st=st, q=q),
                    "option": "goff"
                },
                f"AMtps_theta_BX_wh{wh}_st{st}_q{q}": {
                    "type" : "root-draw",
                    "draw": "ph2TpgThetaEmuAm_BX>>AMtps_theta_BX_wh{wh}_st{st}_q{q}(100,0,100)".format(wh=wh, st=st, q=q),
                    "selection": "ph2TpgThetaEmuAm_wheel=={wh} && ph2TpgThetaEmuAm_station=={st} && ph2TpgThetaEmuAm_quality=={q}".format(wh=wh, st=st, q=q),
                    "option": "goff"
                },
                # only available for extended dataformat
                f"AMtps_theta_zCMSSW_wh{wh}_st{st}_q{q}": {
                    "type" : "root-draw",
                    "draw": "ph2TpgExtThetaEmuAm_zCMSSW>>AMtps_theta_zCMSSW_wh{wh}_st{st}_q{q}(131074,-65537,65537)".format(wh=wh, st=st, q=q),
                    "selection": "ph2TpgExtThetaEmuAm_wheel=={wh} && ph2TpgExtThetaEmuAm_station=={st} && ph2TpgExtThetaEmuAm_quality=={q}".format(wh=wh, st=st, q=q),
                    "option": "goff"
                },
                f"AMtps_theta_kCMSSW_wh{wh}_st{st}_q{q}": {
                    "type" : "root-draw",
                    "draw": "ph2TpgExtThetaEmuAm_kCMSSW>>AMtps_theta_kCMSSW_wh{wh}_st{st}_q{q}(131074,-65537,65537)".format(wh=wh, st=st, q=q),
                    "selection": "ph2TpgExtThetaEmuAm_wheel=={wh} && ph2TpgExtThetaEmuAm_station=={st} && ph2TpgExtThetaEmuAm_quality=={q}".format(wh=wh, st=st, q=q),
                    "option": "goff"
                },
            })
