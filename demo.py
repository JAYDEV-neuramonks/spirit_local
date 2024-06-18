# demo space

import pandas as pd
import streamlit as st
import os
import sys
import datetime
import logging

#from fuzzywuzzy import fuzz
#from fuzzywuzzy import process

import yaml

from config import settings
import utils
from fuzzywuzzy import fuzz
#from data_processing import utils, sales_matchers, operations_analyser, subscriptions_matcher

import os
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
load_dotenv()
OPENAI_APIKEY = os.getenv('OPENAI_API_KEY')

# Configure logging
log_output_dir = os.path.join(settings.working_dir , 'logs')
output_dir = os.path.join(settings.working_dir , 'output')
input_dir = os.path.join(settings.working_dir, 'input')
prompts_dir = os.path.join(settings.working_dir, 'prompts')

if not os.path.exists(log_output_dir):
    os.makedirs(log_output_dir)

# The filename where to store the logs
log_file = os.path.join(log_output_dir, 'processing.log')

# Check if logging is already set up by looking if the root logger has handlers
root_logger = logging.getLogger()
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # or whichever level you want
if not root_logger.hasHandlers():
    # We are here because the script runs for the first time in this session
    logging.basicConfig(
        filename=log_file, 
        level=logging.INFO, 
        format='%(asctime)s %(levelname)s %(message)s', 
        datefmt='%Y-%m-%d %H:%M:%S'
    )
# Create a console handler with a higher level
console_handler = logging.StreamHandler(sys.stdout)  # You can also use sys.stderr
console_handler.setLevel(logging.INFO)
# Set a simple format for the console handler
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
        matching_demo_app()  # this is your main app function
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
  

def matching_demo_app():
    chat_model = get_gpt_llm()

    # Menu for user selection
    st.sidebar.header(f" Matching app demo")
    menu_demo = st.sidebar.radio("Matching:", ["View profiles", "Search matching", "Create tags", "Create matching" ])


    if menu_demo == "View profiles":
        st.header("View Profiles")
        

            
    if menu_demo == "Search matching":
        st.header("Get top  matches for a profile")
        
        prompts_path = os.path.join(prompts_dir, 'prompts.txt')
        prompts = parse_prompts(prompts_path)
        prompt_get_tags = prompts[0]['prompt_content']
        
        
        if st.button('Create tags'):
            st.info(f"Desactivated")
            return
            with st.spinner('Please wait... Process is running.'):
                st.info(f"The process iterate each profile and add tags for description and linkedin")
                output_dir = os.path.join(settings.working_dir, 'output')  # Update this path to your specific directory
                files_to_delete = os.listdir(output_dir)
                for file_name in files_to_delete:
                    file_path = os.path.join(output_dir, file_name)
                    try:
                        os.remove(file_path)  # Delete the file
                        print(f"Deleted file: {file_path}")
                    except Exception as e:
                        print(f"Error deleting file: {file_path}, Error: {e}")
                prompt_get_tags = prompts[0]['prompt_content']
                
                profiles = create_profiles_tags(prompt_get_tags, chat_model)


    if menu_demo == "Create matching":
        st.header("Create tags for Profiles")
      


def get_gpt_llm(model_name="gpt-3.5-turbo-16k", temperature=0):
    #todo define better + parameter
    max_tokens=500
    chat_params = {
        "model": model_name, # Bigger context window
        "openai_api_key": OPENAI_APIKEY,
        "temperature": temperature, # To avoid pure copy-pasting from docs lookup
        "max_tokens": max_tokens
    }
    llm = ChatOpenAI(**chat_params)

    return llm

# Function to parse the YAML file with prompts
def parse_prompts(file_path):
    with open(file_path, 'r') as file:
        prompts = yaml.safe_load(file.read())
    return prompts


def print_report(msg, type="logger"):
    logger.info(msg)  # Log the message
    if type == "streamlit":
        st.write(msg)  # Display the message in Streamlit
    else:
        print(msg)  # Print the message to the console
        




def encrypt(text):
    result = ""
    for char in text:
        if char.isalpha():  # Check if the character is a letter
            # Shift character by 1, wrap around if necessary
            shifted_char = chr((ord(char.lower()) - ord('a') + 1) % 26 + ord('a'))
            # Preserve the original case (uppercase/lowercase)
            if char.isupper():
                shifted_char = shifted_char.upper()
            result += shifted_char
        else:
            # For non-alphabetic characters, keep them as is
            result += char

    return result


if __name__ == '__main__':
    main()
