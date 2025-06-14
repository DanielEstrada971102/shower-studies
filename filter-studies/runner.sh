#!/bin/bash

# Check if the required arguments are provided
if [[ -z "$1" || -z "$2" ]]; then
    echo "Usage: $0 <minbias|zprime> <seg_version>"
    exit 1
fi

# Get the arguments
mode=$1
seg_version=$2

# Validate the mode argument
if [[ "$mode" != "minbias" && "$mode" != "zprime" ]]; then
    echo "Invalid mode. Use 'minbias' or 'zprime'."
    exit 1
fi

# Validate the seg_version argument
if [[ "$seg_version" != "1" && "$seg_version" != "2" ]]; then
    echo "Invalid seg_version. Use '1' or '2'."
    exit 1
fi

# Set input_dir and run_config_file based on mode
if [[ "$mode" == "minbias" ]]; then
    input_dir="MINBIAS DIR"
    run_config_file="run_config_4rates.yaml"
else 
    input_dir="ZPRIME DIR"
    run_config_file="run_config.yaml"
fi

# Update the segmentation version in the run config file
sed -i "s/shower_seg_version: [0-9]\+/shower_seg_version: $seg_version/" "$run_config_file"

# Execute the dtpr fill-histos command
dtpr fill-histos -i "$input_dir/" -o "." -cf "$run_config_file" --tag="_${mode}_segv${seg_version}"
