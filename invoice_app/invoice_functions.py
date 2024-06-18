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
openai.api_key = os.getenv('OPENAI_API_KEY')

MAX_TOKEN_COUNT = 32000
MAX_LENGTH_MULTIPLIER = 5
TOKEN_COUNT_LIMIT_FOR_MODEL = 15500
TOKEN_COUNT_SKIP_THRESHOLD = 31000

class Result(BaseModel):
    vendorEmail: str
    uo_2: str
    invoiceNumber: str
    vendorCode: str
    commitmentCode: str
    title: str
    dueDate: str
    documentType: str
    vendorSiret: str
    projectCode: str
    ttc: str
    tiers: str
    ht: str
    dateDocument: str
    subChapter: str
    commitment: str
    project: str
    invoiceType: str

def estimate_token_count(text):
    """Estimate the number of tokens based on the text length.
    Rough estimation assuming an average token length, including spaces."""
    return len(text) / 5

def extract_data_json(json_data):
    print("""Extract and process data from a JSON file.""")
    
    pages_data = json_data.get('pages', [])
    sentences = []

    for page in pages_data:
        if page.get('$type') == 'PageContent':
            for text_zone in page.get('Items', []):
                if text_zone.get('$type') == 'TextZone':
                    for line in text_zone.get('Ln', []):
                        for item in line.get('Items', []):
                            if item.get('$type') == 'Word':
                                sentences.append(item.get('Value', ''))

    sentence = ' '.join(sentences)
    #file_name = os.path.basename(json_file_path)
    file_name = json_data.get('nom_pjs', [])
    return {'sentence': sentence, 'file_name': file_name}

