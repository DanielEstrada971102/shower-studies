from dtpr.base import NTuple
from dtpr.utils.config import RUN_CONFIG
from dtpr.utils.functions import color_msg
from pandas import DataFrame
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np


def match_shower_genmuons(shower, highpt_threshold=100):
    """
    Matches the shower with genmuons and returns the matched genmuons.
    """
    matched_genmuons = [gm for tp in shower.matched_tps for gm in tp.matched_genmuons]
    shower.matched_genmuons = matched_genmuons
    for gm in matched_genmuons:
        if hasattr(gm, 'matched_showers') and shower not in gm.matched_showers:
            gm.matched_showers.append(shower)
        else:
            gm.matched_showers = [shower]

    shower.is_highpt_shower = True if any(gm.pt > highpt_threshold for gm in matched_genmuons) else False

# ----- This is to be used as preprocesor function in the config file -----

def highpt_showers_identifier(event, highpt_threshold=100):
    """
    Identifies high pt showers in the event.
    """
    for shower in event.fwshowers:
        match_shower_genmuons(shower, highpt_threshold)

# ------------------------------------------------------------------------

def classify_showers(event):
    """
    Summarizes shower data for an event.
    """
    summary = {
        "tp": 0,
        "tp_matched_amtp": 0,
        "tp_matched_amtp_highpt": 0,
        "tp_matched_amtp_not_highpt": 0,
        "tp_not_matched_amtp": 0,
        "tp_not_matched_amtp_highpt": 0,
        "tp_not_matched_amtp_not_highpt": 0,
        "fp": 0,
        "fp_matched_amtp": 0,
        "fp_matched_amtp_highpt": 0,
        "fp_matched_amtp_not_highpt": 0,
        "fp_not_matched_amtp": 0,
        "fp_not_matched_amtp_highpt": 0,
        "fp_not_matched_amtp_not_highpt": 0
    }

    for shower in event.fwshowers:
        key = "tp" if shower.is_true_shower else "fp"
        summary[key] += 1
        key = f"{key}_matched_amtp" if shower.matched_tps else f"{key}_not_matched_amtp"
        summary[key] += 1
        key = f"{key}_highpt" if shower.is_highpt_shower else f"{key}_not_highpt"
        summary[key] += 1

    return summary

