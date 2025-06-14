import dtpr.utils.root_plot_functions as rpf
from dtpr.utils.functions import color_msg
import ROOT as r

def main():
    folder = "."
    color_msg("Plotting", color="blue")
    graphs = []

    with r.TFile.Open(f"{folder}/histograms/histograms_1106.root", "READ") as f:
        # gm showered that matches a shower / gm showered
        eff_ = r.TEfficiency(f.Get("shower_showeredgenmuon_tag_eff_pttrend_num"), f.Get("shower_showeredgenmuon_tag_eff_pttrend_total"))
        graph = eff_.CreateGraph()
        for ibin in range(graph.GetN()):
            graph.SetPointEXhigh(ibin, 0)
            graph.SetPointEXlow(ibin, 0)

        graphs.append((graph, "Method 2"))

        # gm showered that matches a shower / gm showered (method 3)
        eff_meth3 = r.TEfficiency(f.Get("shower_showeredgenmuon_tag_eff_pttrend_mth3_num"), f.Get("shower_showeredgenmuon_tag_eff_pttrend_mth3_total"))
        graph_meth3 = eff_meth3.CreateGraph()
        for ibin in range(graph_meth3.GetN()):
            graph_meth3.SetPointEXhigh(ibin, 0)
            graph_meth3.SetPointEXlow(ibin, 0)
        graphs.append((graph_meth3, "Method 3"))

    nBins = 50
    binFirst = 0
    binLast = 3335

    # Now plot the graphs
    rpf.plot_graphs(
        graphs = graphs, 
        name = "filter_genmuons_shower_tag_2",
        nBins = nBins, 
        firstBin = binFirst, 
        lastBin = binLast,
        maxY = 1.1,
        notes =  [
            ("Private work (#bf{CMS} Phase-2 Simulation)", (.08, .90, .5, .95), 0.03),
            ("200 PU", (.75, .90, .89, .95), 0.03),
        ],
        legend_pos=(0.3, 0.68, 0.44, 0.78),
        drawOption="pe1 same",
        titleX = "GenMuon Pt [GeV]", 
        titleY = "#frac{GenMuon showered identified}{GenMuon showered}",
        outfolder = "./plots",
    )

    # rpf.make_plots(
    #     info_for_plots=[{ 
    #         "file_name": f"{folder}/histograms/histograms_genmuons.root",
    #         "histos_names": ["shower_matchAmTP_eff_MBX", "shower_matchHighPtmuon_eff_MBX", "shower_matchshoweredgenmuon_eff_MBX"],
    #         "legends":  ["Shower that matches AM TP", "Shower that matches high PT genmuon", "Shower that matches showered genmuon"],
    #     }],
    #     output_name = "showers_matches",
    #     outfolder=folder + "/plots",
    #     legend_pos=(0.5, 0.48, 0.54, 0.6),
    #     titleY="",
    #     # logy=True,
    # )

    color_msg("Done!", color="green")

if __name__ == "__main__":
    main()