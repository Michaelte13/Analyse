# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 13:46:50 2026

@author: m.petit
"""
   
import pandas as pd
import streamlit as st

st.title("⚡ Analyse énergétique")

st.write("Importer une courbe de charge")

fichier = st.file_uploader("Choisir un fichier Excel", type=["xlsx"])


@st.cache_data
def charger_donnees(file):
    return pd.read_excel(file)


if fichier is not None:
    donnees = charger_donnees(fichier)
    st.success("Fichier chargé avec succès !")

    tab1, tab2 = st.tabs(["📊 Graphique", "📋 Données brutes"])

    with tab1:
        st.subheader("Aperçu de la courbe de charge")

        # 1. On sépare les colonnes texte/date des colonnes numériques
        colonnes_toutes = list(donnees.columns)
        colonnes_numeriques = list(
            donnees.select_dtypes(include=["number"]).columns
        )

        if not colonnes_numeriques:
            st.error(
                "Aucune colonne numérique (ex: puissance en kW) n'a été trouvée dans le fichier."
            )
        else:
            # 2. L'utilisateur peut choisir les colonnes (ou garder la sélection par défaut)
            col_x = st.selectbox("Sélectionner la date/heure (Axe X)", colonnes_toutes, index=0)
            col_y = st.selectbox("Sélectionner la puissance / valeur (Axe Y)", colonnes_numeriques, index=0)

            # 3. On trace le graphique proprement
            st.line_chart(donnees, x=col_x, y=col_y)

    with tab2:
        st.subheader("Tableau des données")
        st.dataframe(donnees)