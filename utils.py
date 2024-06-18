import base64
import os
import uuid
from datetime import datetime, timedelta
import time
import re
import unicodedata
import hashlib  # for password 
from config import settings

token_output_dir = os.path.join(settings.working_dir , 'token')
TOKEN_EXPIRATION_TIME = 6000 
def get_file_content_as_string(file_path):
    with open(file_path, 'rb') as f:
        return f.read()

def create_download_link(file_path, filename):
    b64_content = base64.b64encode(get_file_content_as_string(file_path)).decode()
    return f'<a href="data:application/octet-stream;base64,{b64_content}" download="{filename}">> {filename}</a>'


### identification
# Directory where tokens are stored
TOKEN_DIR = token_output_dir

def generate_token():
    """
    Generate a unique token.
    """
    return str(uuid.uuid4())

def save_token(token):
    """
    Save the token on the filesystem with the current timestamp.
    """
    token_file = os.path.join(TOKEN_DIR, token)
    with open(token_file, 'w') as file:
        file.write(str(datetime.now()))

def token_exists(token):
    """
    Check if the token exists and is valid.
    """
    token_file = os.path.join(TOKEN_DIR, token)
    if os.path.isfile(token_file):
        # Optionally, check if the token is expired (e.g., valid for 1 hour)
        with open(token_file, 'r') as file:
            creation_time = datetime.fromisoformat(file.read())
        if datetime.now() - creation_time < timedelta(hours=1):
            return True
    return False

def delete_token(token):
    """
    Delete a token. Typically called on logout.
    """
    token_file = os.path.join(TOKEN_DIR, token)
    if os.path.isfile(token_file):
        os.remove(token_file)

def clean_expired_tokens():
    current_time = time.time()
    for token_file in os.listdir(TOKEN_DIR):
        # Construct the token file path
        token_path = os.path.join(TOKEN_DIR, token_file)
        
        # Check the file creation time and remove if expired
        creation_time = os.path.getctime(token_path)  # Gets the file creation time
        if (current_time - creation_time) > TOKEN_EXPIRATION_TIME:
            os.remove(token_path)


# Simple function to hash the password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Simple function to check the password against the hash
def check_password(hashed_password, user_input_password):
    hashed_input = hash_password(user_input_password)
    return hashed_password == hashed_input


def normalize_string(s):
    if not isinstance(s, str):
        # You could also convert it to a string (if that's acceptable) or handle the error as appropriate for your application.
        raise ValueError(f"Expected a string, got {type(s)} instead.")

    # Remove accents
    s = ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))

    # Convert to lower case
    s = s.lower()

    # Remove extra spaces
    s = ' '.join(s.split())

    return s

def inclusion_check(main_string, target_string):
    # Ensure both inputs are strings
    if not isinstance(main_string, str) or not isinstance(target_string, str):
        # Handle the error: either raise an exception or return a default value/false.
        raise ValueError(f" >> Both main_string and target_string must be of type str. Got {type(main_string)} for {main_string} and {type(target_string)} for {target_string}.")
    main_string_normalized = normalize_string(main_string)
    target_string_normalized = normalize_string(target_string)
    
    # Use regex for a more flexible check, which can handle cases where the words in your target string are surrounded by other characters or words
    pattern = re.compile(r'\b' + re.escape(target_string_normalized) + r'\b')
  
    return bool(pattern.search(main_string_normalized))

import yaml

def parse_prompts(file_path):
    with open(file_path, 'r') as file:
        prompts = yaml.safe_load(file.read())
    return prompts



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