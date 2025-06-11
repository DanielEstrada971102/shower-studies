import os
import subprocess
import shutil
from dtpr.base import NTuple
from dtpr.utils.config import RUN_CONFIG
from dtpr.utils.functions import color_msg
import pandas as pd

RUN_CONFIG.change_config_file(config_path="./run_config.yaml")
# Create the Ntuple object
ntuple = NTuple(inputFolder="./ntuple4aggreement.root")

# Create a mapping of event numbers to indices for faster lookups
event_number_to_index = {event.number: event.index for event in ntuple.events}


def remake_file(file, output_folder="../data/Input_CMSSW/digis_IN_FPGA"):
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

    os.makedirs(output_folder, exist_ok=True)
    data.to_csv(f"{output_folder}/{file_name}", sep=" ", header=False, index=False)

def main():
    # create a __tmp_ folder to extract the tar.gz file
    os.makedirs("__tmp__", exist_ok=True)
    # Extract the tar.gz file
    subprocess.run(["tar", "-xzf", "dumped_digis_ntuple4agreement.tar.gz", "-C", "__tmp__"], check=True)
    dumped_digis_folder = "__tmp__/results/"

    for file in os.scandir(dumped_digis_folder):
        print(f"Processing file: {file.name}")
        remake_file(os.path.join(dumped_digis_folder, file.name))

    # delete the __tmp__ folder
    shutil.rmtree("__tmp__")

if __name__ == "__main__":
    main()