def report_results(results):
    sums = results.sum()

    print(sums)

    tab20c = plt.get_cmap("tab20c")
    tab20b = plt.get_cmap("tab20b")
    size = 0.3

    # Outer pie
    outer_pie_vals = [sums['tp'], sums['fp']]
    outer_pie_labels = ['True Positive', 'False Positive']
    outer_pie_colors = [tab20c(0), tab20c(4)]

    # Middle pie
    middle_pie_vals = [sums['tp_matched_amtp'], sums['tp_not_matched_amtp'], sums['fp_matched_amtp'], sums['fp_not_matched_amtp']]
    middle_pie_labels = ['TP Matched AMTP', 'TP Not Matched AMTP', 'FP Matched AMTP', 'FP Not Matched AMTP']
    middle_pie_colors = [tab20c(1), tab20b(1), tab20c(5), tab20b(5)]

    # Inner pie
    inner_pie_vals = [
        sums['tp_matched_amtp_highpt'], sums['tp_matched_amtp_not_highpt'],
        sums['tp_not_matched_amtp_highpt'], sums['tp_not_matched_amtp_not_highpt'],
        sums['fp_matched_amtp_highpt'], sums['fp_matched_amtp_not_highpt'],
        sums['fp_not_matched_amtp_highpt'], sums['fp_not_matched_amtp_not_highpt']
    ]
    inner_pie_labels = ['TP Matched High Pt', 'TP Matched Not High Pt', 'TP Not Matched High Pt', 'TP Not Matched Not High Pt',
                        'FP Matched High Pt', 'FP Matched Not High Pt', 'FP Not Matched High Pt', 'FP Not Matched Not High Pt']
    inner_pie_colors = [tab20c(2), tab20c(3), tab20b(2), tab20b(3), tab20c(6), tab20c(7), tab20b(6), tab20b(7)]

    fig, ax = plt.subplots(figsize=(10, 10))

    # Outer pie chart
    _,label_text_out,number_text_out = ax.pie(
        outer_pie_vals, radius=1, colors=outer_pie_colors,
        wedgeprops=dict(width=size, edgecolor='w'), labels=outer_pie_labels,
        autopct=lambda pct: f"{pct:.1f}%" if pct > 0 else "",
        pctdistance=0.85,
    )

    # Middle pie chart
    _,_,number_text_mid = ax.pie(
        middle_pie_vals, radius=1-size, colors=middle_pie_colors,
        wedgeprops=dict(width=size, edgecolor='w'), labels=middle_pie_labels,
        autopct=lambda pct: f"{pct:.1f}%" if pct > 0 else "",
        pctdistance=0.75,
        labeldistance=None,
    )

    # Inner pie chart
    _,_,number_text_in = ax.pie(
        inner_pie_vals, radius=1-2*size, colors=inner_pie_colors,
        wedgeprops=dict(width=size, edgecolor='w'), labels=inner_pie_labels,
        autopct=lambda pct: f"{pct:.1f}%" if pct > 0 else "",
        pctdistance=0.5,
        labeldistance=None,
    )

    for txt in label_text_out:
        txt.set_fontweight('bold')
    for txt in number_text_in:
        txt.set_fontweight('bold')
    for txt in number_text_mid:
        txt.set_fontweight('bold')
    for txt in number_text_out:
        txt.set_color('white')
        txt.set_fontweight('bold')

    # Adjust legend for nested style
    ax.legend(
        # handles=[
        #     plt.Line2D([0], [0], color=tab20c(0), lw=4, label='Outer: True Positive'),
        #     plt.Line2D([0], [0], color=tab20c(4), lw=4, label='Outer: False Positive'),
        #     plt.Line2D([0], [0], color=tab20c(1), lw=4, label='Middle: TP Matched AMTP'),
        #     plt.Line2D([0], [0], color=tab20b(1), lw=4, label='Middle: TP Not Matched AMTP'),
        #     plt.Line2D([0], [0], color=tab20c(5), lw=4, label='Middle: FP Matched AMTP'),
        #     plt.Line2D([0], [0], color=tab20b(5), lw=4, label='Middle: FP Not Matched AMTP'),
        #     plt.Line2D([0], [0], color=tab20c(2), lw=4, label='Inner: TP Matched High Pt'),
        #     plt.Line2D([0], [0], color=tab20c(3), lw=4, label='Inner: TP Matched Not High Pt'),
        #     plt.Line2D([0], [0], color=tab20b(2), lw=4, label='Inner: TP Not Matched High Pt'),
        #     plt.Line2D([0], [0], color=tab20b(3), lw=4, label='Inner: TP Not Matched Not High Pt'),
        #     plt.Line2D([0], [0], color=tab20c(6), lw=4, label='Inner: FP Matched High Pt'),
        #     plt.Line2D([0], [0], color=tab20c(7), lw=4, label='Inner: FP Matched Not High Pt'),
        #     plt.Line2D([0], [0], color=tab20b(6), lw=4, label='Inner: FP Not Matched High Pt'),
        #     plt.Line2D([0], [0], color=tab20b(7), lw=4, label='Inner: FP Not Matched Not High Pt')
        # ],
        loc='center left', bbox_to_anchor=(1, 0, 0.5, 1),
        # title='Showers Classification (Nested)',
        fontsize=10, title_fontsize=12
    )
    ax.set(aspect="equal", title='Showers Classification')
    plt.tight_layout()
    fig.savefig("showers_classification_pie_chart_80PTthr.svg", dpi=300)

