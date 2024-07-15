import fnmatch
import os
import pandas as pd
import sys

def find_csv_files(root_directory, pattern='metrics_*.csv'):
    csv_files = []
    for dirpath, _, filenames in os.walk(root_directory):
        for filename in filenames:
            if fnmatch.fnmatch(filename, pattern):
                csv_files.append(os.path.join(dirpath, filename))
    return csv_files

# Set the directory of the instances
instances = ["theottest-1", "theottest-2", "lstm-pm25"]
all_data = pd.DataFrame()

# Read in tune name from system argument
tune_name=str(sys.argv[1])
grid_file=str(sys.argv[2])
inst=str(sys.argv[3])
# Write the combined data frame to a new CSV file
base_output_file = f'{grid_file}/output_py/COLLATE'
os.makedirs(base_output_file, exist_ok=True)
output_file=f"{base_output_file}/{tune_name}_col.csv"

root_directory = f'{grid_file}/output_py/TUNING/{inst}'
print(root_directory)

# Get a list of all CSV files starting with "metrics" in the specified directory and its subdirectories
csv_files = find_csv_files(root_directory)

# Check if there are any CSV files
if csv_files:
    # Read all CSV files into a list of data frames
    data_frames = [pd.read_csv(file) for file in csv_files]

    # Combine the data frames into one data frame
    single_csv = pd.concat(data_frames)

    # Check if the output file already exists and append the data if it does
    if os.path.exists(output_file):
        print("found output")
        extant = pd.read_csv(output_file)
        combined_data = pd.concat([extant, single_csv])
    else:
        combined_data = single_csv

    # Remove duplicates based on all columns
    combined_data = combined_data.drop_duplicates()

    # Write to file
    combined_data.to_csv(output_file, index=False)
    print("Collated metrics saved to:", output_file)
else:
    print(f"No CSV files starting with 'metrics' found in {root_directory}.")
