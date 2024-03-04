import pandas as pd
import os
import json
import subprocess

hostname = subprocess.check_output(["hostname"]).decode("utf-8").strip()

# Specify the file path for the CSV file with selected combinations
selected_combos_path = "/srv/samba/hp_tune_grid/hps_selected_" + hostname + ".csv"

# Read the CSV file into a DataFrame
selected_combos_df = pd.read_csv(selected_combos_path)

# Extract variables from the DataFrame
combinations = selected_combos_df[['epochs', 'batch_size', 'units1', 'units2','lrate']].values.tolist()

print("length of combinations:", len(combinations))

image_name = input("Enter image name:")
run_name = input("Enter a custom container name:")
max_con = int(input("Enter max containers to start:"))

# split into chunks
def split(a, n):
    k, m = divmod(len(a), n)
    return [slice(i * k + min(i, m), (i + 1) * k + min(i + 1, m)) for i in range(n)]

def split_by_indices(a, n):
    indices = split(list(range(len(a))), n)
    chunks = [a[idx] for idx in indices]
    return chunks

split_combos = split_by_indices(combinations, max_con)

# Create a base output directory
base_output_directory = "/srv/samba/hp_tune_grid/output/"+hostname+"/"+run_name
print(base_output_directory)
os.makedirs(base_output_directory, exist_ok=True)

# Create individual output directories for each chunk
output_directories = [f'{base_output_directory}/hprun_split_container_{i+1}_{len(split_combos)}' for i in range(len(split_combos))]
print(output_directories)

for directory in output_directories:
    os.makedirs(directory, exist_ok=True)

# Dynamic starting port
dynamic_starting_port = 80

# create docker file
with open('/home/ubuntu/LSTM_cleaned_02_26/docker-compose.yml', 'w') as compose_file:
    compose_file.write('version: \'3\'\n\nservices:\n')

    for i, combo in enumerate(split_combos, start=1):
        service_name = f'{run_name}_container{i}'  # Use the custom container name provided by the user
        output_directory = output_directories[i - 1]
        compose_file.write(f'  {service_name}:\n')
        compose_file.write(f'    image: {image_name}\n')
        compose_file.write(f'    ports:\n')
        compose_file.write(f'      - "{dynamic_starting_port + i}:8787"\n')  # Map container port 8787 to host ports dynamically

        # Convert the 2D array to a string
        serialized_combinations = json.dumps(combo)
        # Set the environment variable
        os.environ["COMBINATIONS_ENV"] = serialized_combinations

        # Add environment variables for each combination
        compose_file.write(f'    environment:\n')
        compose_file.write(f'      combos: "{serialized_combinations}"\n')

        # Add volumes to mount output directory
        compose_file.write(f'    volumes:\n')
        compose_file.write(f'      - {output_directory}:/app/output\n')

        # Add command to run the script inside the container
        compose_file.write(f'    command: Rscript /LSTM_cv_tuning.R\n\n')

print("Docker Compose file generated successfully.")
