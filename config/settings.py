from dotenv import load_dotenv
import os
import json

load_dotenv()
# SERVER_PWD = os.getenv('SERVER_PWD')
# SERVER_IP = os.getenv('SERVER_IP')

SERVER_PWD = "/home/jaydev/kshatra/creative-ai/spirit/CognitiveConstructor"
SERVER_IP = "127.0.0.1"



client = "spirit"
working_dir = os.path.join(SERVER_PWD, 'app', 'clients', client)

#define api_path
config_path = 'streamlit_apps_config.json'
with open(config_path) as config_file:
    config = json.load(config_file)
current_app = "invoice"
filtered_apps = [app for app in config['apps'] if app['client'] == client and app['name'] == current_app]
# If there's exactly one app matching the criteria, use it
if len(filtered_apps) == 1:
    api_path = f"http://{SERVER_IP}:{str(filtered_apps[0]['api_port'])}"