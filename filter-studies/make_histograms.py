import dtpr.utils.root_plot_functions as rpf
from dtpr.utils.functions import color_msg

def main():
    folder = "."
    color_msg("Plotting", color="blue")

    rpf.make_plots(
        info_for_plots=[{ 
            "file_name": f"{folder}/histograms/histograms.root",
            "histos_names": "tps_match_showers_MBX_AM",
            "legends":  "#frac{AM TPs that match any shower}{AM TPs}",
        }],
        output_name = "tps_shower_match_ratio",
        outfolder=folder + "plots/",
        legend_pos=(0.5, 0.48, 0.54, 0.6),
        titleY="",
        logy=True,
    )

    rpf.make_plots(
        info_for_plots=[{ 
            "file_name": f"{folder}/histograms/histograms.root",
            "histos_names": "matched_tps_MBX_AM",
            "legends":  "#frac{AM TPs that match a real shower}{AM TPs that match a shower}",
        }],
        output_name = "matched_tps_ratio",
        outfolder=folder + "plots/",
        legend_pos=(0.5, 0.48, 0.54, 0.6),
        titleY=""
    )

    rpf.make_plots(
        info_for_plots=[{ 
            "file_name": f"{folder}/histograms/histograms.root",
            "histos_names": ["tps_q<6_MBX", "tps_q>6_MBX"],
            "legends":  ["AM TP - q < 6", "AM TP - q > 6"],
        }],
        output_name = "tps",
        outfolder=folder + "plots/",
        legend_pos=(0.5, 0.48, 0.54, 0.6),
        titleY="Number of AM TPs",
        type="histo",
        maxY=600,
    )

    rpf.make_plots(
        info_for_plots=[{ 
            "file_name": f"{folder}/histograms/histograms.root",
            "histos_names": ["shower_MBX", "shower_true_MBX"],
            "legends":  ["showers", "True showers"],
        }],
        output_name = "showers",
        outfolder=folder + "plots/",
        legend_pos=(0.5, 0.48, 0.54, 0.6),
        titleY="Number of showers",
        type="histo",
        maxY=50,
    )

    color_msg("Done!", color="green")

if __name__ == "__main__":
    main()