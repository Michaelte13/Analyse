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

    # Sélection des colonnes dans la barre latérale
    colonnes_toutes = list(donnees.columns)
    colonnes_numeriques = list(
        donnees.select_dtypes(include=["number"]).columns
    )

    st.sidebar.header("⚙️ Paramètres des colonnes")
    col_x = st.sidebar.selectbox(
        "Colonne Date / Heure", colonnes_toutes, index=0
    )
    col_y = st.sidebar.selectbox(
        "Colonne Puissance (kW/MW)", colonnes_numeriques, index=0
    )

    # Conversion en Datetime
    df = donnees.copy()
    df[col_x] = pd.to_datetime(df[col_x], errors="coerce")
    df = df.dropna(subset=[col_x])

    # -------------------------------------------------------------
    # FILTRE PAR MOIS / SAISON / PERIODE (MENU DÉROULANT)
    # -------------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.header("📅 Filtre Temporel")

    date_min = df[col_x].min().date()
    date_max = df[col_x].max().date()

    # Définition des options pour le menu déroulant
    options_filtre = [
        "Toutes les données",
        "--- Saisons ---",
        "❄️ Hiver",
        "☀️ Été",
        "🍂 Mi-saison",
        "--- Mois ---",
        "01 - Janvier",
        "02 - Février",
        "03 - Mars",
        "04 - Avril",
        "05 - Mai",
        "06 - Juin",
        "07 - Juillet",
        "08 - Août",
        "09 - Septembre",
        "10 - Octobre",
        "11 - Novembre",
        "12 - Décembre",
        "--- Personnalisé ---",
        "✏️ Plage de dates",
    ]

    choix_filtre = st.sidebar.selectbox(
        "Sélectionner la période :",
        options_filtre,
        index=0,
    )

    # Dictionnaire de correspondance Mois -> Numéro de mois
    mois_dict = {
        "01 - Janvier": 1,
        "02 - Février": 2,
        "03 - Mars": 3,
        "04 - Avril": 4,
        "05 - Mai": 5,
        "06 - Juin": 6,
        "07 - Juillet": 7,
        "08 - Août": 8,
        "09 - Septembre": 9,
        "10 - Octobre": 10,
        "11 - Novembre": 11,
        "12 - Décembre": 12,
    }

    # Application de la logique de filtrage
    if choix_filtre in ["--- Saisons ---", "--- Mois ---", "--- Personnalisé ---", "Toutes les données"]:
        df_filtre = df.copy()

    elif choix_filtre == "❄️ Hiver":
        df_filtre = df[df[col_x].dt.month.isin([12, 1, 2, 3])].copy()

    elif choix_filtre == "☀️ Été":
        df_filtre = df[df[col_x].dt.month.isin([6, 7, 8])].copy()

    elif choix_filtre == "🍂 Mi-saison":
        df_filtre = df[df[col_x].dt.month.isin([4, 5, 9, 10, 11])].copy()

    elif choix_filtre in mois_dict:
        mois_num = mois_dict[choix_filtre]
        df_filtre = df[df[col_x].dt.month == mois_num].copy()

    elif choix_filtre == "✏️ Plage de dates":
        plage_dates = st.sidebar.date_input(
            "Choisir la plage de dates :",
            value=(date_min, date_max),
            min_value=date_min,
            max_value=date_max,
        )
        if isinstance(plage_dates, tuple) and len(plage_dates) == 2:
            start_date, end_date = plage_dates
            df_filtre = df[
                (df[col_x].dt.date >= start_date)
                & (df[col_x].dt.date <= end_date)
            ].copy()
        else:
            df_filtre = df.copy()

    # -------------------------------------------------------------
    # AFFICHAGE DE DES RÉSULTATS
    # -------------------------------------------------------------
    if df_filtre.empty:
        st.warning("Aucune donnée disponible pour la période sélectionnée.")
    else:
        st.info(
            f"📍 **Analyse du {df_filtre[col_x].min().strftime('%d/%m/%Y')} au {df_filtre[col_x].max().strftime('%d/%m/%Y')}**"
        )

        # -------------------------------------------------------------
        # ANALYSE JOUR / NUIT & ANOMALIES
        # -------------------------------------------------------------
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
                "Fin de journée (Heure)",
                min_value=0,
                max_value=23,
                value=22,
            )

        # Qualification des périodes et des jours
        heures = df_filtre[col_x].dt.hour
        est_jour = (heures >= heure_debut_jour) & (heures < heure_fin_jour)
        df_filtre["Période"] = "🌙 Nuit"
        df_filtre.loc[est_jour, "Période"] = "☀️ Jour"

        # Date exacte pour grouper par jour
        df_filtre["Date_Jour"] = df_filtre[col_x].dt.date

        jours_fr = [
            "1. Lundi",
            "2. Mardi",
            "3. Mercredi",
            "4. Jeudi",
            "5. Vendredi",
            "6. Samedi",
            "7. Dimanche",
        ]
        df_filtre["Jour_Semaine"] = df_filtre[col_x].dt.dayofweek.map(
            lambda x: jours_fr[x] if pd.notnull(x) else None
        )

        # Calcul de la moyenne de référence par type de jour et période
        moyennes = df_filtre.groupby(["Jour_Semaine", "Période"])[
            col_y
        ].transform("mean")
        df_filtre["Moyenne_Reference"] = moyennes

        # Affichage du tableau récapitulatif
        tableau_moyennes = (
            df_filtre.groupby(["Jour_Semaine", "Période"])[col_y]
            .mean()
            .unstack("Période")
        )
        st.bar_chart(tableau_moyennes)
        st.dataframe(tableau_moyennes.style.format("{:.2f}"))

        st.markdown("---")

        # --- SYNTHÈSE DES ANOMALIES PAR JOUR CONCERNÉ ---
        st.subheader("2. Jours impactés par des dépassements ou creux")

        seuil_pct = st.slider(
            "Seuil d'écart par rapport à la moyenne (%)",
            min_value=5,
            max_value=100,
            value=20,
            step=5,
        )

        df_filtre["Limite_Haute"] = df_filtre["Moyenne_Reference"] * (
            1 + seuil_pct / 100
        )
        df_filtre["Limite_Basse"] = df_filtre["Moyenne_Reference"] * (
            1 - seuil_pct / 100
        )

        # Détection des points hors limites
        df_filtre["Est_Depassement"] = (
            df_filtre[col_y] > df_filtre["Limite_Haute"]
        )
        df_filtre["Est_Creux"] = df_filtre[col_y] < df_filtre["Limite_Basse"]

        # REGROUPEMENT PAR DATE ET PÉRIODE
        depassements_synthese = (
            df_filtre[df_filtre["Est_Depassement"]]
            .groupby(["Date_Jour", "Jour_Semaine", "Période"])
            .agg(
                Valeur_Max=(col_y, "max"),
                Moyenne_Habituelle=("Moyenne_Reference", "first"),
                Nb_Points_Anormaux=(col_y, "count"),
            )
            .reset_index()
        )

        creux_synthese = (
            df_filtre[df_filtre["Est_Creux"]]
            .groupby(["Date_Jour", "Jour_Semaine", "Période"])
            .agg(
                Valeur_Min=(col_y, "min"),
                Moyenne_Habituelle=("Moyenne_Reference", "first"),
                Nb_Points_Anormaux=(col_y, "count"),
            )
            .reset_index()
        )

        # Metrics
        col_m1, col_m2 = st.columns(2)
        col_m1.metric(
            "🔴 Jours avec dépassement",
            f"{len(depassements_synthese)} événement(s)",
        )
        col_m2.metric(
            "🔵 Jours en sous-consommation",
            f"{len(creux_synthese)} événement(s)",
        )

        subtab_haut, subtab_bas = st.tabs(
            [
                "🔴 Jours avec Dépassements",
                "🔵 Jours en Sous-consommation",
            ]
        )

        with subtab_haut:
            if not depassements_synthese.empty:
                st.warning(
                    f"Jours et périodes ayant dépassé de plus de +{seuil_pct}% la moyenne :"
                )
                st.dataframe(
                    depassements_synthese.rename(
                        columns={
                            "Date_Jour": "Date",
                            "Jour_Semaine": "Jour",
                            "Valeur_Max": "Puissance Max Atteinte",
                            "Moyenne_Habituelle": "Moyenne Attendue",
                            "Nb_Points_Anormaux": "Nombre de relevés hors norme",
                        }
                    ).style.format(
                        {
                            "Puissance Max Atteinte": "{:.2f}",
                            "Moyenne Attendue": "{:.2f}",
                        }
                    )
                )
            else:
                st.info("Aucun jour concerné par un dépassement.")

        with subtab_bas:
            if not creux_synthese.empty:
                st.info(
                    f"Jours et périodes inférieurs de plus de -{seuil_pct}% à la moyenne :"
                )
                st.dataframe(
                    creux_synthese.rename(
                        columns={
                            "Date_Jour": "Date",
                            "Jour_Semaine": "Jour",
                            "Valeur_Min": "Puissance Min Atteinte",
                            "Moyenne_Habituelle": "Moyenne Attendue",
                            "Nb_Points_Anormaux": "Nombre de relevés hors norme",
                        }
                    ).style.format(
                        {
                            "Puissance Min Atteinte": "{:.2f}",
                            "Moyenne Attendue": "{:.2f}",
                        }
                    )
                )
            else:
                st.info("Aucun jour concerné par un creux de consommation.")