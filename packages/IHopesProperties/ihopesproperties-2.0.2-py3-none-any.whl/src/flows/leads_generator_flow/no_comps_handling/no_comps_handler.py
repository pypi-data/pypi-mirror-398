import json
from typing import List

# File to store properties with no comps
NO_COMPS_FILE = 'src/leads_generator_flow/no_comps_handling/no_comps_properties.json'

# Load the list of properties with no comps from the file
def load_no_comps_properties():
    try:
        with open(NO_COMPS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []  # Return an empty list if the file doesn't exist

# Save the list of properties with no comps to the file
def save_no_comps_properties(no_comps_list):
    with open(NO_COMPS_FILE, "w") as f:
        json.dump(no_comps_list, f)

# Check if a property is in the no-comps list
def is_in_no_comps_list(property_address):
    no_comps_list = load_no_comps_properties()
    return property_address in no_comps_list

# Add a property to the no-comps list
def add_to_no_comps_list(property_address):
    no_comps_list = load_no_comps_properties()
    if property_address not in no_comps_list:
        no_comps_list.append(property_address)
        save_no_comps_properties(no_comps_list)