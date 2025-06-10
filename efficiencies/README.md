# Shower Efficiency Studies

In this section, the goal is to estimate an efficiency for the algorithm that generates the DT shower primitives.

It is important to consider that, since the algorithm is based on a simple count of hits arriving at the detector, it is quite common for some cases triggered as a shower not to necessarily correspond to events caused by radiation from a muon. Therefore, to evaluate this, it is worth defining what is considered a "real shower." This can be done with the module `shower_functions.py` using the function `build_real_showers`. A notion of a real shower can also be obtained from the muons generated with the module `dtpr.utils.genmuon_functions` using the method `analyze_genmuon_showers`.

### build_real_showers:
This function analyzes the `simhits` and `digis` at the Super Layer level of an event and constructs shower primitives based on their properties according to the following conditions:

* **cond 1**: The number of `simhits` in a SL exceeds a defined **threshold** (parameter).
* **cond 2**: At least 3 `simhits` in the SL are produced by interaction with a muon.
* **cond 3**: At least one `simhit` in the SL is produced by an electron (indicative of electromagnetic shower).
* **cond 4**: The distribution of the `wire` number of the `simhits` in a SL is sufficiently wide (evaluated through variance).
* **cond 5**: More than one `offline segment` in the same station matches the `generated muon`. (to fix)
* **cond 6**: The number of `digis` in a SL exceeds the **threshold** and their wire distribution is sufficiently wide.

Based on this, a `realshower` primitive is generated and assigned a type depending on which conditions are met:

* **type 1**: Conditions **1**, **2**, **3**, and **4** are met.
* **type 2**: Conditions **1**, **3**, and **4** are met.
* **type 3**: Conditions **1** and **5** are met.
* **type 4**: Condition **6** is met. (**DEPRECATED**)

The following confusion map shows the distribution of real showers by type, wheel, and station, using a `simhits` threshold of 8.

<div style="text-align: center;"><img src="./plots/confusion_maps/conf_map_real_shower_type_distributions.svg" width="50%"></div>

### analyze_genmuon_showers:
This function assigns a boolean `showered` tag to the generated muons, indicating whether the muon radiated or not, based on:

* **method 1**: The muon matches at least two `offline segments` in the same station.
* **method 2**: In any station the muon passes through, there are more than 8 `simhits` from electrons.

The difference between using one definition or another can be evaluated by plotting the fraction of generated muons that radiate as a function of their pt, depending on the real shower definition used. This is shown in the following graph:

<div style="text-align: center;"><img src="./plots/genmuons_showered_tag_methods/genmuons_showered_tag_methods.svg" width="50%"></div>

Additionally, a method 3 was added, which tags as showered those muons that match at least one of the real showers in any of the chambers they pass through.

## Efficiency Evaluation:
Showers are classified into categories based on the information from "real showers." True Positives (TP) are showers that match the position of a real shower, False Positives (FP) are showers that do not match a real shower, False Negatives (FN) are real showers not detected by the algorithm, and True Negatives (TN) are showers not detected by the algorithm and are not real showers. The statistical set includes all chambers where there is a shower (real or not) and chambers passed by a generated muon. (This is done with the function `get_locs_to_check` from the module `shower_histos.py`).

With this in mind, a confusion map of showers by station and wheel can be generated, as shown below, along with an efficiency plot by wheel and station.

<div style="text-align: center;"><img src="./plots/confusion_maps/conf_map_thr6_woutTN.svg" width="50%"></div>
<div style="text-align: center;"><img src="./plots/eff_fwshower/eff_fwshower.svg" width="50%"></div>
