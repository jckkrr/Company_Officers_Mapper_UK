############## Constistuent.Online #################
####### Code-free analysis for curious folk. ######

### An application for mapping out the networks of business connections of a company's directors, officers and significant others.

## streamlit run "C:\Users\Jack\Documents\Python_projects\streamlit_apps\uk_companies_house_mapper\streamlit_app.py"

### --------------------------------------- IMPORTS 

import json
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from pyvis.network import Network
import pyvis
import re
import requests

import project_functions 

css = 'body, html, p, h1, .st-emotion-cache-1104ytp h1, [class*="css"] {font-family: "Inter", sans-serif;}'
st.markdown( f'<style>{css}</style>' , unsafe_allow_html= True)

### ---------------------------------------- FUNCTIONS   

## A basic function to return resutls from API query to Companies House. 
## Note the three required inputs. The last one can be None.
def api_json(id_number, id_type, additional_information):
        
    base_url = f'https://api.companieshouse.gov.uk/{id_type}/{id_number}'
    url = base_url if additional_information == None else base_url + '/' + additional_information        
    response = requests.get(url, auth=(api_key, '')).json()
    
    return response


## This function returns a dataframe containing all of a companies Officers and Persons With Significant Control.
def get_directors(company_number):

    df_directors = pd.DataFrame()

    json_company = api_json(company_number, 'company', None)

    print(json_company)
    
    api_person_types = ['officers', 'persons-with-significant-control']

    for person_type in api_person_types:
        json_data = api_json(company_number, 'company', person_type)
        df_json_data = pd.json_normalize(json_data['items'])
        df_directors = pd.concat([df_directors, df_json_data]).reset_index(drop = True)
    
    df_directors.insert(0, 'company_name', json_company['company_name'])
    df_directors.insert(1, 'company_number', json_company['company_number'])
    df_directors.insert(2, 'company_status', json_company['company_status'])
    df_directors.insert(3, 'date_of_creation', json_company['date_of_creation'])
    
    return df_directors


## A function that returns a dataframe listing a director's appointments. 
## Note that it only shows that first xxx appointments, so for institutional investors, it will be incomplete

def get_directors_appointments(director_id):

    df_director_appointments = pd.DataFrame()

    json_appointments = api_json(director_id, 'officers', 'appointments')
    
    ## For those with more than 1 page of results
    total_appointments = json_appointments['total_results']
    if total_appointments > json_appointments['items_per_page']:
        json_appointments = api_json(director_id, 'officers', f'appointments?items_per_page={total_appointments}')
    
    number_of_appointments = len(json_appointments['items'])
    for a in range(0, number_of_appointments):

        appointment_data = json_appointments['items'][a]
        df_a = pd.json_normalize(appointment_data)
        df_director_appointments = pd.concat([df_director_appointments, df_a]).reset_index(drop = True)

    return df_director_appointments


## A function to collate the appointments of all people of a company's Officers and PSCs.
def get_companyDirectorAppointments(df_directors):
    
    director_ids = [x.split('/')[-2] for x in df_directors['links.officer.appointments'] if pd.notna(x)]
    
    df_company_director_appointments = pd.DataFrame()
    
    for director_id in director_ids:
                    
        df_da = get_directors_appointments(director_id)
        df_company_director_appointments = pd.concat([df_company_director_appointments, df_da]).reset_index(drop = True)
        
    for col in [x for x in df_company_director_appointments if x.startswith('appointed_to.')]:
        df_company_director_appointments = df_company_director_appointments.rename(columns = {col: col.replace('appointed_to.', '').strip()})
    
    
    df_company_director_appointments = pd.concat([df_directors, df_company_director_appointments])
    df_company_director_appointments = df_company_director_appointments.reset_index(drop = True)
    
    return df_company_director_appointments
        
    
### Plotting function contained in project_functions.py
    

### --------------------------------------- RUN 

required_columns = ['node_left', 'connection', 'node_right']

st.markdown("**Open Investigation Tools** | [constituent.online](%s)" % 'http://www.constituent.online')
    
st.title('Company Officers Mapper (UK)')
st.write('An easy way to see who is in business with who.')

company_number = st.text_input('Enter company number (which you can find on [Companies  House](%s)) &#x2935;' % 'https://find-and-update.company-information.service.gov.uk/',  '08355862') .strip()

if company_number:  # 04241161
    
    st.markdown("""<style>.getting-data {font-size:14px !important; padding: 0; margin: 0; line-height: 6px;}</style>""", unsafe_allow_html=True)
    st.markdown(f'<p class="getting-data">Getting data...</p>', unsafe_allow_html=True)
    
    company_name_print = None
    company_name_details = api_json(company_number, 'company', None)
    if 'company_name' in company_name_details.keys():
        company_name_print = company_name_details['company_name']
    
    
    df_directors = get_directors(company_number)
    
    if df_directors.shape[0] == 0:
        st.write('-- NO PERSONS FOUND --')
    
    else:
        
        st.markdown("""<style>.small-font {font-size:8px !important; padding: 0; margin: 0; line-height: 6px;}</style>""", unsafe_allow_html=True)
        st.markdown(f'<p class="small-font">Hold tight. This can take a minute.</p>', unsafe_allow_html=True)
        
        df_company_director_appointments = get_companyDirectorAppointments(df_directors) 
    
        plot_formatting = {'title': company_name_print + ' | ' + company_number, 'node_scaler': 10, 'node_shape': 'square'}
        project_functions.plotNetwork(df_company_director_appointments, plot_formatting)
    
        st.dataframe(df_company_director_appointments)