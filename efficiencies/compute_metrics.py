"""
This code intends to adapt the histograms which only have tp, fp, tn, fn values to histograms which
have the metrics (accuracy, precision, recall, f1-score) computed and stored in them. The new 
histograms will be stored in the same file as the original ones.
"""

import ROOT as r

def extend_histos(file_path, histo_name_template):
    f = r.TFile.Open(file_path, "UPDATE")

    pre, pos = histo_name_template.split("MB")

    for iStation in range(1, 5):
        histos = {
            "acc": [
                r.TH1I(f"Fwshower_acc_MB{iStation}_num", "", 5, -2.5 , 2.5),
                r.TH1I(f"Fwshower_acc_MB{iStation}_total", "", 5, -2.5 , 2.5)
            ],
            "precision": [
                r.TH1I(f"Fwshower_precision_MB{iStation}_num", "", 5, -2.5 , 2.5),
                r.TH1I(f"Fwshower_precision_MB{iStation}_total", "", 5, -2.5 , 2.5)
            ],
            "recall": [
                r.TH1I(f"Fwshower_recall_MB{iStation}_num", "", 5, -2.5 , 2.5),
                r.TH1I(f"Fwshower_recall_MB{iStation}_total", "", 5, -2.5 , 2.5)
            ],
            "f1-score": [
                r.TH1I(f"Fwshower_f1score_MB{iStation}_num", "", 5, -2.5 , 2.5),
                r.TH1I(f"Fwshower_f1score_MB{iStation}_total", "", 5, -2.5 , 2.5)
            ]
        }
        for iWheel in range(1, 6):
            h2 = f.Get(f"{pre}MB{iStation}{pos[1:]}")

            # 1. Extract values from TH2 bins
            tp = h2.GetBinContent(iWheel, 1)
            fp = h2.GetBinContent(iWheel, 2)
            tn = h2.GetBinContent(iWheel, 3)
            fn = h2.GetBinContent(iWheel, 4)

            # accuracy = (TP + TN) / total
            histos["acc"][0].SetBinContent(iWheel, tp + tn)
            histos["acc"][1].SetBinContent(iWheel, tp + fp + tn + fn)

            # precision = TP / (TP + FP)
            histos["precision"][0].SetBinContent(iWheel, tp)
            histos["precision"][1].SetBinContent(iWheel, tp + fp)

            # recall = TP / (TP + FN)
            histos["recall"][0].SetBinContent(iWheel, tp)
            histos["recall"][1].SetBinContent(iWheel, tp + fn)

            # f1-score = 2 * (precision * recall) / (precision + recall)
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

            histos["f1-score"][0].SetBinContent(iWheel, f1_score)
            histos["f1-score"][1].SetBinContent(iWheel, 1)

        # Write histograms to file
        for metric, histo_pair in histos.items():
            histo_pair[0].Write()
            histo_pair[1].Write()

    f.Close()


def main():
    file_path = "histograms/histograms_dy_C.root"
    histo_name_template = "shower_tpfptnfn_MBX"

    extend_histos(file_path, histo_name_template)

if __name__ == "__main__":
    main()