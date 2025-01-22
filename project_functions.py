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
    