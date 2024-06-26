import pandas as pd
import os
import json
import subprocess
import sys

hostname = subprocess.check_output(["hostname"]).decode("utf-8").strip()

#find hyperparameters from collated  metrics 
# Read in tune name from system argument
tune_name=str(sys.argv[1])
grid_file=str(sys.argv[2])
#create file paths 
hps_dir=f"{grid_file}/output_py/COLLATE/{tune_name}_col.csv"
print(hps_dir)
#join to directory 

col_met=pd.read_csv(hps_dir)

col_met=col_met.sort_values(by=['r2'],ascending=False)
print(col_met)
batchsize = col_met['batch'][0] if 'batch' in col_met else None
units1 = col_met['units1'][0] if 'units1' in col_met else None
units2 = col_met['units2'][0] if 'units2' in col_met else None
units3 = col_met['units3'][0] if 'units3' in col_met else None
lrate = col_met['lrate'][0] if 'lrate' in col_met else None
layers = col_met['layers'][0] if 'layers' in col_met else None
epoch=1000
print(units2)
combinations = [
    int(epoch) if epoch is not None else -1,
    int(batchsize) if batchsize is not None else -1,
    int(units1) if units1 is not None else -1,
    int(units2) if units2 is not None else -1,
    int(units3) if units3 is not None else -1,
    float(lrate) if lrate is not None else -1.0,
    int(layers) if layers is not None else -1
]
print(combinations)
image_name=sys.argv[3]
# Create a base output directory
base_output_directory =  f"{grid_file}/output_py/{tune_name}/EARLY_STOP/"
print(base_output_directory)
os.makedirs(base_output_directory, exist_ok=True)

# Create individual output directories for each chunk
output_directories = [f'{base_output_directory}']
print(output_directories)

os.makedirs(output_directories[0], exist_ok=True)

# Dynamic starting port
dynamic_starting_port = 110

# create docker file
with open('/home/ubuntu/LSTM_PY/docker-compose.yml', 'w') as compose_file:
    compose_file.write('version: \'3\'\n\nservices:\n')

    service_name = f'{tune_name}'  # Use the custom container name provided by the user
    output_directory = output_directories[0]
    compose_file.write(f'  {service_name}:\n')
    compose_file.write(f'    image: {image_name}\n')
    compose_file.write(f'    ports:\n')
    compose_file.write(f'      - "{dynamic_starting_port}:8787"\n')  # Map container port 8787 to host ports dynamically

    # Convert the 2D array to a string and convert nan to null
    serialized_combinations = json.dumps([x if pd.notna(x) else None for x in combinations])
    # Set the environment variable
    os.environ["COMBINATIONS_ENV"] = serialized_combinations

    # Add environment variables for each combination
    compose_file.write(f'    environment:\n')
    compose_file.write(f'      combos: "{serialized_combinations}"\n')

    # Add volumes to mount output directory
    compose_file.write(f'    volumes:\n')
    compose_file.write(f'      - {output_directory}:/app/output\n')

    # Add command to run the script inside the container
    compose_file.write(f'    command: python3 /LSTM_model_fit_ES.py\n\n')

print("Docker Compose file generated successfully.")

