import pandas as pd
import os
import json
import sys
import subprocess

hostname = subprocess.check_output(["hostname"]).decode("utf-8").strip()

#read current working directory 
grid_file=sys.argv[4]
# Specify the file path for the CSV file with selected combinations
selected_combos_path = f'{grid_file}/hps_selected_{hostname}.csv'
print(selected_combos_path)
# Read the CSV file into a DataFrame
selected_combos_df = pd.read_csv(selected_combos_path)

# Extract variables from the DataFrame
combinations = selected_combos_df[['epoch','batch_size', 'units1', 'units2','units3','lrate','layers']].values.tolist()

print("length of combinations:", len(combinations))

#pull image name from shell script 
image_name=sys.argv[3]
#pull output name 
run_name=sys.argv[2]
#pull number of containers 
max_con=int(sys.argv[1])
# split into chunks
def split(a, n):
    k, m = divmod(len(a), n)
    return [slice(i * k + min(i, m), (i + 1) * k + min(i + 1, m)) for i in range(n)]

def split_by_indices(a, n):
    indices = split(list(range(len(a))), n)
    chunks = [a[idx] for idx in indices]
    return chunks

split_combos = split_by_indices(combinations, max_con)
base_output_directory = f'{grid_file}/output_py/TUNING/{hostname}'

#make base directory
print(base_output_directory)
os.makedirs(base_output_directory, exist_ok=False)

# Create individual output directories for each chunk
output_directories = [f'{base_output_directory}/hprun_split_container_{i+1}_{len(split_combos)}' for i in range(len(split_combos))]

for directory in output_directories:
    try:
        os.makedirs(directory, exist_ok=False)
        print(f"Directory {directory} created.")
    except FileExistsError:
        print(f"Directory {directory} already exists.")

# Dynamic starting port
dynamic_starting_port = 80

#create directory in which to create compose compose file 
compose_dir=f'{grid_file}/compose_files/{hostname}/'
try:
    os.makedirs({compose_dir}, exist_ok=False)
    print(f"Directory {compose_dir} created.")
except FileExistsError:
    print(f"Directory {compose_dir} already exists.")

# create docker file
with open('{compose_dir}docker-compose.yml', 'w') as compose_file:
    compose_file.write('version: \'3\'\n\nservices:\n')

    for i, combo in enumerate(split_combos, start=1):
        service_name = f'{hostname}_{run_name}_container{i}'  # Use the custom container name provided by the user
        output_directory = output_directories[i - 1]
        compose_file.write(f'  {service_name}:\n')
        compose_file.write(f'    image: {image_name}\n')
        compose_file.write(f'    ports:\n')
        compose_file.write(f'      - "{dynamic_starting_port + i}:8787"\n')  # Map container port 8787 to host ports dynamically

        # Convert the 2D array to a string and convert nan to null
        serialized_combinations = json.dumps([[x if pd.notna(x) else None for x in row] for row in combo])
        # Set the environment variable
        os.environ["COMBINATIONS_ENV"] = serialized_combinations

        # Add environment variables for each combination
        compose_file.write(f'    environment:\n')
        compose_file.write(f'      combos: "{serialized_combinations}"\n')

        # Add volumes to mount output directory
        compose_file.write(f'    volumes:\n')
        compose_file.write(f'      - {output_directory}:/app/output\n')

        # Add command to run the script inside the container
        compose_file.write(f'    command: python3 /LSTM_model_fit.py\n\n')

print("Docker Compose file generated successfully.")
