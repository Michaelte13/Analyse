# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 13:46:50 2026

@author: m.petit
"""
   
import pandas as pd

import streamlit as st

st.title("⚡ Analyse énergétique")

st.write("Importer une courbe de charge")

fichier = st.file_uploader(
    "Choisir un fichier Excel",
    type=["xlsx"]
)

@st.cache_data
def charger_donnees(file):
    return pd.read_excel(file)

if fichier is not None:

    donnees = charger_donnees(fichier)

    st.success("Fichier chargé avec succès !")

    tab1, tab2 = st.tabs(
        ["📊 Graphique", "📋 Données brutes"]
    )

    with tab1:
        st.subheader("Aperçu de la courbe de charge")
        st.line_chart(donnees)

    with tab2:
        st.subheader("Tableau des données")
        st.dataframe(donnees)