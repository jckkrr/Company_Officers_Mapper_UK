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
        
    

# A function to plot out the dataframe as a network map
def plotNetwork(df, plot_formatting):
  
    ###
                    
    g = pyvis.network.Network(
        directed=False, 
        width = "100%", 
    )
    
    g.force_atlas_2based(spring_length=3)
    
    ### Nodes: collate list of nodes, then prepare
     
    palette = {
        'type_0': 'rgba(0, 150, 25, 1)',
        'type_1': 'rgba(102, 99, 236, 1)', 
        'tertiary': 'rgba(0, 150, 25, 1)',
        'blank_image': 'https://upload.wikimedia.org/wikipedia/commons/a/a7/Blank_image.jpg',
    }
    
    
    ##
    
    df = df.copy()
    
    df['name'] = df['name'].str.upper()
    df['name'] = [name.split(',')[1] + ' ' + name.split(',')[0] if ',' in name else name for name in df['name']]

    for index, row in df.iterrows():
        if row['name'].split(' ')[0] in ['MR', 'MRS', 'MS', 'MISS']:
            print(row['name'])
            df.loc[index, 'name '] = row['name'] = ' '.join(row['name'].split(' ')[1:])
    
    df['name'] = [x.strip() for x in df['name']]
        
    ##
        
    df_nodes = pd.concat([df['name'], df['company_name']]).value_counts().to_frame().rename(columns = {0: 'count'})
    df_nodes['proportion'] = df_nodes['count'] / df_nodes['count'].max() # Normalise. Scaling happens when node is added
    df_nodes['size'] = 5 + (df_nodes['proportion'] * 15)
    df_nodes['type'] = np.where(df_nodes.index.isin(df['name']), 1, 0)
    df_nodes = df_nodes.sort_index()
        
    df_nodes['rgba'] = np.where(df_nodes['type'] == 1, palette['type_1'], palette['type_0'])
    df_nodes['shape'] = np.where(df_nodes['type'] == 1, 'square', 'circularImage')
    df_nodes['image'] = np.where(df_nodes['type'] == 1, '', palette['blank_image'])
    df_nodes['font_size'] = 10 + (df_nodes['proportion'] * 15)
    
    
    ### Add nodes
    nodes_unique = list(df_nodes.index)
    for node in nodes_unique:
        g.add_node(node, 
                   size = df_nodes.loc[node, 'size'], 
                   color = df_nodes.loc[node, 'rgba'],
                   shape = df_nodes.loc[node, 'shape'],
                   image = df_nodes.loc[node, 'image'],
                   font = (f'{df_nodes.loc[node, "font_size"]} Manrope black')
                  )
        
     
    ### Add edges
    for index, row in df.iterrows():
        g.add_edge(row['name'], row['company_name'], color = palette['type_0'])
    
    
    ### Display   
    path = '/tmp'
    g.save_graph(f'temp.html')
    HtmlFile = open(f'temp.html', 'r', encoding='utf-8')
    source_code = HtmlFile.read()
    
    components.html(
        source_code, 
        height = int(610), 
        width = int(777)
    )
    
    ### Make some slight improvements to the download graph
    source_code = source_code.replace('height: 600px', 'height: 1000').replace('height: 500px', 'height: 1000')    
    source_code = source_code.replace('border: 1px solid lightgray', 'border: 0px solid lightgray') # removes border that otherwise appears
    source_code = source_code.replace('background-color:rgba(200,200,200,0.8)', 'background: linear-gradient(to bottom right, #33ccff 0%, #ff99cc 100%);')
    source_code = source_code.replace(
        '</style>', 
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700;900&display=swap"></style>'
    )
    source_code = source_code.replace(
        '<body>', 
        f'<body><span style="font-family: Manrope; font-size: 24px; font-weight:600">{plot_formatting["title"]}</span><br> \
            <span style="font-family: Inter; font-size: 14px;"><b>Open Investigation Tools</b> | <a href="http://www.constituent.online" style="color:#000000;">constituent.online</a></span>'
    )

    st.download_button(
        label = "For easier analysis, download as HTML",
        data = source_code,
        file_name = "downloadable_html.html",
        mime = "application/octet-stream",
    )
    