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

    # Sélection automatique de la 1ère colonne (Date) et de la 2ème colonne (Puissance)
    col_x = donnees.columns[0]
    col_y = donnees.columns[1]

    # Conversion en Datetime
    df = donnees.copy()
    df[col_x] = pd.to_datetime(df[col_x], errors="coerce")
    df = df.dropna(subset=[col_x]).sort_values(col_x)

    # -------------------------------------------------------------
    # FILTRE PAR MOIS / SAISON / PERIODE (MENU DÉROULANT)
    # -------------------------------------------------------------
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
    # AFFICHAGE DES RÉSULTATS DANS DES ONGLETS
    # -------------------------------------------------------------
    if df_filtre.empty:
        st.warning("Aucune donnée disponible pour la période sélectionnée.")
    else:
        st.info(
            f"📍 **Analyse du {df_filtre[col_x].min().strftime('%d/%m/%Y')} au {df_filtre[col_x].max().strftime('%d/%m/%Y')}**"
        )

        # Création des 3 onglets
        tab1, tab2, tab3 = st.tabs(
            [
                "📊 Moyennes Globales",
                "🔴 Dépassements de Moyenne",
                "⚡ Dépassements de Puissance Souscrite",
            ]
        )

        # -------------------------------------------------------------
        # PRÉPARATION COMMUNE DES DONNÉES (JOUR / NUIT & JOUR SEMAINE)
        # -------------------------------------------------------------
        st.sidebar.markdown("---")
        st.sidebar.header("🕒 Plages Horaires Jour/Nuit")
        heure_debut_jour = st.sidebar.number_input(
            "Début de journée (Heure)", min_value=0, max_value=23, value=6
        )
        heure_fin_jour = st.sidebar.number_input(
            "Fin de journée (Heure)", min_value=0, max_value=23, value=22
        )

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

        # -------------------------------------------------------------
        # ONGLET 1 : MOYENNES GLOBALES
        # -------------------------------------------------------------
        with tab1:
            st.subheader("Moyennes globales par jour de la semaine (Jour vs Nuit)")

            tableau_moyennes = (
                df_filtre.groupby(["Jour_Semaine", "Période"])[col_y]
                .mean()
                .unstack("Période")
            )
            st.bar_chart(tableau_moyennes)
            st.dataframe(tableau_moyennes.style.format("{:.2f}"))

        # -------------------------------------------------------------
        # ONGLET 2 : DÉTECTION DES DÉPASSEMENTS DE MOYENNE
        # -------------------------------------------------------------
        with tab2:
            st.subheader("Dépassements de la moyenne constatée (vs 3 semaines précédentes)")

            seuil_pct = st.slider(
                "Seuil de dépassement de la moyenne (%)",
                min_value=5,
                max_value=100,
                value=20,
                step=5,
            )

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

            if not depassements_synthese.empty:
                st.metric(
                    "🔴 Périodes (Jour/Nuit) avec dépassement de moyenne",
                    f"{len(depassements_synthese)} événement(s)",
                )
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
                st.success("Pas de dépassement")

        # -------------------------------------------------------------
        # ONGLET 3 : DÉPASSEMENTS DE LA PUISSANCE CONTRACTUELLE
        # -------------------------------------------------------------
        with tab3:
            st.subheader("Analyse du dépassement de la puissance souscrite (Contrat)")

            # Saisie de la valeur du contrat
            valeur_max_absolue = df_filtre[col_y].max()
            puissance_souscrite = st.number_input(
                "Renseigner la Puissance Souscrite / Contrat (kW)",
                min_value=0.0,
                value=float(round(valeur_max_absolue * 0.8, 2)),
                step=10.0,
            )

            # Estimation automatique du pas de temps entre deux points
            if len(df_filtre) > 1:
                pas_de_temps_min = (
                    df_filtre[col_x].diff().median().total_seconds() / 60
                )
                if pd.isna(pas_de_temps_min) or pas_de_temps_min <= 0:
                    pas_de_temps_min = 10
            else:
                pas_de_temps_min = 10

            # Filtrage des dépassements de la puissance contractuelle
            df_depassements_contrat = df_filtre[df_filtre[col_y] > puissance_souscrite].copy()
            nb_occurrences = len(df_depassements_contrat)
            temps_total_minutes = int(nb_occurrences * pas_de_temps_min)

            # Formatage de la durée
            heures_duree = temps_total_minutes // 60
            minutes_duree = temps_total_minutes % 60
            if heures_duree > 0:
                duree_str = f"{heures_duree}h {minutes_duree}min"
            else:
                duree_str = f"{minutes_duree} min"

            # Affichage selon qu'il y ait dépassement ou non
            if not df_depassements_contrat.empty:
                col_v1, col_v2, col_v3, col_v4 = st.columns(4)
                col_v1.metric("⏱️ Temps au-dessus du contrat", duree_str)
                col_v2.metric("📊 Nb de relevés en dépassement", f"{nb_occurrences}")
                col_v3.metric("🔥 Puissance Max Atteinte", f"{valeur_max_absolue:.2f} kW")
                
                ecart_max = valeur_max_absolue - puissance_souscrite
                col_v4.metric("📈 Dépassement Max", f"+{ecart_max:.2f} kW")

                st.markdown("---")

                st.warning(
                    f"⚠️ Le contrat ({puissance_souscrite:.2f} kW) a été dépassé pendant un cumul de **{duree_str}** sur la période sélectionnée."
                )

                df_depassements_contrat["Dépassement (kW)"] = df_depassements_contrat[col_y] - puissance_souscrite
                df_depassements_contrat["Dépassement (%)"] = (df_depassements_contrat["Dépassement (kW)"] / puissance_souscrite) * 100

                df_depassement_detail = df_depassements_contrat[
                    [col_x, "Jour_Semaine", "Période", col_y, "Dépassement (kW)", "Dépassement (%)"]
                ].copy()

                df_depassement_detail[col_x] = df_depassement_detail[col_x].dt.strftime("%d/%m/%Y %H:%M")

                st.dataframe(
                    df_depassement_detail.rename(
                        columns={
                            col_x: "Horodatage",
                            "Jour_Semaine": "Jour",
                            "Période": "Période",
                            col_y: "Puissance Relevée (kW)",
                        }
                    ).style.format(
                        {
                            "Puissance Relevée (kW)": "{:.2f}",
                            "Dépassement (kW)": "+{:.2f}",
                            "Dépassement (%)": "+{:.1f}%",
                        }
                    ),
                    use_container_width=True,
                )
            else:
                st.success("Pas de dépassement")