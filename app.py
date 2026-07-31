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
    df = df.dropna(subset=[col_x]).sort_values(col_x)

    # -------------------------------------------------------------
    # FILTRE PAR MOIS / SAISON / PERIODE (MENU DÉROULANT)
    # -------------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.header("📅 Filtre Temporel")

    date_min = df[col_x].min().date()
    date_max = df[col_x].max().date()

    options_filtre = [
        "Toutes les données",
        "❄️ Hiver",
        "🌸 Printemps",
        "☀️ Été",
        "🍂 Automne",
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

    if choix_filtre == "Toutes les données":
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

        # Graphique des moyennes
        tableau_moyennes = (
            df_filtre.groupby(["Jour_Semaine", "Période"])[col_y]
            .mean()
            .unstack("Période")
        )
        st.bar_chart(tableau_moyennes)
        st.dataframe(tableau_moyennes.style.format("{:.2f}"))

        st.markdown("---")

        # -------------------------------------------------------------
        # 2. DÉTECTION DES DÉPASSEMENTS (vs 3 SEMAINES PRÉCÉDENTES)
        # -------------------------------------------------------------
        st.subheader("2. Dépassements de la moyenne constatée (vs 3 semaines précédentes)")

        seuil_pct = st.slider(
            "Seuil de dépassement de la moyenne (%)",
            min_value=5,
            max_value=100,
            value=20,
            step=5,
        )

        # Synthèse journalière
        synthese_journaliere = (
            df_filtre.groupby(["Date_Jour", "Jour_Semaine", "Période"])[col_y]
            .mean()
            .reset_index()
            .rename(columns={col_y: "Moyenne_Constatee"})
            .sort_values("Date_Jour")
        )

        synthese_journaliere["Moyenne_3_Semaines_Precedentes"] = (
            synthese_journaliere.groupby(["Jour_Semaine", "Période"])["Moyenne_Constatee"]
            .transform(lambda x: x.shift(1).rolling(window=3, min_periods=1).mean())
        )

        moyenne_globale_creneau = synthese_journaliere.groupby(["Jour_Semaine", "Période"])["Moyenne_Constatee"].transform("mean")
        synthese_journaliere["Moyenne_Reference"] = synthese_journaliere["Moyenne_3_Semaines_Precedentes"].fillna(moyenne_globale_creneau)

        synthese_journaliere["Limite_Haute"] = synthese_journaliere["Moyenne_Reference"] * (1 + seuil_pct / 100)
        synthese_journaliere["Ecart_Pct"] = ((synthese_journaliere["Moyenne_Constatee"] - synthese_journaliere["Moyenne_Reference"]) / synthese_journaliere["Moyenne_Reference"]) * 100

        depassements_synthese = synthese_journaliere[
            synthese_journaliere["Moyenne_Constatee"] > synthese_journaliere["Limite_Haute"]
        ].copy()

        st.metric(
            "🔴 Périodes (Jour/Nuit) avec dépassement de moyenne",
            f"{len(depassements_synthese)} événement(s)",
        )

        if not depassements_synthese.empty:
            st.warning(
                f"Périodes ayant une moyenne de consommation supérieure de plus de +{seuil_pct}% par rapport à la moyenne des 3 semaines précédentes :"
            )
            
            tableau_affichage = depassements_synthese.rename(
                columns={
                    "Date_Jour": "Date",
                    "Jour_Semaine": "Jour",
                    "Période": "Période",
                    "Moyenne_Constatee": "Moyenne du Jour (kW)",
                    "Moyenne_Reference": "Moyenne 3 Semaines Précédentes (kW)",
                    "Ecart_Pct": "Écart (%)",
                }
            )[["Date", "Jour", "Période", "Moyenne du Jour (kW)", "Moyenne 3 Semaines Précédentes (kW)", "Écart (%)"]]

            st.dataframe(
                tableau_affichage.style.format(
                    {
                        "Moyenne du Jour (kW)": "{:.2f}",
                        "Moyenne 3 Semaines Précédentes (kW)": "{:.2f}",
                        "Écart (%)": "+{:.1f}%",
                    }
                )
            )
        else:
            st.success("Aucune période ne dépasse la moyenne des 3 semaines précédentes au seuil sélectionné.")

        st.markdown("---")

        # -------------------------------------------------------------
        # 3. VALEURS MAXIMALES ATTEINTES ET TEMPS PASSÉ
        # -------------------------------------------------------------
        st.subheader("3. Puissances maximales atteintes et temps de fonctionnement")

        # Estimation automatique du pas de temps (en minutes) entre deux relevés
        if len(df_filtre) > 1:
            pas_de_temps_min = (
                df_filtre[col_x].diff().median().total_seconds() / 60
            )
            if pd.isna(pas_de_temps_min) or pas_de_temps_min <= 0:
                pas_de_temps_min = 10  # Valeur par défaut si indéterminée
        else:
            pas_de_temps_min = 10

        # Récupération de la valeur max absolue
        valeur_max_absolue = df_filtre[col_y].max()

        # Groupe par valeur maximale
        df_max = df_filtre[df_filtre[col_y] == valeur_max_absolue]
        nb_occurrences = len(df_max)
        temps_total_minutes = int(nb_occurrences * pas_de_temps_min)

        # Formatage lisible de la durée
        heures_duree = temps_total_minutes // 60
        minutes_duree = temps_total_minutes % 60
        if heures_duree > 0:
            duree_str = f"{heures_duree}h {minutes_duree}min"
        else:
            duree_str = f"{minutes_duree} min"

        # Métriques clés
        col_v1, col_v2, col_v3 = st.columns(3)
        col_v1.metric("🔥 Puissance Max Absolue", f"{valeur_max_absolue:.2f}")
        col_v2.metric("⏱️ Temps total à cette puissance", duree_str)
        col_v3.metric("📊 Nombre d'apparitions (points)", f"{nb_occurrences} relevé(s)")

        # Tableau détaillé des dates où la puissance maximale est atteinte
        st.markdown(f"**Détail des horodatages où la valeur maximale ({valeur_max_absolue:.2f}) a été observée :**")

        df_max_detail = df_max[[col_x, "Jour_Semaine", "Période", col_y]].copy()
        df_max_detail[col_x] = df_max_detail[col_x].dt.strftime("%d/%m/%Y %H:%M")

        st.dataframe(
            df_max_detail.rename(
                columns={
                    col_x: "Horodatage",
                    "Jour_Semaine": "Jour",
                    "Période": "Période",
                    col_y: "Puissance Relevée",
                }
            ).style.format({"Puissance Relevée": "{:.2f}"}),
            use_container_width=True,
        )