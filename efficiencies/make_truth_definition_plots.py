import ROOT as r
import dtpr.utils.root_plot_functions as rpf
from dtpr.utils.functions import color_msg


def main():
    folder = "."
    color_msg("Plotting", color="blue")

    graphs = []

    with r.TFile.Open(f"{folder}/histograms/histograms_thr6.root", "READ") as f:
        # gm showered / gm vs pt for the three methods
        eff_meth1 = r.TEfficiency(f.Get("showered_genmuon_meth1_num"), f.Get("showered_genmuon_meth1_total"))
        graph_meth1 = eff_meth1.CreateGraph()
        for ibin in range(graph_meth1.GetN()):
            graph_meth1.SetPointEXhigh(ibin, 0)
            graph_meth1.SetPointEXlow(ibin, 0)
        graphs.append((graph_meth1, "Method 1"))

        eff_meth2 = r.TEfficiency(f.Get("showered_genmuon_meth2_num"), f.Get("showered_genmuon_meth2_total"))
        graph_meth2 = eff_meth2.CreateGraph()
        for ibin in range(graph_meth2.GetN()):
            graph_meth2.SetPointEXhigh(ibin, 0)
            graph_meth2.SetPointEXlow(ibin, 0)
        graphs.append((graph_meth2, "Method 2"))

        eff_meth3 = r.TEfficiency(f.Get("showered_genmuon_meth3_num"), f.Get("showered_genmuon_meth3_total"))
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
        name = "genmuons_showered_tag_methods",
        nBins = nBins, 
        firstBin = binFirst, 
        lastBin = binLast,
        maxY = 1.1,
        notes =  [
            ("Private work (#bf{CMS} Phase-2 Simulation)", (.08, .90, .5, .95), 0.03),
            ("200 PU", (.75, .90, .89, .95), 0.03),
        ],
        legend_pos= (.6, .2, .75, .3),
        drawOption="pe1 same",
        titleX = "GenMuon Pt [GeV]", 
        titleY = "#frac{GenMuon showered}{GenMuon}",
        outfolder = "./plots",
    )

if __name__ == "__main__":
    main()