def process_json_files(directory_path, output_dir_path):
    """Get files from local folder and process one at a time"""
    print("process_json_files")
    json_files = glob.glob(f"{directory_path}/*.json")
    results = []
    print(f"Processing {len(json_files)} files...")

    for json_file_path in tqdm(json_files, desc="Progress"):
        print(f"Processing file: {json_file_path}")
        try:
            with open(json_file_path, 'rb') as file:
                raw_data = file.read()
                if not raw_data:
                    print(f"Warning: The file {json_file_path} is empty.")
                    return None
                encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
                json_data = json.loads(raw_data.decode(encoding))
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from the file {json_file_path}: {e}")
            return None
        invoice_data = process_json_file(json_data, directory_path, output_dir_path)
        results.append(invoice_data)
        
        if json_data is None:
            continue
    output_file_path = os.path.join(output_dir_path, "export.csv")       
    if not os.path.exists(output_dir_path):
        os.makedirs(output_dir_path)
    
    print(results)

    with open(output_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            "sentence", "file_name", "LLM_output"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for item in results:
            try:
                writer.writerow(item)
            except ValueError as e:  # Catch the correct exception
                print(f"Cannot write the CSV for {json_file_path}: {e}")
                # Log the error or take other appropriate action
    
    return results


def process_json_file(json_data, directory_path, output_dir_path):
    logging.info("Processing a json file.")

    invoice_data = extract_data_json(json_data)
    sentence = invoice_data.get('sentence', '')

    token_count = estimate_token_count(sentence)

    if token_count > MAX_TOKEN_COUNT:
        max_length = MAX_TOKEN_COUNT * MAX_LENGTH_MULTIPLIER
        invoice_data['sentence'] = sentence[:max_length]

    document_details = invoice_data
    sci_name_found, id_engagement_found, id_project_found = check_invoice(invoice_data['sentence'], directory_path, output_dir_path)

    #add invoice check from

    logging.info(f"Estimated token count for {json_data.get('nom_pjs', [])}: {token_count}")

    model = choose_model_based_on_token_count(token_count)
    logging.info(token_count)
    #if token_count > TOKEN_COUNT_SKIP_THRESHOLD:
    #    logging.warning(f"{json_data.get('nom_pjs', [])} skipped due to token limit")
    #    return {"error": "Token count exceeds limit, processing skipped."}

    try:
        response = make_api_call_to_generate_output(model, document_details)
        logging.info("API call successful.")
        llm_output = response.choices[0].message.content
        llm_output = clean_json_string(llm_output)
        llm_output_dict = json.loads(llm_output)
        llm_output_dict['sci_name_found']=sci_name_found
        llm_output_dict['id_engagement_found']=str(id_engagement_found)
        llm_output_dict['id_project_found']=str(id_project_found)
        llm_output_updated_str = json.dumps(llm_output_dict)
        # Add the updated LLM output to invoice_data
        invoice_data["LLM_output"] = llm_output_updated_str
        
        return invoice_data
    except Exception as e:
        logging.error(f"API call failed: {e}")
        return {"error": "Failed to make API call."}


def choose_model_based_on_token_count(token_count):
    #return 'gpt-4-0125-preview' if token_count > TOKEN_COUNT_LIMIT_FOR_MODEL else 'gpt-3.5-turbo-0125'
    return 'gpt-4o'
    #return 'gpt-4-0125-preview'

def make_api_call_to_generate_output(model, document_details):
    response = openai.chat.completions.create(
            model=model,
            temperature=0.1,
            response_format={ "type": "json_object" },
            messages=[
                {
                    "role":"system", 
                    "content":
                        f"""Tu es un système de lecture automatisé de factures et de situations de travaux pour une entreprise de type SCI (société civile immobilière). À partir de données de l’OCR, tu génères une sortie JSON avec les clés suivantes et leurs valeurs respectives. Les dates doivent être au format ISO 8601. Si la clé est absente, le champ est rempli avec une chaîne vide dans le jeu de données. Voici la structure :
                        "tiers" : Le nom du fournisseur (qui ne peut pas être une SCI).
                        "tiersEmail" : adresse e-mail du fournisseur.
                        "numeroPiece" : Contient la référence (Réf. ou numéro de facture) du document, qui peut contenir des lettres et des chiffres et un slash si ce sont des situations de travaux.
                        "tiersSiret" : le numéro SIRET du fournisseur ; composé de 14 chiffres : les 9 chiffres du SIREN et 5 chiffres propres à l’établissement.
                        "ttc" : Le montant total à payer, toutes taxes comprises (TTC) sans le signe ou la mention euro, sans espace et un point pour les décimales. Vigilance sur le taux de TVA appliqué car il y a de forte variabilité, tu dois te baser sur le total TTC. Laisse ce champs vide s’il s’agit d’une situation de travaux.
                        "ht" : Le montant total du document au format hors taxes (HT) sans le signe ou la mention euro, sans espace et un point pour le décimales. Laisse ce champs vide s’il s’agit d’une situation de travaux.
                        "dateDocument" : La date d’émission du document.
                        "dueDate" : Indique la date de l’échéance du document. Elle est fixée à 30 jours pour une facture, 45 jours pour les engagements de travaux. Elle sera payée en milieu de mois (le 15) ou ou fin du mois (30 ou 31) suivant la date d’émission de la facture et ajoute 15 jours de plus pour les situations de travaux.
                        "typeFacture" : Indique le type de la facture (facture, situation de travaux ou avoir).
                        "sousChapitre" : toujours "09 - FACTURES"
                        "typeDocument" : Spécifie le type de document en fonction de la typologie suivante. Par défaut, le code est 09.01 - Factures, mais voici les informations possibles :
                        09.13 - Factures avec engagement à créer / 09.12 - Factures travaux / 09.11 - Factures prorata /09.09 - Factures SAV / 09.08 - Factures travaux et prorata / 09.05 - Factures développement avancé (après promesse) / 09.06 - Factures études / 09.07 - Factures marketing / 09.21 - Honoraires juridiques / 09.22 - Honoraires prescripteurs / 09.03 - Factures administration et gestion / 09.31 - Situations travaux MOE BPCC / 09.32 - Situations travaux MOE externe / 09.04 - Factures développement (avant promesse) / 09.30 - Situations travaux / 09.10 - Factures service clients."""
                },
                {"role":"user", "content":f"Here are the document details: \n{document_details}, create a JSON output"}
            ]
        )
    return response    

def clean_json_string(data):
    llm_output_clean = json.loads(data)
    data = json.dumps(llm_output_clean, ensure_ascii=False, indent=4)
    data = data.replace('\n', ' ').replace('\r', '')
    return data


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
    id_project_found = None
    id_sci_found = None

    sci_name_found = any(name.lower() in json_data for name in sci_ref['Name'])    
    if sci_name_found:
        # If SCI name is found, retrieve the corresponding 'id'
        for name in sci_ref['Name']:
            if name.lower() in json_data:
                id_sci_found = sci_ref[sci_ref['Name'].str.lower() == name.lower()]['Id'].iloc[0]
                sci_name_found = name.lower()
                break
        if id_sci_found:
            st.info(f"SCI Name '{name.lower()}' found in text data with ID {id_sci_found}.")
        else:
            st.warning("SCI found but not the id not found in text data.")
    else:
        st.warning("SCI Name not found in text data.")
    
    
    if(id_sci_found):
        # Find projects with matching ProjectCompanyId
        matching_projects = projects_ref[projects_ref['ProjectCompanyId'] == id_sci_found]   
        json_data_lower = json_data.lower() 
    
        if not matching_projects.empty:
            # Find the project with the smallest ID
            smallest_id_project = matching_projects.loc[matching_projects['Id'].idxmin()]
            project_name_found = smallest_id_project['Name'].lower()
            id_project_found = smallest_id_project['Id']

            # Display the project found
            st.info(f"Project found in text data: {project_name_found} {id_project_found}")
        else:
            st.warning("No Project found in text data.")
    
    id_engagement_found=0
    '''
    engagements_ref['Id'] = engagements_ref['Id'].astype(str)  # Make sure the 'Id' column is of string type
    engagements_ref_found = any(str(id_engagement) in json_data for id_engagement in engagements_ref['Id'])
    id_engagement_found=0

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
        else:
            st.warning("id_engagement found but not the id not found in text data.")
    else:
        st.warning("id_engagement not found in text data.")
    '''
    
    return sci_name_found, id_engagement_found, id_project_found