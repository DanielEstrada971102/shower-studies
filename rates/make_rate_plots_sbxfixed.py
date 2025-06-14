from dtpr.utils.functions import color_msg
from dtpr.utils.root_plot_functions import *

def main():
    # --- Files to be used --- #
    folder = "."

    color_msg("Plotting rates", color="blue")

    # ------------------------------ all bx plot ------------------------------ #
    info_for_plots_allbx = [
        {
            "file_name": f"{folder}/histograms/histograms_sbxfix_thr6.root",
            "histos_names": ["Rate_allBX_MBX_AM", "Rate_goodBX_MBX_AM", "Rate_allBX_MBX_FwShower", "Rate_goodBX_MBX_FwShower"],
            "legends": ["AM all BX", "AM good BX", "Showers all BX", "Showers good BX"],
        }
    ]

    make_plots(
        info_for_plots=info_for_plots_allbx,
        type="histo",
        titleY="DT Local Trigger Rate (Hz)",
        output_name = "showerrate_sbxfixed",
        outfolder=folder + "/rate_plots_sbxfixed", 
        logy=True,
        scaling= (1/1929240) * 2760 * 11246, #(1/1565520) * 2760 * 11246,
        repite_color_each=2,
        legend_pos=(0.14, 0.42, 0.30, 0.56),
        maxY=1e8,
    )

    # # ------------------------------ good bx plot ------------------------------ #
    # info_for_plots_goodbx = [
    #     { 
    #         "file_name": f"{folder}/histograms/histograms_sbxfix_thr6.root",
    #         "histos_names": ["Rate_goodBX_MBX_AM", "Rate_goodBX_MBX_FwShower"],
    #         "legends": [f"AM", f"Showers Algo"],
    #     }
    # ]

    # make_plots(
    #     info_for_plots=info_for_plots_goodbx,
    #     type="histo",
    #     titleY="DT Local Trigger Rate (Hz)",
    #     output_name = "showerrate_goodbx_sbxfixed",
    #     outfolder=folder + "/rate_plots_sbxfixed", 
    #     logy=True,
    #     scaling= (1/1929240) * 2760 *11246, #(1/10000) * 2760 * 11246,
    #     # repite_color_each=2,
    #     legend_pos=(0.67, 0.38, 0.87, 0.44),
    #     maxY=1e8,
    # )

if __name__ == "__main__":
    main()