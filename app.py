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

    # Nettoyage des dates valides
    df = df.dropna(subset=[col_x])

    # -------------------------------------------------------------
    # FILTRE PAR PÉRIODE & SAISON (BARRE LATÉRALE)
    # -------------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.header("📅 Filtre Temporel & Saisons")

    date_min = df[col_x].min().date()
    date_max = df[col_x].max().date()

    # Raccourci par saison
    saison = st.sidebar.radio(
        "Sélection rapide :",
        ["Toutes les données", "❄️ Hiver", "☀️ Été", "🍂 Mi-saison", "✏️ Personnalisé"],
        index=0,
    )

    # Logique d'application des dates
    if saison == "❄️ Hiver":
        # Décembre, Janvier, Février, Mars
        df_filtre = df[df[col_x].dt.month.isin([12, 1, 2, 3])]
    elif saison == "☀️ Été":
        # Juin, Juillet, Août
        df_filtre = df[df[col_x].dt.month.isin([6, 7, 8])]
    elif saison == "🍂 Mi-saison":
        # Avril, Mai, Septembre, Octobre, Novembre
        df_filtre = df[df[col_x].dt.month.isin([4, 5, 9, 10, 11])]
    elif saison == "✏️ Personnalisé":
        # Sélecteur de dates libres
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
            ]
        else:
            df_filtre = df.copy()
    else:
        df_filtre = df.copy()

    # Vérification qu'il reste des données
    if df_filtre.empty:
        st.warning(
            "Aucune donnée disponible pour la période ou la saison sélectionnée."
        )
    else:
        # Affichage de la plage sélectionnée
        st.info(
            f"📍 **Analyse du {df_filtre[col_x].min().strftime('%d/%m/%Y')} au {df_filtre[col_x].max().strftime('%d/%m/%Y')}** ({len(df_filtre)} points)"
        )

        # Onglets d'analyse
        tab1, tab2 = st.tabs(
            ["📊 Graphique temporel", "🌙 Analyse Jour / Nuit & Anomalies"]
        )

        # ONGLET 1 : Graphique temporel filtré
        with tab1:
            st.subheader("Courbe de charge temporelle (Période sélectionnée)")
            st.line_chart(df_filtre, x=col_x, y=col_y)

        # ONGLET 2 : Moyennes & Anomalies calculées uniquement sur la sélection !
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
                    "Fin de journée (Heure)",
                    min_value=0,
                    max_value=23,
                    value=22,
                )

            # Calculs sur le DataFrame FILTRÉ
            heures = df_filtre[col_x].dt.hour
            est_jour = (heures >= heure_debut_jour) & (heures < heure_fin_jour)
            df_filtre["Période"] = "🌙 Nuit"
            df_filtre.loc[est_jour, "Période"] = "☀️ Jour"

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

            # Calcul des moyennes uniquement sur la saison/période choisie
            moyennes = df_filtre.groupby(["Jour_Semaine", "Période"])[
                col_y
            ].transform("mean")
            df_filtre["Moyenne_Reference"] = moyennes

            tableau_moyennes = (
                df_filtre.groupby(["Jour_Semaine", "Période"])[col_y]
                .mean()
                .unstack("Période")
            )

            st.bar_chart(tableau_moyennes)
            st.dataframe(tableau_moyennes.style.format("{:.2f}"))

            st.markdown("---")

            # --- SECTION ANOMALIES SUR LA PÉRIODE ---
            st.subheader("2. Dépassements par rapport à la moyenne de cette période")

            seuil_pct = st.slider(
                "Seuil d'écart par rapport à la moyenne sélectionnée (%)",
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

            depassements = df_filtre[
                df_filtre[col_y] > df_filtre["Limite_Haute"]
            ].copy()
            sous_consommations = df_filtre[
                df_filtre[col_y] < df_filtre["Limite_Basse"]
            ].copy()

            col_m1, col_m2 = st.columns(2)
            col_m1.metric(
                "🔴 Dépassements sur la période", f"{len(depassements)} pts"
            )
            col_m2.metric(
                "🔵 Creux sur la période", f"{len(sous_consommations)} pts"
            )

            subtab_haut, subtab_bas = st.tabs(
                ["🔴 Dépassements (Plus élevé)", "🔵 Creux (Plus bas)"]
            )

            with subtab_haut:
                if not depassements.empty:
                    st.warning(
                        f"Dépassements de plus de +{seuil_pct}% par rapport à la moyenne de la saison/période choisie :"
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
                                "Moyenne_Reference": "Moyenne de la Période",
                            }
                        )
                    )
                else:
                    st.info("Aucun dépassement anormal sur cette période.")

            with subtab_bas:
                if not sous_consommations.empty:
                    st.info(
                        f"Consommations inférieures de plus de -{seuil_pct}% à la moyenne de la période :"
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
                                "Moyenne_Reference": "Moyenne de la Période",
                            }
                        )
                    )
                else:
                    st.info("Aucune sous-consommation anormale sur cette période.")