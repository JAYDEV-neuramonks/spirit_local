# demo space

import pandas as pd
import streamlit as st
import os
import sys
import datetime
import logging
import time
import zipfile
import json
import requests
import glob
from tqdm import tqdm

from invoice_app import invoice_functions
from config import settings
import utils


# Configure logging
log_output_dir = os.path.join(settings.working_dir , 'logs')
output_dir = os.path.join(settings.working_dir , 'output')
input_dir = os.path.join(settings.working_dir, 'input')

if not os.path.exists(log_output_dir):
    os.makedirs(log_output_dir)

# The filename where to store the logs
log_file = os.path.join(log_output_dir, 'processing.log')

# Check if logging is already set up by looking if the root logger has handlers
root_logger = logging.getLogger()
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # or whichever level you want
if not root_logger.hasHandlers():
    logging.basicConfig(
        filename=log_file, 
        level=logging.INFO, 
        format='%(asctime)s %(levelname)s %(message)s', 
        datefmt='%Y-%m-%d %H:%M:%S'
    )

console_handler = logging.StreamHandler(sys.stdout)  # You can also use sys.stderr
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
# Add the handler to the root logger
#logger.addHandler(console_handler)

password = "123"
hashed_password = utils.hash_password(password)  # you could print and then store this in your script

def main():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    utils.clean_expired_tokens()
    token = st.query_params.get('token') 
    
     # Check if the token is not None and if it's valid
    if token is not None and utils.token_exists(token[0]):  # token_exists checks if it's a valid token
        st.session_state.authenticated = True
    else:
        # If no valid token, the user is not authenticated
        st.session_state.authenticated = False

    #####
    # remove this line to activate authentification
    st.session_state.authenticated = True
    #####
    

    if st.session_state.authenticated:
        #st.info("Session valide")
        app()
    else:
        st.info("Session non valide")
        login()

def login():
    st.title("Controle d'acces")
    user_input_password = st.text_input("Mot de passe ", type="password")

    if st.button("Valider"):
        utils.clean_expired_tokens()
        st.experimental_set_query_params(token="")
        # If the password is correct, proceed to the main application
        if utils.check_password(hashed_password, user_input_password):
            new_token = utils.generate_token()
            utils.save_token(new_token)
            st.experimental_set_query_params(token=new_token)
            st.session_state.authenticated = True

            with st.spinner('Loading...'):
                #ime.sleep(0.3)
                st.experimental_rerun()
        else:
            st.error("Le mot de passe est incorrect. Merci d'essayer à nouveau.")
  
def print_report(msg, type="logger"):
    logger.info(msg)  # Log the message
    if type == "streamlit":
        st.write(msg)  # Display the message in Streamlit
    else:
        print(msg)  # Print the message to the console

