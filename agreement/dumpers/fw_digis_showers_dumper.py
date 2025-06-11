# Code of Javier Prado (generateAndRunTCL.py)

import os
import subprocess
import shutil
import re
# input_dir = os.path.abspath("C:/Users/estradadaniel/FIRMWARE_EMULATOR/Input_CMSSW/digis_IN_FPGA/")
# VivadoDir = os.path.abspath("C:/Users/estradadaniel/FIRMWARE_EMULATOR/AlgoritmoFPGA_Nuevo/project_1_V2/project_1_V2.sim/sim_1/behav/xsim/")
input_dir = os.path.abspath("C:/Users/estradadaniel/cernbox/shower-studies/agreement/digis_dumped_ntuple4agreement_remade/")
VivadoDir = os.path.abspath("C:/Users/estradadaniel/FIRMWARE_EMULATOR/AlgoritmoFPGA_Nuevo/project_1_V2/project_1_V2.sim/sim_1/behav/xsim/")
# Define output directories
output_dir_hitlog = os.path.abspath("C:/Users/estradadaniel/FIRMWARE_EMULATOR/FPGA_Outputs_2/HitLog")
output_dir_shower = os.path.abspath("C:/Users/estradadaniel/FIRMWARE_EMULATOR/FPGA_Outputs_2/ShowerOutput")


#File with the TB
vhdl_path = os.path.abspath("C:/Users/estradadaniel/FIRMWARE_EMULATOR/AlgoritmoFPGA_Nuevo/project_1_V2/project_1_V2.srcs/sources_1/new/Top_tb.vhd")
vivado_path = os.path.abspath("C:/Xilinx/Vivado/2024.1")

def edit_vhdl_testbench(vhdl_testbench_path, input_file):
    """
    Modifies the input file path in the VHDL testbench file.

    Args:
        vhdl_testbench_path (str): Path to the VHDL testbench file
        input_file (str): Name of the input file to be used

    Raises:
        FileNotFoundError: If the VHDL file does not exist
        IOError: If file cannot be opened or written
    """
    if not os.path.exists(vhdl_testbench_path):
        raise FileNotFoundError(f"VHDL file not found: {vhdl_testbench_path}")

    print(f"Modifying VHDL testbench file: {vhdl_testbench_path}")

    try:
        # Read the file content
        with open(vhdl_testbench_path, 'r') as f:
            lines = f.readlines()

        # Modify the file content using regex for flexibility
        pattern = re.compile(r'file input_file : text open read_mode is ".*";')
        updated = False

        for i, line in enumerate(lines):
            if pattern.search(line):
                lines[i] = f'    file input_file : text open read_mode is "{input_file}";\n'
                updated = True
                break

        if not updated:
            raise ValueError("Pattern not found in VHDL file.")

        # Write back to file
        with open(vhdl_testbench_path, 'w') as f:
            f.writelines(lines)

        print(f"Successfully updated input file to: {input_file}")

    except IOError as e:
        print(f"Error modifying VHDL file: {e}")
        raise

def create_tcl_script(input_file, vivado_project_path, simulation_time="200us"):
    """
    Creates a TCL script to run the simulation.
    
    Args:
        input_file (str): Name of the input file being tested.
        vivado_project_path (str): Path to the Vivado project.
        simulation_time (str): Duration of the simulation.

    Returns:
        str: Path to the generated TCL script.
    """
    print(f"Creating TCL script for input file: {input_file.split('/')[-1]}")
    tcl_content = f"""
    open_project "{vivado_project_path.replace('\\', '\\\\')}"
    update_compile_order -fileset sources_1
    set_property top Top_tb [get_filesets sim_1]
    launch_simulation
    run {simulation_time}
    quit
    """
    os.makedirs("__temp__", exist_ok=True)
    # Define the TCL file path (e.g., "run_sim_<input_file>.tcl")
    tcl_path = os.path.abspath(f"__temp__/run_sim_{input_file.split('digis_')[-1].strip('.txt')}.tcl")
    with open(tcl_path, 'w') as f:
        f.write(tcl_content)
    print(f"TCL script created: {tcl_path}")

    return tcl_path


# Run the simulation
def run_simulation(tcl_path, vivado_path):
    vivado_executable = os.path.join(vivado_path, "bin", "vivado")

    # Check if the executable exists
    if not os.path.isfile(vivado_executable):
        raise FileNotFoundError(f"Vivado executable not found: {vivado_executable}")

    cmd = [
        vivado_executable,
        "-mode", "batch",
        "-source", f"{tcl_path}"
    ]

    try:
        print(f"Running Vivado simulation with command: {' '.join(cmd)}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"Simulation failed with return code {process.returncode}")
    except OSError as e:
        print(f"Error executing Vivado: {e}")
        raise

def main():
    vivado_path = os.path.abspath("C:/Xilinx/Vivado/2024.1") # Adjust as needed
    vivado_project_path = os.path.abspath("../../fpga_showers/project_1_V2.xpr/project_1_V2/project_1_V2.xpr")
    vhdl_testbench_path = os.path.abspath("../../fpga_showers/project_1_V2.xpr/project_1_V2/project_1_V2.srcs/sources_1/new/Top_tb.vhd")
    vivado_sim_results_path = os.path.abspath("../../fpga_showers/project_1_V2.xpr/project_1_V2/project_1_V2.sim/sim_1/behav/xsim/")
    input_cmssw_digis_dir = os.path.abspath("../data/Input_CMSSW/digis_IN_FPGA/")
    os.makedirs("../data/FPGA_Outputs/HitLog", exist_ok=True)
    os.makedirs("../data/FPGA_Outputs/ShowerOutput", exist_ok=True)
    output_dir_hitlog = os.path.abspath("../data/FPGA_Outputs/HitLog")
    output_dir_shower = os.path.abspath("../data/FPGA_Outputs/ShowerOutput")

    for file in os.scandir(input_cmssw_digis_dir):
        edit_vhdl_testbench(vhdl_testbench_path, file.path)
        tcl_script = create_tcl_script(file.path, vivado_project_path)
        run_simulation(tcl_script, vivado_path)

        wh, sc, st = map(int, re.search(r"wh(-?\d+)_sc(\d+)_st(\d+)", file.path).groups())
        results_to_recover = {
            "LOG_FILE_SL0.txt": os.path.join(output_dir_hitlog, f"Hitlog_wh{wh}_sc{sc}_st{st}_SL0.txt"),
            "LOG_FILE_SL1.txt": os.path.join(output_dir_hitlog, f"Hitlog_wh{wh}_sc{sc}_st{st}_SL1.txt"),
            "log_outputSL0.txt": os.path.join(output_dir_shower, f"output_wh{wh}_sc{sc}_st{st}_SL0.txt"),
            "log_outputSL1.txt": os.path.join(output_dir_shower, f"output_wh{wh}_sc{sc}_st{st}_SL1.txt")
        }
        # Copy files with error handling
        for src_file, dest_file in results_to_recover.items():
            src_path = os.path.join(vivado_sim_results_path, src_file)
            try:
                shutil.copy2(src_path, dest_file)  # copy2 preserves metadata
                print(f"✔ Copied: {src_path} -> {dest_file}")
            except FileNotFoundError:
                print(f"⚠ Warning: File {src_path} not found, skipping.")
    
    # delete the temporary TCL script directory
    if os.path.exists("__temp__"):
        shutil.rmtree("__temp__")
        print("Temporary directory '__temp__' deleted.")

if __name__ == "__main__":
    main()

