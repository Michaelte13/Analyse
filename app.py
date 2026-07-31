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

        # Clés temporelles
        df_filtre["Date_Jour"] = df_filtre[col_x].dt.date
        df_filtre["Annee"] = df_filtre[col_x].dt.isocalendar().year
        df_filtre["Semaine"] = df_filtre[col_x].dt.isocalendar().week

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

        # Graphique et Tableau des moyennes globales
        tableau_moyennes = (
            df_filtre.groupby(["Jour_Semaine", "Période"])[col_y]
            .mean()
            .unstack("Période")
        )
        st.bar_chart(tableau_moyennes)
        st.dataframe(tableau_moyennes.style.format("{:.2f}"))

        st.markdown("---")

        # -------------------------------------------------------------
        # 2. DÉTECTION DES DÉPASSEMENTS (RÉFÉRENCE : SEMAINE PRÉCÉDENTE N-1)
        # -------------------------------------------------------------
        st.subheader("2. Dépassements de consommation (Comparaison Jour vs Jour et Nuit vs Nuit N-1)")

        seuil_pct = st.slider(
            "Seuil de dépassement par rapport à la semaine précédente (%)",
            min_value=5,
            max_value=100,
            value=20,
            step=5,
        )

        # Calcul des moyennes hebdomadaires séparées pour chaque [Année, Semaine, Jour, Période (Jour/Nuit)]
        moyennes_hebdo = (
            df_filtre.groupby(["Annee", "Semaine", "Jour_Semaine", "Période"])[col_y]
            .mean()
            .reset_index()
            .rename(columns={col_y: "Moyenne_Semaine"})
        )

        # Calcul de la correspondance vers la semaine N+1
        moyennes_hebdo["Date_Repere"] = pd.to_datetime(
            moyennes_hebdo["Annee"].astype(str) + "-W" + moyennes_hebdo["Semaine"].astype(str) + "-1",
            format="%G-W%V-%u"
        )
        moyennes_hebdo["Date_Semaine_Suivante"] = moyennes_hebdo["Date_Repere"] + pd.Timedelta(weeks=1)
        
        moyennes_hebdo["Annee_Suivante"] = moyennes_hebdo["Date_Semaine_Suivante"].dt.isocalendar().year
        moyennes_hebdo["Semaine_Suivante"] = moyennes_hebdo["Date_Semaine_Suivante"].dt.isocalendar().week

        # Fusion : associe pour la même Période (Jour/Nuit) la moyenne correspondante de la semaine N-1
        df_filtre = df_filtre.merge(
            moyennes_hebdo[["Annee_Suivante", "Semaine_Suivante", "Jour_Semaine", "Période", "Moyenne_Semaine"]],
            left_on=["Annee", "Semaine", "Jour_Semaine", "Période"],
            right_on=["Annee_Suivante", "Semaine_Suivante", "Jour_Semaine", "Période"],
            how="left"
        ).rename(columns={"Moyenne_Semaine": "Moyenne_Semaine_Precedente"})

        # Nettoyage
        df_filtre.drop(columns=["Annee_Suivante", "Semaine_Suivante"], errors="ignore", inplace=True)

        # Repli sur la moyenne globale si la semaine précédente n'existe pas dans le fichier
        df_filtre["Moyenne_Reference"] = df_filtre["Moyenne_Semaine_Precedente"].fillna(
            df_filtre.groupby(["Jour_Semaine", "Période"])[col_y].transform("mean")
        )

        # Limite haute pour le calcul du dépassement
        df_filtre["Limite_Haute"] = df_filtre["Moyenne_Reference"] * (1 + seuil_pct / 100)
        df_filtre["Est_Depassement"] = df_filtre[col_y] > df_filtre["Limite_Haute"]

        # Synthèse groupée par Date, Jour et Période (Jour/Nuit)
        depassements_synthese = (
            df_filtre[df_filtre["Est_Depassement"]]
            .groupby(["Date_Jour", "Jour_Semaine", "Période"])
            .agg(
                Valeur_Max=(col_y, "max"),
                Moyenne_N_1=("Moyenne_Reference", "first"),
                Nb_Points_Anormaux=(col_y, "count"),
            )
            .reset_index()
        )

        # Affichage du nombre de dépassements
        st.metric(
            "🔴 Jours / Périodes avec dépassement",
            f"{len(depassements_synthese)} événement(s)",
        )

        # Tableau final
        if not depassements_synthese.empty:
            st.warning(
                f"Événements ayant dépassé de plus de +{seuil_pct}% la moyenne de la même période (Jour/Nuit) de la semaine précédente (N-1) :"
            )
            st.dataframe(
                depassements_synthese.rename(
                    columns={
                        "Date_Jour": "Date",
                        "Jour_Semaine": "Jour",
                        "Période": "Période concernée",
                        "Valeur_Max": "Puissance Max Atteinte",
                        "Moyenne_N_1": "Moyenne Période Semaine N-1",
                        "Nb_Points_Anormaux": "Nombre de relevés en dépassement",
                    }
                ).style.format(
                    {
                        "Puissance Max Atteinte": "{:.2f}",
                        "Moyenne Période Semaine N-1": "{:.2f}",
                    }
                )
            )
        else:
            st.success("Aucun dépassement détecté par rapport aux périodes (Jour/Nuit) de la semaine N-1.")