def app():
    # Ensure input_dir exists before attempting to list files in it
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)

    st.sidebar.header(f"Spirit invoice app demo")
    menu_demo = st.sidebar.radio("Invoice:", ["Files Processing", "Upload files", "View results", "Logs"])

    files_in_directory = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
      
    if menu_demo == "Files Processing":
        st.header("Spirit invoice processing")
        if not files_in_directory:
            st.warning(f"Merci de charger un fichier")
        else:
            st.write("Fichier disponible localement")
            if st.button("Check invoice files (local)"):
                invoice_functions.process_json_files(input_dir, output_dir)

        if st.button("Test API"):
            api_url =f"{settings.api_path}/test"
            response = requests.get(api_url)

            if response.status_code == 200:
                st.success("API request successful!")
                st.json(response.json())  # Display JSON response
            else:
                st.error(f"Failed to call API. Status code: {response.status_code}")                


        if st.button("Check invoice files (API / GET)"):
                st.write("Using GET endpoint for internal test")
                api_url = f"{settings.api_path}/get_analyze_invoice"
                response = requests.get(api_url)
                if response.status_code == 200:
                    st.success("API request successful!")
                    st.json(response.json())  # Display JSON response
                else:
                    st.error(f"Failed to call API. Status code: {response.status_code}")              

        if st.button("Check invoice files (API / POST)"):  
                st.warning("Using POST endpoint, simulating a api request.")
                st.write("It can be quite long depending on the size of the json. The script takes the first file of the input folder and request the API")
                with st.spinner('Processing... Please wait'):
                    response = post_json_to_api(input_dir)
                    try:
                        if response.status_code == 200:
                            st.success("API request successful!")
                            st.json(response.json())  # Display JSON response
                        else:
                            st.error(f"Failed to call API. Status code: {response.status_code}")    
                    except Exception as e:
                        st.error("There was an error processing the file.")
                        st.error(f"Error message: {e}" )   
                        print("error in response")
                        logging.error(f"API call failed: {e}")      
        
    if menu_demo == "Upload files":
        st.header("Spirit invoice upload")
        #take files from output dir and extract the json
        uploaded_file_invoice_json = st.file_uploader("Charger un fichier de facture (json)", type=['json'])        
        uploaded_file_invoice_zip = st.file_uploader("Charger un fichier de facture (zip avec les json)", type=['zip'])        
        upload= False
        if uploaded_file_invoice_zip is not None:
            #let's check the file is valid before storing it 
            try:
                with zipfile.ZipFile(uploaded_file_invoice_zip, 'r') as zip_ref:
                    zip_ref.extractall(input_dir)
                    st.success('ZIP file uploaded and extracted successfully.')
            except Exception as e:
                st.error("There was an error processing the file.")
                st.error(f"Error message: {e}")            
        if uploaded_file_invoice_json is not None:
            try:
                file_path = os.path.join(input_dir, uploaded_file_invoice_json.name)       
                with open(file_path, 'wb') as file:
                    file.write(uploaded_file_invoice_json.getbuffer())  # Use getbuffer for BytesIO
                st.success('JSON file uploaded successfully.')
            except Exception as e:
                st.error("There was an error processing the file.")
                st.error(f"Error message: {e}")


        if files_in_directory:   
            if st.button("Supprimer les fichiers"):
                try:
                    for filename in files_in_directory:
                        os.remove(os.path.join(input_dir, filename))  # deletes the file
                    st.success("Fichier supprimé.")
                    with st.spinner('Loading...'):
                        time.sleep(0.3)
                        st.experimental_rerun()
                except Exception as e:
                    st.error(f"Erreur lors de la suppression du fichier: {e}")
            st.info("files in folder, to be processed")  
            for filename in files_in_directory:
                st.write(filename)  

    if menu_demo == "View results":
        results_file_path = os.path.join(output_dir, "export.csv")
    
        # Check if the file exists before attempting to read it
        if not os.path.exists(results_file_path):
            st.warning("No results to display, upload & process file to get results")
            return

        df = pd.read_csv(results_file_path)
        for index, row in df.iterrows():
            st.write(f"**File Name:** {row['file_name']}")
            json_data = json.loads(row['LLM_output'])
            df = pd.DataFrame(json_data.items(), columns=["Key", "Value"])
            st.dataframe(df)

    if menu_demo == "Logs":
        st.header("Spirit Logs")
        download_filename = "spirit_invoice_logs.txt"
        download_link = create_download_link(log_file, download_filename)
        st.markdown(download_link, unsafe_allow_html=True)

def post_json_to_api(directory_path):
    api_path = settings.api_path
    api_url = f"{api_path}/analyze_invoice"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    json_files = glob.glob(f"{directory_path}/*.json")
    if not json_files:
        return "No JSON files found."
    results = []
    print(f"sending {json_files[0]} ...to {api_url}")
    # Attempt to read the file with multiple encodings
    for encoding in ('utf-8-sig', 'utf-16'):
        try:
            with open(json_files[0], 'r', encoding=encoding) as file:
                json_content = file.read()
                break  # Successfully read the file
        except UnicodeDecodeError:
            continue  # Try the next encoding
    else:
        return "Failed to decode JSON file with known encodings."
    
    encoded_json = json_content.encode('utf-8')
    #response = requests.post(api_url, json=json_content, headers=headers)  
    response = requests.post(api_url, data=encoded_json, headers=headers)
    if response.status_code == 200:
        return response
    else:
        return f"Failed to send JSON data. Status code: {response.status_code}"

import base64
def create_download_link(file_path, filename):
    b64_content = base64.b64encode(get_file_content_as_string(file_path)).decode()
    return f'<a href="data:application/octet-stream;base64,{b64_content}" download="{filename}">> {filename}</a>'

def get_file_content_as_string(file_path):
    with open(file_path, 'rb') as f:
        return f.read()

if __name__ == '__main__':
    main()
