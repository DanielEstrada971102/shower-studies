from collections import defaultdict
import re
import os
from os import listdir
# File paths
#input_file = "/nfs/fanae/user/jprado/Prado/entradaFPBRUTO"
FPGA_Input_Hits_Folder="./data/Input_CMSSW/digis_IN_FPGA"
FPGA_Shower_Folder="./data/FPGA_Outputs/ShowerOutput"
FPGA_Verification_Hits_Folder="./data/FPGA_Outputs/HitLog"
#EMULATOR Results
CMSSW_Shower_Folder="./data/Input_CMSSW/Shower_results_Emulator"

def read_input_data(file_path):
    """Read input data and store it as a dictionary with ID as the key."""
    input_data = {}
    with open(file_path, 'r') as f:        
        for line_num, line in enumerate(f, 0):  # Start at line 2
            parts = line.strip().split()
            if len(parts) != 8:
                print(f"Error in input line {line_num}: Expected 7 columns, got {len(parts)}. Skipping.")
                continue
            try:
                bxsend, sl, bx, tdc, layer, wire, wire_id, eventNumber = map(int, parts)                
                input_data[wire_id] = (bxsend, sl, bx, tdc, layer, wire, eventNumber)
                
            except ValueError:
                print(f"Error in input line {line_num}: Non-integer data. Skipping.")
    return input_data

def Hit_Test_data(file_path):
    """Read output data and store it as a dictionary with ID as the key. Detect duplicates."""
    output_data = {}
    duplicates = set()
    seen_ids = set()
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            parts = line.strip().split("|")
            if len(parts) != 5:
                print(f"Error in output line {line_num}: Expected 5 parts, got {len(parts)}. Skipping.")
                continue
            try:
                wire_id = int(parts[0].split(":")[1].strip())
                bx = int(parts[1].split(":")[1].strip())
                tdc = int(parts[2].split(":")[1].strip())
                layer = int(parts[3].split(":")[1].strip())
                wire = int(parts[4].split(":")[1].strip())
                
                if wire_id in seen_ids:
                    duplicates.add(wire_id)

                else:
                    seen_ids.add(wire_id)
                    output_data[wire_id] = (bx, tdc, layer, wire)
                
            except (IndexError, ValueError):
                print(f"Error in output line {line_num}: Invalid format. Skipping.")
    
    if duplicates:
        print(f"Duplicate IDs in output: {sorted(duplicates)}")
    else:
        print("No duplicate IDs in output.")

    return output_data

def parse_input_events(input_data):
    events = {}

    for wire_id, hit_info in input_data.items():
        event_number = hit_info[6]  # Event number is at index 6
        
        if event_number not in events:
            events[event_number] = []
        
        # Create a single tuple with wire_id and all hit info
        hit_tuple = (wire_id,) + hit_info
        events[event_number].append(hit_tuple)
    
    # Sort events dictionary by event number
    events = dict(sorted(events.items()))

    return events

def parse_output_events(output_data,input_data):
#need to retrieve the event_number from ID.
    events = {}
    for wire_id, hit_info in output_data.items():
        event_number = input_data[wire_id][6]  # Event number is at index 6
        
        if event_number not in events:
            events[event_number] = []
        
        # Create a single tuple with wire_id and all hit info
        hit_tuple = (wire_id,) + hit_info
        events[event_number].append(hit_tuple)
    
    # Sort events dictionary by event number
    events = dict(sorted(events.items()))
    
    return events
