from dtpr.base import NTuple
from dtpr.utils.config import RUN_CONFIG
from dtpr.utils.functions import color_msg
from pandas import DataFrame
from tqdm import tqdm

def matches(shower, is_true=True, match_amtps=False, highpt_gm=False, highpt_threshold=100):
    if shower.is_true_shower != is_true:
        return False
    if match_amtps and not shower.matched_tps:
        return False
    if highpt_gm:
        return (
            shower.matched_tps and
            any(
                gm.pt > highpt_threshold
                for tp in shower.matched_tps
                for gm in getattr(tp, "matched_genmuons", [])
            )
        )
    return True

def count_showers(event, **kwargs):
    return sum(1 for shower in getattr(event, "fwshowers", []) if matches(shower, **kwargs))

def get_values_of_event(event):
    output = {
        "tpshowers": count_showers(event, is_true=True),
        "fpshowers": count_showers(event, is_true=False),
        "tpshowers_that_matches_amtp": count_showers(event, is_true=True, match_amtps=True),
        "fpshowers_that_matches_amtp": count_showers(event, is_true=False, match_amtps=True),
        "tpshowers_that_matches_amtp_and_hightpt_gm": count_showers(event, is_true=True, match_amtps=True, highpt_gm=True),
        "fpshowers_that_matches_amtp_and_hightpt_gm": count_showers(event, is_true=False, match_amtps=True, highpt_gm=True),
    }
    return output

def report_results(results):
    sums = results.sum()
    color_msg("-------- Results summary --------", color="yellow", indentLevel=1)

    total_showers = sums['tpshowers'] + sums['fpshowers']
    color_msg(f"Total events processed: {len(results)}", color="purple", indentLevel=2)
    color_msg(f"Total showers: {sums['tpshowers'] + sums['fpshowers']}\n", color="purple", indentLevel=2)
    color_msg(f"True Positive showers: {sums['tpshowers']} ({sums['tpshowers'] / total_showers * 100:.2f}%)", color="purple", indentLevel=2)
    color_msg(f"False Positive showers: {sums['fpshowers']} ({sums['fpshowers'] / total_showers * 100:.2f}%)", color="purple", indentLevel=2)
    color_msg(f"TP showers matching AMTP: {sums['tpshowers_that_matches_amtp']}", color="purple", indentLevel=2)
    color_msg(f"rel. all showers : ({sums['tpshowers_that_matches_amtp'] / total_showers * 100:.2f}%)", color="cyan", indentLevel=3)
    color_msg(f"rel. TP showers : ({sums['tpshowers_that_matches_amtp'] / sums['tpshowers'] * 100:.2f}%)", color="cyan", indentLevel=3)
    color_msg(f"FP showers matching AMTP: {sums['fpshowers_that_matches_amtp']}", color="purple", indentLevel=2)
    color_msg(f"rel. all showers : ({sums['fpshowers_that_matches_amtp'] / total_showers * 100:.2f}%)", color="cyan", indentLevel=3)
    color_msg(f"rel. FP showers : ({sums['fpshowers_that_matches_amtp'] / sums['fpshowers'] * 100:.2f}%)", color="cyan", indentLevel=3)
    color_msg(f"TP showers matching AMTP and high pt GenMuon: {sums['tpshowers_that_matches_amtp_and_hightpt_gm']}", color="purple", indentLevel=2)
    color_msg(f"rel. all showers : ({sums['tpshowers_that_matches_amtp_and_hightpt_gm'] / total_showers * 100:.2f}%)", color="purple", indentLevel=3)
    color_msg(f"rel. TP showers : ({sums['tpshowers_that_matches_amtp_and_hightpt_gm'] / sums['tpshowers'] * 100:.2f}%)", color="purple", indentLevel=3)
    color_msg(f"FP showers matching AMTP and high pt GenMuon: {sums['fpshowers_that_matches_amtp_and_hightpt_gm']} ({sums['fpshowers_that_matches_amtp_and_hightpt_gm'] / total_showers * 100:.2f}%)", color="purple", indentLevel=2)
    color_msg(f"rel. all showers : ({sums['fpshowers_that_matches_amtp_and_hightpt_gm'] / total_showers * 100:.2f}%)", color="purple", indentLevel=3)
    color_msg(f"rel. FP showers : ({sums['fpshowers_that_matches_amtp_and_hightpt_gm'] / sums['fpshowers'] * 100:.2f}%)", color="purple", indentLevel=3)

def main():
    RUN_CONFIG.change_config_file("./run_config.yaml")
    ntuple = NTuple("../../ZprimeToMuMu_M-6000_TuneCP5_14TeV-pythia8/ZprimeToMuMu_M-6000_PU200/250312_131631/0000")
    total = len(ntuple.events) # 10
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

            results.append(get_values_of_event(ev))

    df = DataFrame(results)
    report_results(df)

if __name__ == "__main__":
    import timeit

    print(timeit.timeit(main, number=1))