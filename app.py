# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 13:46:50 2026

@author: m.petit
"""
   
import pandas as pd
import streamlit as st

st.title("⚡ Analyse énergétique")

fichier = st.file_uploader("Choisir un fichier Excel", type=["xlsx"])


@st.cache_data
def charger_donnees(file):
    return pd.read_excel(file)


if fichier is not None:
    donnees = charger_donnees(fichier)
    st.success("Fichier chargé avec succès !")

    # Définition des 2 nouveaux onglets
    tab1, tab2 = st.tabs(["📊 Graphique temporel", "🌙 Analyse Jour / Nuit"])

    # 1. Sélection des colonnes communes
    colonnes_toutes = list(donnees.columns)
    colonnes_numeriques = list(
        donnees.select_dtypes(include=["number"]).columns
    )

    st.sidebar.header("Paramètres des colonnes")
    col_x = st.sidebar.selectbox(
        "Colonne Date / Heure", colonnes_toutes, index=0
    )
    col_y = st.sidebar.selectbox(
        "Colonne Puissance (kW/MW)", colonnes_numeriques, index=0
    )

    # Convertir la colonne X en format Datetime pour pouvoir extraire les heures et jours
    df = donnees.copy()
    df[col_x] = pd.to_datetime(df[col_x], errors="coerce")

    # ONGLET 1 : Graphique classique
    with tab1:
        st.subheader("Courbe de charge temporelle")
        st.line_chart(df, x=col_x, y=col_y)

    # ONGLET 2 : Moyennes Jour / Nuit par jour de la semaine
    with tab2:
        st.subheader("Moyennes par jour de la semaine (Jour vs Nuit)")

        # Réglage des plages d'heures
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            heure_debut_jour = st.number_input(
                "Début de journée (Heure)",
                min_value=0,
                max_value=23,
                value=6,
            )
        with col_h2:
            heure_fin_jour = st.number_input(
                "Fin de journée (Heure)", min_value=0, max_value=23, value=22
            )

        # Création de la colonne Jour / Nuit
        heures = df[col_x].dt.hour
        est_jour = (heures >= heure_debut_jour) & (heures < heure_fin_jour)
        df["Période"] = "🌙 Nuit"
        df.loc[est_jour, "Période"] = "☀️ Jour"

        # Nom des jours en français
        jours_fr = [
            "1. Lundi",
            "2. Mardi",
            "3. Mercredi",
            "4. Jeudi",
            "5. Vendredi",
            "6. Samedi",
            "7. Dimanche",
        ]
        df["Jour_Semaine"] = df[col_x].dt.dayofweek.map(
            lambda x: jours_fr[x] if pd.notnull(x) else None
        )

        # Calcul de la moyenne regroupée
        tableau_moyennes = (
            df.groupby(["Jour_Semaine", "Période"])[col_y]
            .mean()
            .unstack("Période")
        )

        # Affichage du graphique comparatif
        st.bar_chart(tableau_moyennes)

        # Affichage du tableau de chiffres
        st.write("**Tableau des moyennes (kW) :**")
        st.dataframe(tableau_moyennes.style.format("{:.2f}"))