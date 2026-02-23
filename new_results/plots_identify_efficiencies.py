import utils.root_plot_functions as rpf
from dtpr.utils.functions import color_msg, create_outfolder
import ROOT as r

in_folder = "."
out_folder = "./plots"

def identify_efficiency_graphs(tags, labels, inpath=f"{in_folder}/histograms"):
    graphs = []
    for tag, label in zip(tags, labels):
        with r.TFile.Open(f"{inpath}/histograms{tag}.root", "READ") as f:
            # gm showered that matches a shower / gm showered
            eff_ = r.TEfficiency(
                f.Get(f"shower_showeredgenmuon_tag_eff_pttrend_num"), 
                f.Get(f"shower_showeredgenmuon_tag_eff_pttrend_total")
            )
        graph = eff_.CreateGraph()
        for ibin in range(graph.GetN()):
            graph.SetPointEXhigh(ibin, 0)
            graph.SetPointEXlow(ibin, 0)

        graphs.append((graph, label))

    return graphs

def main():
    tags = ["_test2202"]#["_cmssw_nonn", "_jpp_nonn", "_jpp_nn"]#["", "_simhitsfilter", "_simhitsfilter_diffThrs", "_simhitsfilter_diffThrs_nn"]#, "_simhitsfilter_diffThrs_nn_covercell"]
    labels = ["just TPs geometry corrected"]#["cmssw_nonn", "jpp_nonn", "jpp_nn"]#["Nothing", "SimHits filter", "SimHits filter + diff. thresholds", "SimHits filter + diff. thresholds + NN filter"]#, "SimHits filter + diff. thresholds + NN filter + cover cell"]
    graphs = identify_efficiency_graphs(tags, labels)
    
    nBins = 50
    binFirst = 0
    binLast = 3335
    maxY = 1.1
    notes =  [
            ("Private work (#bf{CMS} Phase-2 Simulation)", (.08, .90, .5, .95), 0.03),
            ("200 PU", (.75, .90, .89, .95), 0.03),
    ]
    legend_pos=(0.3, 0.48, 0.44, 0.58)
    drawOption="pe1 same"
    titleX = "GenMuon Pt [GeV]"
    titleY = "Identification efficiency #scale[0.5]{#left[#frac{GenMuon showered identified}{GenMuon showered}#right]}"

    # Now plot the graphs
    rpf.plot_graphs(
        graphs = graphs, 
        name = "identify_efficiency_5",
        nBins = nBins, 
        firstBin = binFirst, 
        lastBin = binLast,
        maxY = maxY,
        notes = notes,
        legend_pos=legend_pos,
        drawOption=drawOption,
        titleX = titleX, 
        titleY = titleY,
        outfolder = out_folder,
        # repit_color_each=2,
    )

if __name__ == "__main__":
    create_outfolder(out_folder)
    main()