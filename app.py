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

    options_filtre = [
        "Toutes les données",
        "--- Saisons ---",
        "❄️ Hiver",
        "🌸 Printemps",
        "☀️ Été",
        "🍂 Automne",
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
        "✏️ Plage de dates",
    ]

    choix_filtre = st.sidebar.selectbox(
        "Sélectionner la période :",
        options_filtre,
        index=0,
    )

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

    if choix_filtre in ["--- Saisons ---", "--- Mois ---", "Toutes les données"]:
        df_filtre = df.copy()

    elif choix_filtre == "❄️ Hiver":
        df_filtre = df[df[col_x].dt.month.isin([12, 1, 2])].copy()

    elif choix_filtre == "🌸 Printemps":
        df_filtre = df[df[col_x].dt.month.isin([3, 4, 5])].copy()

    elif choix_filtre == "☀️ Été":
        df_filtre = df[df[col_x].dt.month.isin([6, 7, 8])].copy()

    elif choix_filtre == "🍂 Automne":
        df_filtre = df[df[col_x].dt.month.isin([9, 10, 11])].copy()

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
    # AFFICHAGE DES RÉSULTATS
    # -------------------------------------------------------------
    if df_filtre.empty:
        st.warning("Aucune donnée disponible pour la période sélectionnée.")
    else:
        st.info(
            f"📍 **Analyse du {df_filtre[col_x].min().strftime('%d/%m/%Y')} au {df_filtre[col_x].max().strftime('%d/%m/%Y')}**"
        )

        # -------------------------------------------------------------
        # 1. PARAMÉTRAGE JOUR / NUIT & MOYENNES GLOBALES
        # -------------------------------------------------------------
        st.subheader("1. Moyennes globales par jour de la semaine (Jour vs Nuit)")

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

        # Qualification Jour / Nuit
        heures = df_filtre[col_x].dt.hour
        est_jour = (heures >= heure_debut_jour) & (heures < heure_fin_jour)
        df_filtre["Période"] = "🌙 Nuit"
        df_filtre.loc[est_jour, "Période"] = "☀️ Jour"

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

        # Affichage du graphique récapitulatif global
        tableau_moyennes = (
            df_filtre.groupby(["Jour_Semaine", "Période"])[col_y]
            .mean()
            .unstack("Période")
        )
        st.bar_chart(tableau_moyennes)
        st.dataframe(tableau_moyennes.style.format("{:.2f}"))

        st.markdown("---")

        # -------------------------------------------------------------
        # 2. DÉTECTION DES DÉPASSEMENTS (RÉFÉRENCE : MOYENNE DES 3 SEMAINES PRÉCÉDENTES)
        # -------------------------------------------------------------
        st.subheader("2. Dépassements de consommation (Comparaison vs Moyenne des 3 semaines précédentes)")

        seuil_pct = st.slider(
            "Seuil de dépassement par rapport aux 3 semaines précédentes (%)",
            min_value=5,
            max_value=100,
            value=20,
            step=5,
        )

        # Calcul de la moyenne sur 3 semaines glissantes par [Jour_Semaine, Période]
        # On regroupe d'abord par (Jour de la semaine, Période, Date exacte)
        moyennes_journalieres = (
            df_filtre.groupby(["Date_Jour", "Jour_Semaine", "Période"])[col_y]
            .mean()
            .reset_index()
            .sort_values("Date_Jour")
        )

        # Calcul de la moyenne glissante sur les 3 occurrences précédentes du même (Jour_Semaine, Période)
        moyennes_journalieres["Moyenne_3_Semaines_Precedentes"] = (
            moyennes_journalieres.groupby(["Jour_Semaine", "Période"])[col_y]
            .transform(lambda x: x.shift(1).rolling(window=3, min_periods=1).mean())
        )

        # Fusion des références dans le dataframe d'origine
        df_filtre = df_filtre.merge(
            moyennes_journalieres[["Date_Jour", "Période", "Moyenne_3_Semaines_Precedentes"]],
            on=["Date_Jour", "Période"],
            how="left"
        )

        # Si pas assez d'historique (ex: les premières semaines), on se rabat sur la moyenne générale
        df_filtre["Moyenne_Reference"] = df_filtre["Moyenne_3_Semaines_Precedentes"].fillna(
            df_filtre.groupby(["Jour_Semaine", "Période"])[col_y].transform("mean")
        )

        # Calcul de la limite haute
        df_filtre["Limite_Haute"] = df_filtre["Moyenne_Reference"] * (1 + seuil_pct / 100)
        df_filtre["Est_Depassement"] = df_filtre[col_y] > df_filtre["Limite_Haute"]

        # Synthèse des événements de dépassement
        depassements_synthese = (
            df_filtre[df_filtre["Est_Depassement"]]
            .groupby(["Date_Jour", "Jour_Semaine", "Période"])
            .agg(
                Valeur_Max=(col_y, "max"),
                Moyenne_3_Sém_Prec=("Moyenne_Reference", "first"),
                Nb_Points_Anormaux=(col_y, "count"),
            )
            .reset_index()
        )

        # Affichage des métriques
        st.metric(
            "🔴 Jours / Périodes avec dépassement",
            f"{len(depassements_synthese)} événement(s)",
        )

        # Tableau des dépassements
        if not depassements_synthese.empty:
            st.warning(
                f"Événements ayant dépassé de plus de +{seuil_pct}% la moyenne des 3 semaines précédentes (pour le même jour et la même période) :"
            )
            st.dataframe(
                depassements_synthese.rename(
                    columns={
                        "Date_Jour": "Date",
                        "Jour_Semaine": "Jour",
                        "Période": "Période concernée",
                        "Valeur_Max": "Puissance Max Atteinte",
                        "Moyenne_3_Sém_Prec": "Moyenne 3 Semaines Précédentes",
                        "Nb_Points_Anormaux": "Nombre de relevés en dépassement",
                    }
                ).style.format(
                    {
                        "Puissance Max Atteinte": "{:.2f}",
                        "Moyenne 3 Semaines Précédentes": "{:.2f}",
                    }
                )
            )
        else:
            st.success("Aucun dépassement détecté par rapport à la moyenne des 3 semaines précédentes.")