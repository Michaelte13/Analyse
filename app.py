import numpy as np
import pandas as pd
import streamlit as st

# ... (début du code inchangé jusqu'à l'onglet 2) ...

with tab2:
    st.subheader(
        "1. Moyennes dynamiques & Détection par rapport aux 3 semaines précédentes (S-1 à S-3)"
    )

    col_h1, col_h2 = st.columns(2)
    heure_debut_jour = col_h1.number_input(
        "Début de journée (Heure)", min_value=0, max_value=23, value=6
    )
    heure_fin_jour = col_h2.number_input(
        "Fin de journée (Heure)", min_value=0, max_value=23, value=22
    )

    # Qualification Jour / Nuit
    df_filtre = df_filtre.sort_values(col_x).reset_index(drop=True)
    heures = df_filtre[col_x].dt.hour
    est_jour = (heures >= heure_debut_jour) & (heures < heure_fin_jour)
    df_filtre["Période"] = np.where(est_jour, "☀️ Jour", "🌙 Nuit")
    df_filtre["Date_Jour"] = df_filtre[col_x].dt.date

    jours_fr = np.array(
        [
            "1. Lundi",
            "2. Mardi",
            "3. Mercredi",
            "4. Jeudi",
            "5. Vendredi",
            "6. Samedi",
            "7. Dimanche",
        ]
    )
    df_filtre["Jour_Semaine"] = jours_fr[df_filtre[col_x].dt.dayofweek.values]
    df_filtre["Tranche_Horaire"] = df_filtre[col_x].dt.strftime("%H:%M")

    # ------------------------------------------------------------------
    # CALCUL DE LA MOYENNE GLISSANTE SUR LES 3 SEMAINES PRÉCÉDENTES (21 jours)
    # ------------------------------------------------------------------
    # On pivote les données pour avoir les tranches horaires en colonnes et les dates en lignes
    # afin de faire un calcul de moyenne sur 21 jours par créneau horaire exact.

    # 1. Calcul de la moyenne par tranche horaire et par jour exact de la semaine
    # Pour calculer sur 21 jours glissants par type de jour (ex: les 3 derniers Lundis)
    # On regroupe par Jour de la semaine et Tranche horaire avec rolling sur 3 occurrences
    df_filtre["Moyenne_3_Semaines"] = (
        df_filtre.groupby(["Jour_Semaine", "Tranche_Horaire"])[col_y]
        .transform(lambda x: x.shift(1).rolling(window=3, min_periods=1).mean())
    )

    # Fallback : Si les 3 semaines précédentes ne sont pas encore disponibles (début d'historique)
    moyenne_globale = df_filtre.groupby(["Jour_Semaine", "Tranche_Horaire"])[col_y].transform("mean")
    df_filtre["Moyenne_3_Semaines"] = df_filtre["Moyenne_3_Semaines"].fillna(moyenne_globale)

    # Affichage d'un aperçu
    st.info("💡 **Référence de comparaison :** Moyenne calculée sur les **3 mêmes jours/heures des 3 semaines précédentes**.")

    st.markdown("---")

    # --- 2. DÉTECTION D'ANOMALIES SOUTENUES ---
    st.subheader("2. Paramètres des alertes d'anomalies")

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        seuil_pct = st.slider(
            "Seuil d'écart / 3 semaines précédentes (%)",
            min_value=5,
            max_value=100,
            value=20,
            step=5,
        )

    with col_s2:
        duree_min_h = st.select_slider(
            "⏱️ Durée minimale continue de l'anomalie :",
            options=[0.25, 0.5, 1.0, 2.0, 3.0, 4.0],
            value=1.0,
            format_func=lambda x: (
                f"{int(x*60)} min" if x < 1 else f"{int(x)} heure(s)"
            ),
        )

    # Détection du pas de temps
    deltas = df_filtre[col_x].diff().dt.total_seconds().dropna() / 60.0
    pas_temps_min = deltas.median() if not deltas.empty else 60.0
    nb_points_min = max(1, int(round((duree_min_h * 60) / pas_temps_min)))

    st.caption(
        f"💡 *Pas de mesure détecté : **{pas_temps_min:.0f} min**. Une anomalie nécessite au moins **{nb_points_min} relevé(s) consécutif(s)**.*"
    )

    # Calcul des limites dynamiques (basées sur les 3 semaines précédentes)
    facteur = seuil_pct / 100.0
    df_filtre["Limite_Haute"] = df_filtre["Moyenne_3_Semaines"] * (1 + facteur)
    df_filtre["Limite_Basse"] = df_filtre["Moyenne_3_Semaines"] * (1 - facteur)

    # Identification des anomalies
    df_filtre["Is_High"] = (
        df_filtre[col_y] > df_filtre["Limite_Haute"]
    ).astype(int)
    df_filtre["Is_Low"] = (
        df_filtre[col_y] < df_filtre["Limite_Basse"]
    ).astype(int)

    # Fenêtre glissante pour vérifier si l'anomalie dure le temps requis
    df_filtre["Est_Depassement_Soutenu"] = (
        df_filtre["Is_High"]
        .rolling(window=nb_points_min, min_periods=nb_points_min)
        .sum()
        == nb_points_min
    )
    df_filtre["Est_Creux_Soutenu"] = (
        df_filtre["Is_Low"]
        .rolling(window=nb_points_min, min_periods=nb_points_min)
        .sum()
        == nb_points_min
    )

    # Propagation pour capturer la totalité du bloc d'anomalie
    if nb_points_min > 1:
        dep_mask = (
            df_filtre["Est_Depassement_Soutenu"][::-1]
            .rolling(window=nb_points_min, min_periods=1)
            .max()[::-1]
            .astype(bool)
        )
        creux_mask = (
            df_filtre["Est_Creux_Soutenu"][::-1]
            .rolling(window=nb_points_min, min_periods=1)
            .max()[::-1]
            .astype(bool)
        )
    else:
        dep_mask = df_filtre["Est_Depassement_Soutenu"]
        creux_mask = df_filtre["Est_Creux_Soutenu"]

    # Agrégation de synthèse
    depassements_synthese = (
        df_filtre[dep_mask]
        .groupby(["Date_Jour", "Jour_Semaine", "Période"])
        .agg(
            Valeur_Max=(col_y, "max"),
            Moyenne_Attendue_3S=("Moyenne_3_Semaines", "mean"),
            Nb_Points_Anormaux=(col_y, "count"),
        )
        .reset_index()
    )

    creux_synthese = (
        df_filtre[creux_mask]
        .groupby(["Date_Jour", "Jour_Semaine", "Période"])
        .agg(
            Valeur_Min=(col_y, "min"),
            Moyenne_Attendue_3S=("Moyenne_3_Semaines", "mean"),
            Nb_Points_Anormaux=(col_y, "count"),
        )
        .reset_index()
    )

    if not depassements_synthese.empty:
        depassements_synthese["Duree_Totale_h"] = (
            depassements_synthese["Nb_Points_Anormaux"] * pas_temps_min / 60.0
        )
    if not creux_synthese.empty:
        creux_synthese["Duree_Totale_h"] = (
            creux_synthese["Nb_Points_Anormaux"] * pas_temps_min / 60.0
        )

    # Affichage des alertes
    col_m1, col_m2 = st.columns(2)
    col_m1.metric(
        "🔴 Alertes de Dépassement",
        f"{len(depassements_synthese)} événement(s)",
    )
    col_m2.metric(
        "🔵 Alertes de Sous-consommation",
        f"{len(creux_synthese)} événement(s)",
    )

    subtab_haut, subtab_bas = st.tabs(
        ["🔴 Dépassements / 3 Semaines", "🔵 Sous-consommations / 3 Semaines"]
    )

    with subtab_haut:
        if not depassements_synthese.empty:
            st.warning(
                f"Événements ayant dépassé de +{seuil_pct}% la moyenne des 3 semaines précédentes pendant au moins {duree_min_h}h :"
            )
            st.dataframe(
                depassements_synthese.rename(
                    columns={
                        "Date_Jour": "Date",
                        "Jour_Semaine": "Jour",
                        "Valeur_Max": "Puissance Max Atteinte",
                        "Moyenne_Attendue_3S": "Moyenne Atten. (3S préc.)",
                        "Nb_Points_Anormaux": "Nb Relevés Anormaux",
                        "Duree_Totale_h": "Durée Cumulée (h)",
                    }
                ).style.format(
                    {
                        "Puissance Max Atteinte": "{:.2f}",
                        "Moyenne Atten. (3S préc.)": "{:.2f}",
                        "Durée Cumulée (h)": "{:.1f}",
                    }
                )
            )
        else:
            st.info("Aucun dépassement significatif par rapport aux 3 semaines précédentes.")

    with subtab_bas:
        if not creux_synthese.empty:
            st.info(
                f"Événements inférieurs de -{seuil_pct}% à la moyenne des 3 semaines précédentes pendant au moins {duree_min_h}h :"
            )
            st.dataframe(
                creux_synthese.rename(
                    columns={
                        "Date_Jour": "Date",
                        "Jour_Semaine": "Jour",
                        "Valeur_Min": "Puissance Min Atteinte",
                        "Moyenne_Attendue_3S": "Moyenne Atten. (3S préc.)",
                        "Nb_Points_Anormaux": "Nb Relevés Anormaux",
                        "Duree_Totale_h": "Durée Cumulée (h)",
                    }
                ).style.format(
                    {
                        "Puissance Min Atteinte": "{:.2f}",
                        "Moyenne Atten. (3S préc.)": "{:.2f}",
                        "Durée Cumulée (h)": "{:.1f}",
                    }
                )
            )
        else:
            st.info("Aucune sous-consommation significative par rapport aux 3 semaines précédentes.")