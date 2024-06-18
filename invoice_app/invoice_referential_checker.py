import os
import re
import csv
import json
import glob
import openai
import chardet
from tqdm import tqdm
from pydantic import BaseModel
from dotenv import load_dotenv
import logging
import pandas as pd
import streamlit as st

load_dotenv()

def get_ref(directory_path, output_dir_path):
    """Get files from local folder and process one at a time"""
    input_ref_dir = os.path.join(directory_path, 'referentials')

    # Handling the SCI Reference CSV
    sci_ref_path = os.path.join(input_ref_dir, "sci_ref.csv")
    try:
        sci_ref = pd.read_csv(sci_ref_path, delimiter='\t', on_bad_lines='skip')
        #print("SCI Reference Data:")
        #print(sci_ref.head())
    except Exception as e:
        st.error(f"Failed to read SCI reference: {e}")

    # Handling the Projects Reference CSV
    projects_ref_path = os.path.join(input_ref_dir, "projects_ref.csv")
    try:
        projects_ref = pd.read_csv(projects_ref_path, delimiter='\t', on_bad_lines='skip')
        #print("Projects Reference Data:")
        #pd.set_option('display.max_columns', None)
        #print(projects_ref['Name'])
    except pd.errors.ParserError as pe:
        st.error(f"Failed to read PROJECT reference: {pe}")
    except Exception as e:
        st.error(f"An unexpected error occurred while reading the PROJECT file: {e}")
    
    # Handling the Projects engagement CSV
    engagements_ref_path = os.path.join(input_ref_dir, "projects_ref.csv")
    try:
        engagements_ref = pd.read_csv(engagements_ref_path, delimiter='\t', on_bad_lines='skip')
        #print("Projects Reference Data:")
        #pd.set_option('display.max_columns', None)
        #print(projects_ref['Name'])
    except pd.errors.ParserError as pe:
        st.error(f"Failed to read PROJECT reference: {pe}")
    except Exception as e:
        st.error(f"An unexpected error occurred while reading the ENGAGEMENT file: {e}")

    return sci_ref, projects_ref, engagements_ref

def check_invoice(json_data, directory_path, output_dir_path):
    sci_ref, projects_ref, engagements_ref = get_ref(directory_path, output_dir_path)
    st.header(f"checking info for a new invoice")
    st.write(json_data)
    """
    Check if specified SCI and Project names from plain text are found in reference DataFrames.
    
    Args:
    json_data (str): Plain text data containing information.
    sci_ref (DataFrame): DataFrame containing SCI reference data.
    projects_ref (DataFrame): DataFrame containing Project reference data.

    Returns:
    bool: True if both names are found exactly in the text data, False otherwise.
    """
    # Convert all searches to lower case for case-insensitive matching
    json_data = json_data.lower()
    sci_name_found = False
    project_name_found = False

    sci_name_found = any(name.lower() in json_data for name in sci_ref['Name'])
    
    if sci_name_found:
        # If SCI name is found, retrieve the corresponding 'id'
        id_found = None
        for name in sci_ref['Name']:
            if name.lower() in json_data:
                id_found = sci_ref[sci_ref['Name'].str.lower() == name.lower()]['Id'].iloc[0]
                sci_name_found = name.lower()
                break
        if id_found:
            st.info(f"SCI Name '{name.lower()}' found in text data with ID {id_found}.")
        else:
            st.warning("SCI found but not the id not found in text data.")
            return sci_name_found, project_name_found
    else:
        st.warning("SCI Name not found in text data.")
        return sci_name_found, project_name_found
    
    engagements_ref['Id'] = engagements_ref['Id'].astype(str)  # Make sure the 'Id' column is of string type
    engagements_ref_found = any(str(id_engagement) in json_data for id_engagement in engagements_ref['Id'])

    if engagements_ref_found:
        # If SCI name is found, retrieve the corresponding 'id'
        id_found = None
        for id_engagement in engagements_ref['Id']:
            if str(id_engagement) in json_data:
                filtered_df = engagements_ref[engagements_ref['Id'] == str(id_engagement)]
                if not filtered_df.empty:
                    id_found = filtered_df['Id'].iloc[0]
                    id_engagement_found = id_engagement
                break
        if id_found:
            st.info(f"id_engagement '{id_engagement}' found in text data with ID {id_found}.")
            return sci_name_found, id_engagement_found
        else:
            st.warning("id_engagement found but not the id not found in text data.")
            return sci_name_found, id_engagement_found
    else:
        st.warning("id_engagement not found in text data.")
        return sci_name_found, 0

    '''no need to search for project now
    # Find projects with matching ProjectCompanyId
    matching_projects = projects_ref[projects_ref['ProjectCompanyId'] == id_found]    
    st.info(f"{len(matching_projects)} projects related to this SCI")
    # Check for constructed Id+Name in json_data
    project_name_found = False
    for _, project in matching_projects.iterrows():
        project_id_name = f"{project['Name']}".lower()
        st.info(f"Searching for : {project_id_name}")
        if project_id_name in json_data.lower():
            project_name_found = True
            st.info(f"Project found in text data: {project_id_name}")
            break
    if not project_name_found:
        st.warning(f"No Project found in text data. ")
        return sci_name_found, project_name_found
    '''
    
    return sci_name_found, project_name_found