#Read the data from the FPGA file
def parse_showers_FPGA(shower_hits_file):
    """
    Parse shower hits data from file.
    
    Args:
        shower_hits_file (str): Path to the shower hits file
        
    Returns:
        dict: Dictionary with parsed shower data per index
    """
    shower_data = []
    
    with open(shower_hits_file, 'r') as file:
        data = file.read()
        
        # Regular expression patterns to extract fields
        index_pattern = r"Index:\s+(\d+)"
        shower_bx_pattern = r"ShowerBX_SL\d+:\s+(\d+)"
        max_wire_pattern = r"Max Wire SL\d+:\s+(\d+)"
        min_wire_pattern = r"Min Wire SL\d+:\s+(\d+)"
        wire_counter_pattern = r"WireCounter_SL\d+:\s+([0-9\s]+)"
        ids_pattern = r"IDs:\s+([\d\s]+)"
        
        # Split the data into individual entries
        entries = data.split("Index:")
        
        for entry in entries[1:]:  # Skip first empty entry
            entry_data = {}
            try:
                # Extract fields
                entry_data["Index"] = int(entry.split()[0])
                entry_data["ShowerBX"] = int(re.search(shower_bx_pattern, entry).group(1))
                entry_data["MaxWire"] = int(re.search(max_wire_pattern, entry).group(1))
                entry_data["MinWire"] = int(re.search(min_wire_pattern, entry).group(1))
                entry_data["WireCounter"] = [int(x) for x in re.search(wire_counter_pattern, entry).group(1).split()]
                entry_data["IDs"] = [int(x) for x in re.search(ids_pattern, entry).group(1).split()]
                
                shower_data.append(entry_data)
            except (ValueError, AttributeError) as e:
                print(f"Error parsing entry: {e}")
                continue
    
    return shower_data
#Read the data from the Emulator file
#def parse_Shower_emulator(ShowersEmulator_File, SuperLayer):
def compare_input_output(input_data, output_data_SL0, output_data_SL1):
    Output_ALL={}
    Output_ALL=output_data_SL0
    Output_ALL.update(output_data_SL1)
    Output_ALL = dict(sorted(Output_ALL.items()))
    comparison_results = {}  # Dictionary to store comparison results
    missing_in_output = []  # List to store ids that are missing in the output
    missmatched=[]
    for id in input_data.keys():
        if id in Output_ALL:
            # Compare input_data[id] with Output_ALL[id] and store the result
            if input_data[id][2:6] == Output_ALL[id]:
                comparison_results[id] = "Match"
            else:
                comparison_results[id] = "Mismatch"
                missmatched.append(id)
        else:
            # If the id is not found in Output_ALL, mark it as missing
            if input_data[id][1]!= 2:
                comparison_results[id] = "Not Found in Output"
                missing_in_output.append(id)
    
    # Returning both the comparison results and the missing ids
    if len(missing_in_output)>0:        
        print("Missing hits")
        for i in missing_in_output:
            print(input_data[i])
    else:
        print("No Missing hits")
   
    return comparison_results, missing_in_output, missmatched

#Use the input data to recover the missing information in the shower data
def add_hits_to_showers(showers, input_data):
    for shower in showers:
            shower['Hits'] = []
            for hit_id in shower['IDs']:
                if hit_id in input_data:
                    hit_info = {
                        'ID': hit_id,
                        'BXsend': input_data[hit_id][0],
                        'SL': input_data[hit_id][1],
                        'BX': input_data[hit_id][2],
                        'TDC': input_data[hit_id][3],
                        'Layer': input_data[hit_id][4],
                        'Wire': input_data[hit_id][5],
                        'Event': input_data[hit_id][6]
                    }
                    shower['Hits'].append(hit_info)
                else:
                    print(f"Warning: Hit ID {hit_id} not found in input data")
        
    return showers

#Convert from showerobject to events
def Events_Showers_FPGA(Showers):
    Truths = {}
    for shower in Showers:
        # Get unique events from all hits in this shower
        shower_events = set(hit['Event'] for hit in shower['Hits'])
        if shower_events.__len__()>1:
            "Print multiple ids in a shower!"

        # For each event this shower belongs to
        for event in shower_events:
            if event not in Truths:
                Truths[event] = []
            
            # Add shower information as a dictionary
            shower_info = {
                'ShowerBX': shower['ShowerBX'],
                'MinWire': shower['MinWire'],
                'MaxWire': shower['MaxWire'],
                'WireCounter': shower['WireCounter'],
                'Hits': shower['Hits'],
                'IDs': shower['IDs']
            }
            Truths[event].append(shower_info)
    return Truths
        
