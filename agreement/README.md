# Shower Agreement Studies

This project aims to evaluate whether the CMSSW shower emulator can reproduce the primitives expected from BMTL1. To achieve this, the repository `../fpga_showers` is included as a submodule, containing the Vivado simulator for the shower algorithm. The simulator takes hits as input based on BX in a specific format, which can be generated using the script `dumpers/digis_showers_dumper.py`. (This version fails to reproduce the hits taken by the CMSSW emulator, so it is recommended to obtain them directly from the emulator by enabling the `debug` flag, which activates the method [`dump_digis_to_file`](https://github.com/DanielEstrada971102/cmssw/blob/7d539b8d6d0334a8c79159e5cdc1019613af3305/L1Trigger/DTTriggerPhase2/src/ShowerBuilder.cc#L302)). This script also extracts shower information for comparison with the simulator's results.

On the other hand, with the input hits in the correct format, the shower simulator is executed through the script `dumpers/fw_digis_showers_dumper.py`. This produces several log files indicating the hits received for constructing each shower.

Finally, based on the output files from both the simulator and the emulator, the scripts `single_agreement.py` and `all_agreement.py` can be used to estimate the desired agreement.

Preliminary results with a sample of ~400 events showed that the CMSSW shower emulator produces slightly more showers than the firmware. However, overall agreement is quite good, estimated at $96\pm1$%.

