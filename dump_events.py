from dtpr.base.config import Config
from dtpr.base import NTuple
from dtpr.utils.dumper import dump_events
import os
import argparse as ap


parser = ap.ArgumentParser()
parser.add_argument("-cf", "--config-file", help="Path to the configuration file")
parser.add_argument("-i", "--inputs", nargs="+", help="Path to the input file")
parser.add_argument("-o", "--output", help="Path to the output file")
parser.add_argument("--maxevents", type=int, default=-1, help="Maximum number of events to process")
args = parser.parse_args()


def main():
    config_file_path = os.path.abspath(args.config_file)
    config = Config(config_file_path)

    ntuple = NTuple(args.inputs, CONFIG=config)
    events = ntuple.events[:args.maxevents] if args.maxevents > 0 else ntuple.events
    ForceRNTuple = False # Set to True if you want to force the use of RNTuple format for dumping events
    dump_events(events, args.output, fRNTuple=ForceRNTuple)


if __name__ == "__main__":
    main()
