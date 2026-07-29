# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 13:46:50 2026

@author: m.petit
"""

import streamlit as st
import pandas as pd

st.title("Analyse énergétique")

st.write("Importer une courbe de charge")

fichier = st.file_uploader(
    "Choisir un fichier Excel",
    type=["xlsx"]
)

if fichier is not None:
    donnees = pd.read_excel(fichier)

    st.success("Fichier chargé avec succès !")

    st.write(donnees)