def main():
    RUN_CONFIG.change_config_file("./run_config.yaml")
    ntuple = NTuple("/lustrefs/hdd_pool_dir/L1T/Filter/ThresholdScan_Zprime_DY/last/ZprimeToMuMu_M-6000_PU200/250312_131631/0000")
    total = len(ntuple.events)
    # total = 10
    results = []
    with tqdm(
        total=total,
        desc=color_msg(
            "Running:", color="purple", indentLevel=1, return_str=True
        ),
        ncols=100,
        ascii=True,
        unit=" event",
    ) as pbar:
        for ev in ntuple.events:
            if not ev:
                continue
            if not ev.tps:
                continue
            if not ev.fwshowers:
                continue
            if total < 10:
                pbar.update(1)
            elif ev.index % (total // 10) == 0:
                pbar.update(total // 10)
            if ev.index > total:
                break

            # highpt_showers_identifier(ev, highpt_threshold=100)
            results.append(classify_showers(ev))

    df = DataFrame(results)
    report_results(df)

if __name__ == "__main__":
    import timeit

    print(timeit.timeit(main, number=1))




    # color_msg("-------- Results summary --------", color="yellow", indentLevel=1)

    # total_showers = sums['tpshowers'] + sums['fpshowers']
    # color_msg(f"Total events processed: {len(results)}", color="purple", indentLevel=2)
    # color_msg(f"Total showers: {sums['tpshowers'] + sums['fpshowers']}\n", color="purple", indentLevel=2)
    # color_msg(f"True Positive showers: {sums['tpshowers']} ({sums['tpshowers'] / total_showers * 100:.2f}%)", color="purple", indentLevel=2)
    # color_msg(f"False Positive showers: {sums['fpshowers']} ({sums['fpshowers'] / total_showers * 100:.2f}%)", color="purple", indentLevel=2)
    # color_msg(f"TP showers matching AMTP: {sums['tpshowers_that_matches_amtp']}", color="purple", indentLevel=2)
    # color_msg(f"rel. all showers : ({sums['tpshowers_that_matches_amtp'] / total_showers * 100:.2f}%)", color="cyan", indentLevel=3)
    # color_msg(f"rel. TP showers : ({sums['tpshowers_that_matches_amtp'] / sums['tpshowers'] * 100:.2f}%)", color="cyan", indentLevel=3)
    # color_msg(f"FP showers matching AMTP: {sums['fpshowers_that_matches_amtp']}", color="purple", indentLevel=2)
    # color_msg(f"rel. all showers : ({sums['fpshowers_that_matches_amtp'] / total_showers * 100:.2f}%)", color="cyan", indentLevel=3)
    # color_msg(f"rel. FP showers : ({sums['fpshowers_that_matches_amtp'] / sums['fpshowers'] * 100:.2f}%)", color="cyan", indentLevel=3)
    # color_msg(f"TP showers matching AMTP and high pt GenMuon: {sums['tpshowers_that_matches_amtp_and_highpt_gm']}", color="purple", indentLevel=2)
    # color_msg(f"rel. all showers : ({sums['tpshowers_that_matches_amtp_and_highpt_gm'] / total_showers * 100:.2f}%)", color="purple", indentLevel=3)
    # color_msg(f"rel. TP showers : ({sums['tpshowers_that_matches_amtp_and_highpt_gm'] / sums['tpshowers'] * 100:.2f}%)", color="purple", indentLevel=3)
    # color_msg(f"FP showers matching AMTP and high pt GenMuon: {sums['fpshowers_that_matches_amtp_and_highpt_gm']} ({sums['fpshowers_that_matches_amtp_and_highpt_gm'] / total_showers * 100:.2f}%)", color="purple", indentLevel=2)
    # color_msg(f"rel. all showers : ({sums['fpshowers_that_matches_amtp_and_highpt_gm'] / total_showers * 100:.2f}%)", color="purple", indentLevel=3)
    # color_msg(f"rel. FP showers : ({sums['fpshowers_that_matches_amtp_and_highpt_gm'] / sums['fpshowers'] * 100:.2f}%)", color="purple", indentLevel=3)
