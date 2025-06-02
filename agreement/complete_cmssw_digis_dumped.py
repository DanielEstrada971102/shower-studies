import os
import sys
from dtpr.base import NTuple
from dtpr.utils.config import RUN_CONFIG
from dtpr.utils.functions import color_msg

import pandas as pd

inpath = "./ntuple4aggreement.root"
dumped_digis_folder = "./digis_dumped_ntuple4agreement"
RUN_CONFIG.change_config_file(config_path="./run_config.yaml")

os.makedirs("./digis_dumped_ntuple4agreement_remade", exist_ok=True)

color_msg(f"Running program...", "green")

# Create the Ntuple object
ntuple = NTuple(inputFolder=inpath)

# Create a mapping of event numbers to indices for faster lookups
event_number_to_index = {event.number: event.index for event in ntuple.events}


def remake_file(file):
    data = pd.read_csv(file, sep=" ", header=None, names=["sl", "bx", "tdc", "l", "w", "event"])
    data["event_index"] = data["event"].map(event_number_to_index)
    data["idd"] = data.index

    # Calculate bxsend efficiently
    bxsend = []
    last_bxsend = 0
    for _, group in data.groupby("event_index"):
        group_bxsend = group["bx"] - group["bx"].iloc[0] + last_bxsend
        bxsend.extend(group_bxsend)
        last_bxsend = group_bxsend.iloc[-1] + 50
    data["bxsend"] = bxsend

    # overwrite the file with the new format # bxsend sl bx tdc l w idd event_index
    data = data[["bxsend", "sl", "bx", "tdc", "l", "w", "idd", "event_index"]]
    _, file_name = os.path.split(file)

    data.to_csv(f"./digis_dumped_ntuple4agreement_remade/{file_name}", sep=" ", header=False, index=False)

def main():
    for file in os.listdir(dumped_digis_folder):
        print(f"Processing file: {file}")
        remake_file(os.path.join(dumped_digis_folder, file))

if __name__ == "__main__":
    main()