def parse_Shower_Emu(filename):
    """Parse shower data from the given file while handling missing files gracefully."""
    showers_sl1 = {}  # Dictionary for sl == 1
    showers_sl3 = {}  # Dictionary for sl == 3
    current_event = {}

    if not os.path.exists(filename):
        print(f"Warning: File {filename} not found. Returning empty dictionaries.")
        return showers_sl1, showers_sl3  # Return empty dictionaries if file doesn't exist

    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()

            # Match event headers
            event_match = re.match(r"# Event (\d+)", line)
            if event_match:
                if current_event:  # Save previous event if not empty
                    if current_event.get("sl") == 1:
                        showers_sl1[current_event["event_id"]] = current_event
                    elif current_event.get("sl") == 3:
                        showers_sl3[current_event["event_id"]] = current_event
                current_event = {"event_id": int(event_match.group(1))}
                continue  # Move to the next line

            # Match key-value pairs
            key_value_match = re.match(r"(\w+):\s*(.*)", line)
            if key_value_match:
                key, value = key_value_match.groups()
                try:
                    if key == "wires_profile":  # Convert wire profile into a list
                        current_event[key] = list(map(int, value.strip("[]").split(", ")))
                    elif key in ["sl", "nDigis", "BX", "minW", "maxW"]:  # Convert to integer
                        current_event[key] = int(value)
                    elif key in ["avgPos", "avgTime"]:  # Convert to float
                        current_event[key] = float(value)
                except ValueError:
                    print(f"Warning: Invalid value in file {filename}, line: {line}. Skipping entry.")
                continue

        # Save the last event in the appropriate dictionary
        if current_event:
            if current_event.get("sl") == 1:
                showers_sl1[current_event["event_id"]] = current_event
            elif current_event.get("sl") == 3:
                showers_sl3[current_event["event_id"]] = current_event

    return showers_sl1, showers_sl3

def compare_Showers(Emulator, FPGA):
    match_count = 0    
    missing_in_fpga = 0
    missing_in_emulator = 0

    match_events = []    
    missing_fpga_events = []
    missing_emulator_events = []

    all_events = set(Emulator.keys()).union(FPGA.keys())  # All unique events

    for event in all_events:
        if event in Emulator and event in FPGA:            
            match_count += 1
            match_events.append(event)
        elif event in Emulator:
            missing_in_fpga += 1
            missing_fpga_events.append(event)            
        elif event in FPGA:
            missing_in_emulator += 1
            missing_emulator_events.append(event)
            if missing_in_emulator>5:
                print("AAAAAAAAAAAAAAAAAAH")   

    print('Events in FPGA')
    print(list(FPGA.keys()))

    print('Events in Emulator')
    print(list(Emulator.keys()))

    return[match_count,match_events],[missing_in_fpga,missing_fpga_events],[missing_in_emulator,missing_emulator_events]
        
def organize_hits_by_structure(input_data, station, organized_data=None):
    if organized_data is None:
        organized_data = {}  # Initialize if not provided

    if station not in organized_data:
        organized_data[station] = {}  # Create a new station entry if it doesn't exist

    for wire_id, hit_info in input_data.items():
        bxsend, sl, bx, tdc, layer, wire, event_number = hit_info

        # Ensure SL exists within the station
        if sl not in organized_data[station]:
            organized_data[station][sl] = {}

        # Ensure event exists within the SL
        if event_number not in organized_data[station][sl]:
            organized_data[station][sl][event_number] = []

        # Append hit to the corresponding event
        organized_data[station][sl][event_number].append({
            "wire_id": wire_id,
            "bxsend": bxsend,
            "bx": bx,
            "tdc": tdc,
            "layer": layer,
            "wire": wire
        })

        # Debug statements
        print(f"Station: {station}")
        print(f"SL: {sl}")
        print(f"Event: {event_number}")
        print(f"Hit added: {organized_data[station][sl][event_number][-1]}")
    
    return organized_data

