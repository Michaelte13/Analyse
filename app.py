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

    # Définition des onglets
    tab1, tab2 = st.tabs(
        ["📊 Graphique temporel", "🌙 Analyse Jour / Nuit & Anomalies"]
    )

    # Sélection des colonnes
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

    # Conversion en Datetime
    df = donnees.copy()
    df[col_x] = pd.to_datetime(df[col_x], errors="coerce")

    # ONGLET 1 : Graphique temporel classique
    with tab1:
        st.subheader("Courbe de charge temporelle")
        st.line_chart(df, x=col_x, y=col_y)

    # ONGLET 2 : Moyennes & Détection des anomalies
    with tab2:
        st.subheader("1. Moyennes par jour de la semaine (Jour vs Nuit)")

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

        # Calcul des colonnes Période et Jour
        heures = df[col_x].dt.hour
        est_jour = (heures >= heure_debut_jour) & (heures < heure_fin_jour)
        df["Période"] = "🌙 Nuit"
        df.loc[est_jour, "Période"] = "☀️ Jour"

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

        # Calcul de la moyenne de référence par (Jour_Semaine, Période)
        moyennes = df.groupby(["Jour_Semaine", "Période"])[col_y].transform(
            "mean"
        )
        df["Moyenne_Reference"] = moyennes

        # Affichage du tableau de référence des moyennes
        tableau_moyennes = (
            df.groupby(["Jour_Semaine", "Période"])[col_y]
            .mean()
            .unstack("Période")
        )
        st.bar_chart(tableau_moyennes)
        st.dataframe(tableau_moyennes.style.format("{:.2f}"))

        st.markdown("---")

        # --- SECTION ANOMALIES ---
        st.subheader("2. Détection des dépassements et creux inhabituels")

        # Curseur pour régler la tolérance en %
        seuil_pct = st.slider(
            "Seuil d'écart par rapport à la moyenne (%)",
            min_value=5,
            max_value=100,
            value=20,
            step=5,
            help="Affiche les points qui dépassent de X% la moyenne habituelle du même jour/période.",
        )

        # Calcul des limites haute et basse
        df["Limite_Haute"] = df["Moyenne_Reference"] * (1 + seuil_pct / 100)
        df["Limite_Basse"] = df["Moyenne_Reference"] * (1 - seuil_pct / 100)

        # Filtrage
        depassements = df[df[col_y] > df["Limite_Haute"]].copy()
        sous_consommations = df[df[col_y] < df["Limite_Basse"]].copy()

        # Indicateurs rapides (Metrics)
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("🔴 Dépassements inhabituels", f"{len(depassements)} pts")
        col_m2.metric(
            "🔵 Consommations très basses", f"{len(sous_consommations)} pts"
        )

        # Affichage sous forme de sous-onglets pour la clarté
        subtab_haut, subtab_bas = st.tabs(
            ["🔴 Dépassements (Plus élevé)", "🔵 Creux (Plus bas)"]
        )

        with subtab_haut:
            if not depassements.empty:
                st.warning(
                    f"Mesures dépassant de plus de +{seuil_pct}% la moyenne habituelle :"
                )
                st.dataframe(
                    depassements[
                        [
                            col_x,
                            "Jour_Semaine",
                            "Période",
                            col_y,
                            "Moyenne_Reference",
                        ]
                    ].rename(
                        columns={
                            col_y: "Valeur Mesurée",
                            "Moyenne_Reference": "Moyenne Habituelle",
                        }
                    )
                )
            else:
                st.info("Aucun dépassement anormal détecté avec ce seuil.")

        with subtab_bas:
            if not sous_consommations.empty:
                st.info(
                    f"Mesures inférieures de plus de -{seuil_pct}% à la moyenne habituelle :"
                )
                st.dataframe(
                    sous_consommations[
                        [
                            col_x,
                            "Jour_Semaine",
                            "Période",
                            col_y,
                            "Moyenne_Reference",
                        ]
                    ].rename(
                        columns={
                            col_y: "Valeur Mesurée",
                            "Moyenne_Reference": "Moyenne Habituelle",
                        }
                    )
                )
            else:
                st.info("Aucune sous-consommation anormale détectée.")