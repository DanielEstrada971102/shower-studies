import os
import re
from single_agreement import make_dataframes, stimate_agreements
from pandas import DataFrame
from dtpr.utils.functions import create_outfolder

def make_agreements_summary_plot(agreements_df, save=False):
    import matplotlib.pyplot as plt
    import seaborn as sns

    # Group data by wheel and MB number
    agreements_df['MB'] = agreements_df['st']  # Assuming 'st' corresponds to MB number

    # Create boxplot
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(
        data=agreements_df,
        x=agreements_df['wh'].astype(str) + "_" + agreements_df['MB'].astype(str),
        y='station_agreement',
        ax=ax
    )

    # Customize x-axis
    ax.set_xticklabels(["-2", "-1", "0", "1", "2"] * 4)#, rotation=45)
    ax.set_xlabel("Wheel")
    ax.set_ylabel("Station Agreement")
    ax.set_title("Agreements Summary by Wheel and MB")

    if save:
        plt.savefig(os.path.join("agreements_summary.png"))
    else:
        plt.show()

def main():
    base_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "showers-data2/")
    results_dir = os.path.join(base_dir, "agreements_results/")

    create_outfolder(results_dir)

    # scan directory to know which wh, sc, st to use
    _agreements_data = []
    _anomalous_data = set()
    for file in os.scandir(os.path.join(base_dir, "Input_CMSSW/digis_IN_FPGA")):
        if file.is_file() and file.name.endswith(".txt"):
            # Extract wh, sc, st from filename
            match = re.search(r"wh(-?\d+)_sc(\d+)_st(\d+)", file.name)
            if match:
                wh, sc, st = map(int, match.groups())
            else:
                continue
            print(f"Processing: wh={wh}, sc={sc}, st={st}")
            cmssw_hits_in, fpga_hits_in, cmssw_showers, fpga_showers = make_dataframes(base_dir, wh, sc, st)
            _agreements = stimate_agreements(fpga_showers, cmssw_showers, cmssw_hits_in, fpga_hits_in)

            if all([x is not None for x in _agreements]):
                SL1_agreement, SL3_agreement, station_agreement, err_station_agreement = _agreements
                _agreements_data.append({
                    "wh": wh,
                    "sc": sc,
                    "st": st,
                    "SL1_agreement": SL1_agreement,
                    "SL3_agreement": SL3_agreement,
                    "station_agreement": station_agreement,
                    "err_station_agreement": err_station_agreement
                })
            else:
                _anomalous_data.add((wh, sc, st))

    # Create DataFrames
    agreements_df = DataFrame(_agreements_data)
    anomalous_df = DataFrame(_anomalous_data, columns=["wh", "sc", "st"])

    # # Save DataFrames to CSV
    # agreements_df.to_csv(os.path.join(results_dir, "agreements.csv"), index=False)
    # anomalous_df.to_csv(os.path.join(results_dir, "anomalous.csv"), index=False)

    make_agreements_summary_plot(agreements_df, save=False)

if __name__ == "__main__":
    main()