"""" Plotting script """
from dtpr.utils.functions import color_msg
from dtpr.utils.root_plot_functions import *


def main():    
    # --- Files to be used --- #
    folder = "."
    color_msg("Plotting fwShower efficiency after filter", color="blue")

    info_for_plots = [
        { 
            "file_name": f"{folder}/histograms/histograms_nmsfiltered.root",
            "histos_names": "Fwshower_eff_MBX",
            "legends": "After Filter",
        },
        { 
            "file_name": f"{folder}/../efficiencies/histograms/histograms_thr_rsfix6.root",
            "histos_names": "Fwshower_eff_MBX",
            "legends": "Before Filter",
        }
    ]

    make_plots(
        info_for_plots=info_for_plots,
        output_name = "eff_fwshower_nmsfiltered",
        outfolder=folder+"/plots",
        legend_pos=(0.7, 0.48, 0.84, 0.6),
        titleY="Shower Trigger Efficiency #scale[0.7]{#left[#frac{TP + TN}{TP + FP + FN + TN}#right]}",
        # aditional_notes=[("(TP + TN) / (TP + TN + FP + FN)", (.44, .38, .5, .47), 0.03)]
    )

    color_msg("Done!", color="green")


if __name__ == "__main__":
    main()
