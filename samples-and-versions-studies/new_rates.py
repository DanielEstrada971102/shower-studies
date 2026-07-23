import uproot
import matplotlib.pyplot as plt
import mplhep as hep
plt.style.use(hep.styles.CMS)

def main():
    stations = [1, 2, 3, 4]
    wheels = [-2, -1, 0, 1, 2]
    
    histos_mb_v1 = uproot.open("histograms/histograms_mb_v1.root")
    histos_mb_v1p2 = uproot.open("histograms/histograms_mb_v1p2.root")

    mb_v1_nevents = 1994560
    mb_v1p2_nevents = 1994560

    Luminosity = 2760 * 11246  # in pb^-1


    v1_data = []
    v1p2_data = []
    v1_gbx_data = []
    v1p2_gbx_data = []
    am_v1p2_data = []
    am_v1p2_gbx_data = []

    tick_positions = []
    tick_labels = []

    # 1. Collect data
    current_pos = 0

    for st in stations:
        for wh in wheels:
            key = "nshowers_wh{wh}_st{st}{GOODBX};1"

            v1_data.append(histos_mb_v1[key.format(wh=wh, st=st, GOODBX="")].to_hist().sum() * 1 / mb_v1_nevents * Luminosity)
            v1p2_data.append(histos_mb_v1p2[key.format(wh=wh, st=st, GOODBX="")].to_hist().sum() * 1 / mb_v1p2_nevents * Luminosity)
            v1_gbx_data.append(histos_mb_v1[key.format(wh=wh, st=st, GOODBX="_goodBX")].to_hist().sum() * 1 / mb_v1_nevents * Luminosity)
            v1p2_gbx_data.append(histos_mb_v1p2[key.format(wh=wh, st=st, GOODBX="_goodBX")].to_hist().sum() * 1 / mb_v1p2_nevents * Luminosity)

            key_am = "nAMtps_phi{GOODBX}_wh{wh}_st{st}_q{q};1"
            
            am_v1p2_data.append(sum([histos_mb_v1p2[key_am.format(wh=wh, st=st, GOODBX="", q=q)].to_hist() for q in [-1, 1, 2, 3, 4, 6, 7, 8]]).sum() * 1 / mb_v1p2_nevents * Luminosity)
            am_v1p2_gbx_data.append(sum([histos_mb_v1p2[key_am.format(wh=wh, st=st, GOODBX="_goodBX", q=q)].to_hist() for q in [-1, 1, 2, 3, 4, 6, 7, 8]]).sum() * 1 / mb_v1p2_nevents * Luminosity)

            tick_positions.append(current_pos)
            tick_labels.append(f"{wh}")
            current_pos += 1
        current_pos += 0.5 

    fig, ax = plt.subplots(figsize=(10, 10))

    # Plot boxplot on the left
    # ax.scatter(tick_positions, v1_data, color='blue', label="Version 1")
    ax.scatter(tick_positions, v1p2_data, color='red', label="Showers")
    ax.scatter(tick_positions, am_v1p2_data, color='k', label="AM")
    # ax.scatter(tick_positions, v1_gbx_data, color='blue', marker='x', label="Version 1 (good BX)")
    ax.scatter(tick_positions, v1p2_gbx_data, color='red', marker='x', label="Showers (good BX)")
    ax.scatter(tick_positions, am_v1p2_gbx_data, color='k', marker='x', label="AM (good BX)")

    # 4. Axes, Labels and CMS style
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels)
    ax.tick_params(axis="both", labelsize=18)
    ax.set_yscale('log')
    ax.set_ylim(1, 1e8)
    ax.set_ylabel("DT local trigger rate [Hz]", fontsize=18)
    ax.set_xlabel("Wheel", fontsize=18)
    ax.set_title("MB sample - Version 1.2", fontsize=20, pad=40)
    # Station Labels
    for i, st in enumerate(stations):
        center = (i * 5.5) + 2
        ax.text(center, ax.get_ylim()[0] + (ax.get_ylim()[1]*1e-5), f"MB{st}", 
                ha='center', fontsize=20, fontweight='bold')
        if i < len(stations) - 1:
            ax.axvline((i * 5.5) + 4.75, color="black", linestyle="--", alpha=0.5)

    ax.legend(loc='best', fontsize=20)
    # fig.patch.set_alpha(0)
    # ax.set_facecolor((245/255, 247/255, 248/255))
    hep.cms.label(ax=ax, text="(Private work)", data=False, rlabel="1E34   PU200", fontsize=18)
    plt.tight_layout()
    fig.savefig("rates.svg")
    # plt.show()


if __name__ == "__main__":
    main()