def main():
    # Parse data and check for duplicates
    Results={}
    Showers_Emu={}
    Showers_FPGA={}
    Total_Match=0
    Total_MissFPGA=0
    Total_MisEMUL=0
    Files=os.listdir("./data/Input_CMSSW/digis_IN_FPGA/")
    organized_data = {}
    for File in Files:
        Station=File.removesuffix('.txt')
        Station=Station.removeprefix('digis_')
        print("Processing:")
        print(Station)

        if Station=="wh2_sc12_st1":
            print("AAAAAAAAAH")

        #Input data from CMSSW
        #Return hits sorted by ID
        input_data = read_input_data(FPGA_Input_Hits_Folder+f'/{File}')        
        organized_data = organize_hits_by_structure(input_data, Station, organized_data)
        output_data_SL0 = Hit_Test_data(FPGA_Verification_Hits_Folder+f'/Hitlog_{Station}_SL0.txt')
        output_data_SL1= Hit_Test_data(FPGA_Verification_Hits_Folder+f'/Hitlog_{Station}_SL1.txt')
        
        #Check that the FPGA is feeding the input data correctly.####
        Events_in=parse_input_events(input_data)
        #use the hit ID to recover the event.
        Events_in_SL0=parse_output_events(output_data_SL0,input_data)
        Events_in_SL1=parse_output_events(output_data_SL1,input_data)
        #############################################################

        #Retrieve data from the FPGA output
        Showers_SL0=parse_showers_FPGA(FPGA_Shower_Folder+f'/output_{Station}_SL0.txt')
        Showers_SL1=parse_showers_FPGA(FPGA_Shower_Folder+f'/output_{Station}_SL1.txt')
        #Retrieve data from the Emulator output
        
        #Check the event information
        Showers_SL0_FPGA = add_hits_to_showers(Showers_SL0, input_data)
        Showers_SL1_FPGA = add_hits_to_showers(Showers_SL1, input_data)
        Events_Shower_SL0=Events_Showers_FPGA(Showers_SL0_FPGA)
        Events_Shower_SL1=Events_Showers_FPGA(Showers_SL1_FPGA)

        Showers_SL0_EMU,Showers_SL1_EMU=parse_Shower_Emu(CMSSW_Shower_Folder+f'/showers_{Station}.txt')        
        #Check
        compare_input_output(input_data, output_data_SL0, output_data_SL1)
        
        Match_SL0, Miss_FPGA_Sl0,Miss_Emulator_SL0=compare_Showers(Showers_SL0_EMU,Events_Shower_SL0)
        Match_SL1, Miss_FPGA_Sl1,Miss_Emulator_SL1=compare_Showers(Showers_SL1_EMU,Events_Shower_SL1)
        Results[Station] = {"SL0": [ Match_SL0, Miss_FPGA_Sl0, Miss_Emulator_SL0], "SL1": [Match_SL1, Miss_FPGA_Sl1,Miss_Emulator_SL1]}
        Total_Match+=Match_SL0[0]+Match_SL1[0]
        Total_MissFPGA+=Miss_FPGA_Sl0[0]+Miss_FPGA_Sl1[0]
        Total_MisEMUL+=Miss_Emulator_SL0[0]+Miss_Emulator_SL1[0]        


    print("Total Match")
    print(Total_Match)
    print("Total Miss FPGA")
    print(Total_MissFPGA)
    print("Total Miss EMUL")
    print(Total_MisEMUL)

def main_2():
    Files=os.listdir("./Input_CMSSW/digis_IN_FPGA/")
    organized_data = {}
    for File in Files:
        Station=File.removesuffix('.txt')
        Station=Station.removeprefix('digis_')
        print("Processing:")
        print(Station)

        input_data = read_input_data(FPGA_Input_Hits_Folder+f'/{File}') 
        organized_data = organize_hits_by_structure(input_data, Station, organized_data)

        print(organized_data)
        break

if __name__ == "__main__":
    main()