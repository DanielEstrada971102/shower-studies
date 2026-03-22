from dtpr.base.config import RUN_CONFIG
from dtpr.base import NTuple
from dtpr.utils.dumper import dump_events
import os

def main():
    config_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "yamls/template_config.yaml"))
    input_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "ntuples", "DTDPGNtuple_12_4_2_Phase2Concentrator_thr6_Simulation_99.root"))

    RUN_CONFIG.change_config_file(config_file_path)

    ntuple = NTuple(input_file_path)

    dump_events(ntuple.events[:10], "test_dump_events_output.root")

if __name__ == "__main__":
    main()