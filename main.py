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

    
    # utils.clean_expired_tokens()
    # query_params = st.experimental_get_query_params()
    # token = query_params.get('token') 
    
    #  # Check if the token is not None and if it's valid
    # if token is not None and utils.token_exists(token[0]):  # token_exists checks if it's a valid token
    #     st.session_state.authenticated = True
    # else:
    #     # If no valid token, the user is not authenticated
    #     st.session_state.authenticated = False

    #####
    # remove this line to activate authentification
    st.session_state.authenticated = True
    #####
    

    if st.session_state.authenticated:
        #st.info("Session valide")
         st.write("Welcome") # this is your main app function
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
  



if __name__ == '__main__':
    main()
