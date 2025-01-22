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

css = 'body, html, p, h1, .st-emotion-cache-1104ytp h1, [class*="css"] {font-family: "Inter", sans-serif;}'
st.markdown( f'<style>{css}</style>' , unsafe_allow_html= True)

### ---------------------------------------- FUNCTIONS 

import project_functions   


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
    company_name_details = project_functions.api_json(company_number, 'company', None)
    if 'company_name' in company_name_details.keys():
        company_name_print = company_name_details['company_name']
    
    
    df_directors = project_functions.get_directors(company_number)
    
    if df_directors.shape[0] == 0:
        st.write('-- NO PERSONS FOUND --')
    
    else:
        
        st.markdown("""<style>.small-font {font-size:8px !important; padding: 0; margin: 0; line-height: 6px;}</style>""", unsafe_allow_html=True)
        st.markdown(f'<p class="small-font">Hold tight. This can take a minute.</p>', unsafe_allow_html=True)
        
        df_company_director_appointments = project_functions.get_companyDirectorAppointments(df_directors) 
    
        plot_formatting = {'title': company_name_print + ' | ' + company_number, 'node_scaler': 10, 'node_shape': 'square'}
        project_functions.plotNetwork(df_company_director_appointments, plot_formatting)
    
        st.dataframe(df_company_director_appointments)