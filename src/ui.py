"""UI-komponentit ja toistuvat Streamlit-palikat."""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from .io import get_team_name, get_competition_name, get_season_name
from .model import (
    calculate_summary_stats, calculate_best_worst, calculate_form,
    calculate_opponent_stats, calculate_cumulative_points
)


def render_sidebar_filters(
    data: Dict[str, pd.DataFrame]
) -> Tuple[Optional[List[int]], Optional[int], Optional[int], Optional[str]]:
    """
    Renderöi sidebar-suodattimet.
    
    Args:
        data: Sanakirja kaikista sheeteistä
        
    Returns:
        Tuple (season_ids, team_id, opponent_id, home_away)
    """
    st.sidebar.header("Suodattimet")
    
    # Kausi-suodatin
    if "Seasons" in data and not data["Seasons"].empty:
        seasons_df = data["Seasons"]
        if "season_id" in seasons_df.columns:
            # Luo kausinimet
            season_options = {}
            for _, row in seasons_df.iterrows():
                season_id = row["season_id"]
                season_name = get_season_name(season_id, data)
                season_options[season_name] = season_id
            
            # Järjestä kausi nimen mukaan (uusin ensin) - oletetaan että suurempi vuosi = uudempi
            if "start_year" in seasons_df.columns:
                seasons_df = seasons_df.sort_values("start_year", ascending=False)
                season_options_sorted = {}
                for _, row in seasons_df.iterrows():
                    season_id = row["season_id"]
                    season_name = get_season_name(season_id, data)
                    season_options_sorted[season_name] = season_id
                season_options = season_options_sorted
            
            # Ei oletusvalintaa
            selected_season_names = st.sidebar.multiselect(
                "Kausi",
                options=list(season_options.keys()),
                default=[],
                key="season_filter"
            )
            season_ids = [season_options[name] for name in selected_season_names if name in season_options]
        else:
            season_ids = None
            st.sidebar.warning("Kausidata puuttuu")
    else:
        season_ids = None
        st.sidebar.warning("Kausidata puuttuu")
    
    # Joukkue on aina Mailajoket
    if "Teams" in data and not data["Teams"].empty:
        teams_df = data["Teams"]
        if "team_id" in teams_df.columns and "team_name" in teams_df.columns:
            mailajoket = teams_df[teams_df["team_name"] == "Mailajoket"]
            if not mailajoket.empty:
                team_id = int(mailajoket.iloc[0]["team_id"])
                st.sidebar.info(f"Joukkue: **Mailajoket**")
            else:
                team_id = None
                st.sidebar.warning("Mailajoket-joukkuetta ei löytynyt")
        else:
            team_id = None
            st.sidebar.warning("Joukkuedata puuttuu")
    else:
        team_id = None
        st.sidebar.warning("Joukkuedata puuttuu")
    
    # Vastustaja-suodatin (valinnainen)
    opponent_id = None
    if team_id is not None and "Matches" in data and not data["Matches"].empty:
        matches_df = data["Matches"]
        # Hae kaikki vastustajat valitulle joukkueelle
        if "home_team_id" in matches_df.columns and "away_team_id" in matches_df.columns:
            opponents = set()
            for _, row in matches_df.iterrows():
                home_id = row.get("home_team_id")
                away_id = row.get("away_team_id")
                if pd.notna(home_id) and pd.notna(away_id):
                    if home_id == team_id:
                        opponents.add(away_id)
                    elif away_id == team_id:
                        opponents.add(home_id)
            
            if opponents:
                opponent_options = {"Kaikki": None}
                for opp_id in sorted(opponents):
                    opp_name = get_team_name(opp_id, data)
                    opponent_options[opp_name] = opp_id
                
                selected_opponent = st.sidebar.selectbox(
                    "Vastustaja",
                    options=list(opponent_options.keys()),
                    index=0,
                    key="opponent_filter"
                )
                opponent_id = opponent_options.get(selected_opponent)
    
    # Koti/Vieras-suodatin
    home_away = st.sidebar.selectbox(
        "Koti/Vieras",
        options=["All", "Koti", "Vieras"],
        index=0,
        key="home_away_filter"
    )
    
    # Muunna "Koti" -> "Home", "Vieras" -> "Away"
    if home_away == "Koti":
        home_away = "Home"
    elif home_away == "Vieras":
        home_away = "Away"
    
    return season_ids, team_id, opponent_id, home_away


def render_summary_tab(
    matches_df: pd.DataFrame,
    data: Dict[str, pd.DataFrame],
    team_id: int
) -> None:
    """
    Renderöi yhteenveto-tabin.
    
    Args:
        matches_df: Suodatettu ja rikastettu ottelut DataFrame
        data: Sanakirja kaikista sheeteistä
        team_id: Valitun joukkueen ID
    """
    st.header("Yhteenveto")
    
    if matches_df.empty:
        st.info("Ei otteluita valituilla suodattimilla.")
        return
    
    # Laske perusmetriikat
    stats = calculate_summary_stats(matches_df)
    
    # Laske prosenttiosuudet
    gp = stats["GP"]
    win_pct = (stats["W"] / gp * 100) if gp > 0 else 0
    draw_pct = (stats["D"] / gp * 100) if gp > 0 else 0
    loss_pct = (stats["L"] / gp * 100) if gp > 0 else 0
    
    # Näytä perusmetriikat vaakariveillä
    # Rivi 1: Ottelut ja tulokset
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ottelut (GP)", int(stats["GP"]))
    with col2:
        st.metric(
            "Voitot (W)", 
            int(stats["W"]),
            delta=f"{win_pct:.1f}%"
        )
    with col3:
        st.metric(
            "Tasurit (D)", 
            int(stats["D"]),
            delta=f"{draw_pct:.1f}%"
        )
    with col4:
        st.metric(
            "Tappiot (L)", 
            int(stats["L"]),
            delta=f"{loss_pct:.1f}%"
        )
    
    # Rivi 2: Maalit ja pisteet
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Tehdyt (GF)", 
            int(stats["GF"]),
            delta=f"{stats['GF_per_game']:.2f} /ottelu"
        )
    with col2:
        st.metric(
            "Päästetyt (GA)", 
            int(stats["GA"]),
            delta=f"{stats['GA_per_game']:.2f} /ottelu"
        )
    with col3:
        st.metric("Maaliero (GD)", int(stats["GD"]))
    with col4:
        st.metric(
            "Pisteet", 
            int(stats["points"]),
            delta=f"{stats['PPG']:.2f} /ottelu"
        )
    
    # Paras voitto ja rumin tappio
    best_win, worst_loss = calculate_best_worst(matches_df, data, team_id)
    
    col3_1, col3_2 = st.columns(2)
    with col3_1:
        if best_win:
            st.subheader("Paras voitto")
            st.write(f"**{best_win.get('opponent', 'Tuntematon')}**")
            st.write(f"{best_win.get('goals_for', 0)} - {best_win.get('goals_against', 0)}")
            if best_win.get('date'):
                st.write(f"Päivä: {best_win['date'].strftime('%Y-%m-%d') if hasattr(best_win['date'], 'strftime') else best_win['date']}")
        else:
            st.subheader("Paras voitto")
            st.write("Ei voittoja")
    
    with col3_2:
        if worst_loss:
            st.subheader("Rumin tappio")
            st.write(f"**{worst_loss.get('opponent', 'Tuntematon')}**")
            st.write(f"{worst_loss.get('goals_for', 0)} - {worst_loss.get('goals_against', 0)}")
            if worst_loss.get('date'):
                st.write(f"Päivä: {worst_loss['date'].strftime('%Y-%m-%d') if hasattr(worst_loss['date'], 'strftime') else worst_loss['date']}")
        else:
            st.subheader("Rumin tappio")
            st.write("Ei tappioita")
    
    st.divider()
    
    
    # Vastustajat
    st.subheader("Vastustajat")
    opponent_stats = calculate_opponent_stats(matches_df, data, team_id)
    
    if not opponent_stats.empty:
        # Muuta sarakkeiden nimet ryhdikkääseen muotoon
        display_opponent = opponent_stats.copy()
        display_opponent.columns = [
            "Vastustaja",
            "Ottelut",
            "Voitot",
            "Tasurit",
            "Tappiot",
            "Voittoprosentti (%)"
        ]
        st.dataframe(
            display_opponent,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Ei vastustajatilastoja saatavilla.")
    
    st.divider()
    
    # Trendi: kumulatiiviset pisteet
    st.subheader("Kumulatiiviset pisteet ajan yli")
    cumulative = calculate_cumulative_points(matches_df)
    
    if not cumulative.empty:
        fig = px.line(
            cumulative,
            x="date",
            y="cumulative_points",
            title="Pisteiden kehitys ajan yli",
            labels={"date": "Päivämäärä", "cumulative_points": "Kumulatiiviset pisteet"},
            markers=True
        )
        fig.update_traces(line_width=2, marker_size=6)
        fig.update_layout(
            hovermode='x unified',
            xaxis_title="Päivämäärä",
            yaxis_title="Kumulatiiviset pisteet",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True, key="summary_cumulative_points")
    
    st.divider()
    
    # Kumulatiiviset voitot, tappiot ja tasapelit ajan yli
    st.subheader("Kumulatiiviset voitot, tappiot ja tasapelit ajan yli")
    if not matches_df.empty and "outcome" in matches_df.columns and "date" in matches_df.columns:
        # Järjestä päivämäärän mukaan
        matches_sorted = matches_df.sort_values("date").copy()
        
        # Laske kumulatiiviset määrät
        matches_sorted["cumulative_wins"] = (matches_sorted["outcome"] == "W").cumsum()
        matches_sorted["cumulative_losses"] = (matches_sorted["outcome"] == "L").cumsum()
        matches_sorted["cumulative_draws"] = (matches_sorted["outcome"] == "D").cumsum()
        
        # Luo kuvaaja
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=matches_sorted["date"],
            y=matches_sorted["cumulative_wins"],
            mode='lines+markers',
            name='Voitot',
            line=dict(color='#2ecc71', width=3),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=matches_sorted["date"],
            y=matches_sorted["cumulative_losses"],
            mode='lines+markers',
            name='Tappiot',
            line=dict(color='#e74c3c', width=3),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=matches_sorted["date"],
            y=matches_sorted["cumulative_draws"],
            mode='lines+markers',
            name='Tasapelit',
            line=dict(color='#f39c12', width=3),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title="Kumulatiiviset voitot, tappiot ja tasapelit ajan yli",
            xaxis_title="Päivämäärä",
            yaxis_title="Kumulatiivinen määrä",
            hovermode='x unified',
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True, key="summary_cumulative_wdl")
    else:
        st.info("Ei trendidataa saatavilla.")


def render_matches_tab(
    matches_df: pd.DataFrame,
    data: Dict[str, pd.DataFrame],
    team_id: Optional[int],
    team_perspective: bool = True
) -> None:
    """
    Renderöi ottelut-tabin.
    
    Args:
        matches_df: Suodatettu ja rikastettu ottelut DataFrame
        data: Sanakirja kaikista sheeteistä
        team_id: Valitun joukkueen ID
        team_perspective: Näytäkö joukkueen näkökulmasta vai raaka koti-vieras
    """
    st.header("Ottelut")
    
    if matches_df.empty:
        st.info("Ei otteluita valituilla suodattimilla.")
        return
    
    # Yhteenveto yläpuolella
    stats = calculate_summary_stats(matches_df)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("W-D-L", f"{int(stats['W'])}-{int(stats['D'])}-{int(stats['L'])}")
    with col2:
        st.metric("GF-GA", f"{int(stats['GF'])}-{int(stats['GA'])}")
    with col3:
        st.metric("Pisteet", int(stats["points"]))
    with col4:
        st.metric("PPG", stats["PPG"])
    
    st.divider()
    
    # Toggle: joukkueen näkökulma vs raaka
    if team_id is not None:
        team_perspective = st.toggle(
            "Valitun joukkueen näkökulma",
            value=team_perspective,
            key="team_perspective_toggle"
        )
    
    # Järjestä uusimmasta vanhimpaan (päivämäärän mukaan)
    if "date" in matches_df.columns:
        matches_df = matches_df.sort_values("date", ascending=False)
    
    # Valmistele näytettävä taulukko
    display_df = matches_df.copy()
    
    if team_perspective and team_id is not None:
        # Näytä joukkueen näkökulmasta
        columns_to_show = ["date", "opponent_id", "outcome", "goals_for", "goals_against", "goal_diff", "points_from_match"]
        
        # Lisää vastustajan nimi
        def get_opponent_name(row):
            home_id = row.get("home_team_id")
            away_id = row.get("away_team_id")
            if pd.notna(home_id) and pd.notna(away_id):
                if home_id == team_id:
                    return row.get("away_team_name", "Tuntematon")
                elif away_id == team_id:
                    return row.get("home_team_name", "Tuntematon")
            return "Tuntematon"
        
        display_df["Vastustaja"] = display_df.apply(get_opponent_name, axis=1)
        display_df["Päivä"] = display_df["date"]
        display_df["Tulos"] = display_df.apply(
            lambda row: f"{row.get('goals_for', 0)}-{row.get('goals_against', 0)}",
            axis=1
        )
        display_df["Tulos"] = display_df["Tulos"].replace("0-0", "N/A")
        display_df["Outcome"] = display_df["outcome"]
        display_df["Pisteet"] = display_df["points_from_match"]
        
        display_columns = ["Päivä", "Vastustaja", "Tulos", "Outcome", "Pisteet"]
    else:
        # Näytä raaka koti-vieras
        display_df["Päivä"] = display_df["date"]
        display_df["Koti"] = display_df.get("home_team_name", "Tuntematon")
        display_df["Vieras"] = display_df.get("away_team_name", "Tuntematon")
        display_df["Tulos"] = display_df.apply(
            lambda row: f"{row.get('home_goals', 0)}-{row.get('away_goals', 0)}",
            axis=1
        )
        
        display_columns = ["Päivä", "Koti", "Vieras", "Tulos"]
    
    # Näytä taulukko
    st.dataframe(
        display_df[display_columns],
        use_container_width=True,
        hide_index=True
    )
    
    # CSV-lataus
    csv = display_df[display_columns].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Lataa CSV",
        data=csv,
        file_name="ottelut.csv",
        mime="text/csv",
        key="download_matches_csv"
    )
    
    st.divider()
    
    # Kausittainen heatmap/värijono
    st.subheader("Kausittainen ottelukalenteri")
    
    if not matches_df.empty and "date" in matches_df.columns and "outcome" in matches_df.columns:
        # Ryhmittele kausittain
        matches_with_season = matches_df.copy()
        
        # Lisää kausinimet
        if "season_id" in matches_with_season.columns and "Seasons" in data and not data["Seasons"].empty:
            seasons_df = data["Seasons"][["season_id", "start_year", "end_year"]]
            matches_with_season = matches_with_season.merge(seasons_df, on="season_id", how="left")
            matches_with_season["kausi"] = matches_with_season.apply(
                lambda row: f"{int(row['start_year'])}-{int(row['end_year'])}" 
                if pd.notna(row.get('start_year')) and pd.notna(row.get('end_year'))
                else f"Kausi {row['season_id']}",
                axis=1
            )
        else:
            matches_with_season["kausi"] = matches_with_season.get("season_id", "Tuntematon")
        
        # Järjestä kausien mukaan uusimmasta vanhimpaan
        if "start_year" in matches_with_season.columns:
            matches_with_season = matches_with_season.sort_values("start_year", ascending=False)
        
        # Järjestä kausit uusimmasta vanhimpaan ennen groupby:tä
        # Luo järjestysarvo kausille
        if "start_year" in matches_with_season.columns:
            season_order = matches_with_season.groupby("kausi")["start_year"].first().sort_values(ascending=False).index.tolist()
        else:
            season_order = sorted(matches_with_season["kausi"].unique(), reverse=True)
        
        # Ryhmittele kausittain ja järjestä uusimmasta vanhimpaan
        for kausi in season_order:
            if kausi not in matches_with_season["kausi"].values:
                continue
            season_matches = matches_with_season[matches_with_season["kausi"] == kausi]
            st.write(f"**{kausi}**")
            
            # Järjestä päivämäärän mukaan
            season_matches = season_matches.sort_values("date")
            
            # Luo värikoodatut neliöt
            result_boxes = []
            for _, row in season_matches.iterrows():
                outcome = row.get("outcome")
                
                # Hae vastustaja oikein
                if team_perspective and team_id is not None:
                    home_id = row.get("home_team_id")
                    away_id = row.get("away_team_id")
                    if pd.notna(home_id) and pd.notna(away_id):
                        if home_id == team_id:
                            # Vastustaja on vierasjoukkue
                            if "away_team_name" in row and pd.notna(row.get("away_team_name")):
                                opponent = row.get("away_team_name")
                            else:
                                opponent = get_team_name(away_id, data)
                        elif away_id == team_id:
                            # Vastustaja on kotijoukkue
                            if "home_team_name" in row and pd.notna(row.get("home_team_name")):
                                opponent = row.get("home_team_name")
                            else:
                                opponent = get_team_name(home_id, data)
                        else:
                            opponent = "Tuntematon"
                    else:
                        opponent = "Tuntematon"
                else:
                    home_name = row.get("home_team_name", "Tuntematon")
                    away_name = row.get("away_team_name", "Tuntematon")
                    if home_name == "Tuntematon" and "home_team_id" in row:
                        home_name = get_team_name(row.get("home_team_id"), data)
                    if away_name == "Tuntematon" and "away_team_id" in row:
                        away_name = get_team_name(row.get("away_team_id"), data)
                    opponent = f"{home_name} vs {away_name}"
                
                # Määritä väri ja teksti
                if outcome == "W":
                    color = "#2ecc71"  # Vihreä
                    text = "V"
                elif outcome == "L":
                    color = "#e74c3c"  # Punainen
                    text = "H"
                elif outcome == "D":
                    color = "#f39c12"  # Keltainen/Oranssi
                    text = "T"
                else:
                    color = "#95a5a6"  # Harmaa
                    text = "-"
                
                # Muotoile päivämäärä
                date = row.get("date")
                if hasattr(date, 'strftime'):
                    date_str = date.strftime('%d.%m')
                else:
                    date_str = str(date)[:5] if len(str(date)) > 5 else str(date)
                
                result_boxes.append({
                    "pvm": date_str,
                    "vastustaja": opponent,
                    "tulos": text
                })
            
            # Näytä vaakasuuntaisesti pieniä neliöitä
            if result_boxes:
                # Luo HTML merkkijono
                html_boxes = []
                for box in result_boxes:
                    # Määritä väri tuloksen perusteella
                    if box["tulos"] == "V":
                        color = "#2ecc71"  # Vihreä
                    elif box["tulos"] == "H":
                        color = "#e74c3c"  # Punainen
                    elif box["tulos"] == "T":
                        color = "#f39c12"  # Keltainen/Oranssi
                    else:
                        color = "#95a5a6"  # Harmaa
                    
                    tooltip = f"{box['pvm']} - {box['vastustaja']}"
                    html_boxes.append(
                        f'<span style="background-color: {color}; color: white; width: 40px; height: 40px; '
                        f'border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; '
                        f'font-weight: bold; font-size: 16px; margin-right: 8px; margin-bottom: 8px; '
                        f'min-width: 40px; min-height: 40px;" title="{tooltip}">{box["tulos"]}</span>'
                    )
                
                html_content = '<div style="display: flex; flex-wrap: wrap; margin-bottom: 20px;">' + ''.join(html_boxes) + '</div>'
                st.markdown(html_content, unsafe_allow_html=True)
                
                # Näytä myös taulukko tarkempaa tietoa varten
                calendar_df = pd.DataFrame(result_boxes)
                # Varmista että DataFrame:ssä on vain 3 saraketta
                calendar_df = calendar_df[["pvm", "vastustaja", "tulos"]].copy()
                calendar_df.columns = ["Päivä", "Vastustaja", "Tulos"]
                st.dataframe(calendar_df, use_container_width=True, hide_index=True)
            
            st.divider()


def render_standings_tab(
    data: Dict[str, pd.DataFrame],
    season_ids: Optional[List[int]],
    team_id: Optional[int]
) -> None:
    """
    Renderöi sarjataulukot-tabin.
    
    Args:
        data: Sanakirja kaikista sheeteistä
        season_ids: Lista kausi-ID:itä
        team_id: Valitun joukkueen ID
    """
    st.header("Sarjataulukot")
    
    if "Standings" not in data or data["Standings"].empty:
        st.info("Ei sarjataulukkoja saatavilla.")
        return
    
    standings_df = data["Standings"].copy()
    
    # Suodata kausi
    if season_ids is not None and len(season_ids) > 0:
        if "season_id" in standings_df.columns:
            standings_df = standings_df[standings_df["season_id"].isin(season_ids)]
    
    if standings_df.empty:
        st.info("Ei sarjataulukkoja valituilla suodattimilla.")
        return
    
    # Ryhmittele kilpailu/vaihe/ryhmä -mukaan
    if "competition_id" in standings_df.columns:
        # Liitä kilpailutiedot aina
        if "Competitions" in data and not data["Competitions"].empty:
            comps_df = data["Competitions"]
            merge_cols = ["competition_id", "competition_name"]
            if "stage" in comps_df.columns:
                merge_cols.append("stage")
            
            standings_df = standings_df.merge(
                comps_df[merge_cols],
                on="competition_id",
                how="left"
            )
            standings_df["competition_name"] = standings_df["competition_name"].fillna("Tuntematon")
            if "stage" in standings_df.columns:
                standings_df["stage"] = standings_df["stage"].fillna("Tuntematon")
            else:
                standings_df["stage"] = "Tuntematon"
        else:
            # Jos Competitions puuttuu, luo placeholderit
            standings_df["competition_name"] = "Tuntematon"
            standings_df["stage"] = "Tuntematon"
        
        # Lisää joukkueiden nimet
        if "team_id" in standings_df.columns:
            standings_df["team_name"] = standings_df["team_id"].apply(
                lambda x: get_team_name(x, data) if pd.notna(x) else "Tuntematon"
            )
        
        # Ryhmittele kausi ja kilpailu
        # Lisää kausinimet
        if "Seasons" in data and not data["Seasons"].empty:
            seasons_df = data["Seasons"][["season_id", "start_year", "end_year"]]
            standings_df = standings_df.merge(seasons_df, on="season_id", how="left")
            standings_df["season_display"] = standings_df.apply(
                lambda row: f"{int(row['start_year'])}-{int(row['end_year'])}" 
                if pd.notna(row.get('start_year')) and pd.notna(row.get('end_year'))
                else f"Kausi {row['season_id']}",
                axis=1
            )
        else:
            standings_df["season_display"] = standings_df["season_id"].apply(
                lambda x: f"Kausi {x}"
            )
        
        # Järjestä uusimmasta vanhimpaan (start_year mukaan)
        if "start_year" in standings_df.columns:
            standings_df = standings_df.sort_values("start_year", ascending=False)
        
        # Varmista että competition_name on olemassa ennen groupby:tä
        if "competition_name" not in standings_df.columns:
            standings_df["competition_name"] = "Tuntematon"
        if "stage" not in standings_df.columns:
            standings_df["stage"] = "Tuntematon"
        
        # Ryhmittele kausi ja kilpailu
        for (season_disp, comp_name, comp_stage), group in standings_df.groupby(
            ["season_display", "competition_name", "stage"]
        ):
            st.subheader(f"{season_disp} - {comp_name} {comp_stage if pd.notna(comp_stage) else ''}")
            
            # Järjestä sijoitusten mukaan
            if "rank" in group.columns:
                group = group.sort_values("rank")
            
            # Valmistele näytettävä taulukko
            display_cols = []
            if "rank" in group.columns:
                display_cols.append("rank")
            if "team_name" in group.columns:
                display_cols.append("team_name")
            # Lisää muut sarakkeet jos saatavilla
            for col in group.columns:
                if col not in ["competition_id", "season_id", "team_id", "standing_id", "raw_row"]:
                    if col not in display_cols:
                        display_cols.append(col)
            
            if not display_cols:
                st.warning(f"Ei näytettäviä sarakkeita kilpailulle {comp_name}")
                continue
            
            display_df = group[display_cols].copy()
            display_df.columns = [col.replace("_", " ").title() for col in display_df.columns]
            
            # Korosta valittu joukkue
            if team_id is not None and "team_id" in group.columns:
                # Resetoi indeksit molemmissa jotta ne täsmäävät
                group_reset = group.reset_index(drop=True)
                display_df_reset = display_df.reset_index(drop=True)
                
                # Lisää team_id display_df:ään väliaikaisesti
                display_df_with_team = display_df_reset.copy()
                display_df_with_team["_team_id_temp"] = group_reset["team_id"].values
                
                def highlight_team(row):
                    # Tarkista team_id apusarakkeesta
                    team_id_val = row.get("_team_id_temp")
                    if pd.notna(team_id_val) and team_id_val == team_id:
                        # Palauta tyylit kaikille sarakkeille paitsi apusarakkeelle
                        num_cols = len([c for c in display_df_with_team.columns if c != "_team_id_temp"])
                        return ['background-color: yellow'] * num_cols + ['']
                    return [''] * len(row)
                
                # Poista apusarake ennen näyttämistä
                display_df_final = display_df_with_team.drop(columns=["_team_id_temp"])
                
                try:
                    st.dataframe(
                        display_df_final.style.apply(highlight_team, axis=1),
                        use_container_width=True,
                        hide_index=True
                    )
                except Exception as e:
                    # Jos styler epäonnistuu, näytä ilman korostusta
                    st.dataframe(
                        display_df_final,
                        use_container_width=True,
                        hide_index=True
                    )
            else:
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )
            
            st.divider()
    else:
        st.warning("Standings-taulukossa ei ole competition_id-saraketta.")


def render_players_tab(
    data: Dict[str, pd.DataFrame],
    season_ids: Optional[List[int]],
    team_id: Optional[int]
) -> None:
    """
    Renderöi pelaajat-tabin.
    
    Args:
        data: Sanakirja kaikista sheeteistä
        season_ids: Lista kausi-ID:itä
        team_id: Valitun joukkueen ID
    """
    st.header("Pelaajat")
    st.info("💡 Voit muuttaa suodattimia vasemmasta laidasta.")
    
    if "PlayerSeasonStats" not in data or data["PlayerSeasonStats"].empty:
        st.info("Ei pelaajatilastoja saatavilla.")
        return
    
    stats_df = data["PlayerSeasonStats"].copy()
    
    # Suodata kausi
    if season_ids is not None and len(season_ids) > 0:
        if "season_id" in stats_df.columns:
            stats_df = stats_df[stats_df["season_id"].isin(season_ids)]
    
    # Suodata joukkue
    if team_id is not None:
        if "team_id" in stats_df.columns:
            stats_df = stats_df[stats_df["team_id"] == team_id]
    
    if stats_df.empty:
        st.info("Ei pelaajatilastoja valituilla suodattimilla.")
        return
    
    # Liitä pelaajien nimet
    if "Players" in data and not data["Players"].empty:
        players_df = data["Players"]
        if "player_id" in stats_df.columns and "player_id" in players_df.columns:
            stats_df = stats_df.merge(
                players_df[["player_id", "full_name"]],
                on="player_id",
                how="left"
            )
            stats_df["player_name"] = stats_df["full_name"].fillna("Tuntematon")
    
    # LEADERBOARD
    # Määritä kausiteksti
    if season_ids is None or len(season_ids) == 0:
        season_text = "All Time"
    else:
        if "Seasons" in data and not data["Seasons"].empty:
            seasons_df = data["Seasons"]
            selected_seasons = seasons_df[seasons_df["season_id"].isin(season_ids)]
            if "start_year" in selected_seasons.columns and "end_year" in selected_seasons.columns:
                years = sorted(selected_seasons["start_year"].dropna().unique())
                if len(years) == 1:
                    season_text = f"{int(years[0])}"
                elif len(years) == 2:
                    season_text = f"{int(years[0])}-{int(years[-1])}"
                else:
                    season_text = f"{int(years[0])}-{int(years[-1])}"
            else:
                season_text = f"{len(season_ids)} kautta"
        else:
            season_text = f"{len(season_ids)} kautta"
    
    st.subheader(f"Leaderboard - {season_text}")
    
    # Laske yhteistilastot pelaajittain
    if "player_id" in stats_df.columns:
        # Laske yhteensä ja kausien määrä
        player_totals = stats_df.groupby("player_id").agg({
            "goals": "sum" if "goals" in stats_df.columns else "count",
            "assists": "sum" if "assists" in stats_df.columns else "count",
            "points": "sum" if "points" in stats_df.columns else "count",
            "season_id": "nunique"  # Kausien määrä (Seasons-sarake)
        }).reset_index()
        
        # Nimeä season_id -> seasons
        player_totals = player_totals.rename(columns={"season_id": "seasons"})
        
        # Laske keskiarvot per kausi
        player_totals["pistekeskiarvo"] = (
            player_totals["points"] / player_totals["seasons"]
            if "points" in player_totals.columns and player_totals["seasons"].sum() > 0
            else 0
        )
        player_totals["maalikeskiarvo"] = (
            player_totals["goals"] / player_totals["seasons"]
            if "goals" in player_totals.columns and player_totals["seasons"].sum() > 0
            else 0
        )
        player_totals["syöttökeskiarvo"] = (
            player_totals["assists"] / player_totals["seasons"]
            if "assists" in player_totals.columns and player_totals["seasons"].sum() > 0
            else 0
        )
        
        # Liitä pelaajien nimet
        if "Players" in data and not data["Players"].empty:
            players_df = data["Players"]
            player_totals = player_totals.merge(
                players_df[["player_id", "full_name"]],
                on="player_id",
                how="left"
            )
            player_totals["player_name"] = player_totals["full_name"].fillna("Tuntematon")
        
        # Laske pisteet jos ei ole
        if "points" not in player_totals.columns and "goals" in player_totals.columns and "assists" in player_totals.columns:
            player_totals["points"] = player_totals["goals"] + player_totals["assists"]
            # Laske keskiarvot uudelleen
            player_totals["pistekeskiarvo"] = (
                player_totals["points"] / player_totals["season_id"]
                if player_totals["season_id"].sum() > 0 else 0
            )
        
        # Järjestä pisteiden mukaan
        player_totals = player_totals.sort_values("points" if "points" in player_totals.columns else "goals", ascending=False)
        
        # Näytä top 10
        top_players = player_totals.head(10)
        
        if not top_players.empty:
            # Leaderboard-metriikat
            cols = st.columns(min(5, len(top_players)))
            for idx, (_, player) in enumerate(top_players.iterrows()):
                with cols[idx % len(cols)]:
                    st.metric(
                        f"{idx + 1}. {player.get('player_name', 'Tuntematon')}",
                        f"{int(player.get('points', 0))} p",
                        delta=f"{int(player.get('goals', 0))} m + {int(player.get('assists', 0))} s"
                    )
            
            st.divider()
            
            # Leaderboard-taulukko numeroidulla
            leaderboard_cols = ["player_name"]
            if "seasons" in top_players.columns:
                leaderboard_cols.append("seasons")
            if "goals" in top_players.columns:
                leaderboard_cols.append("goals")
            if "assists" in top_players.columns:
                leaderboard_cols.append("assists")
            if "points" in top_players.columns:
                leaderboard_cols.append("points")
            if "pistekeskiarvo" in top_players.columns:
                leaderboard_cols.append("pistekeskiarvo")
            if "maalikeskiarvo" in top_players.columns:
                leaderboard_cols.append("maalikeskiarvo")
            if "syöttökeskiarvo" in top_players.columns:
                leaderboard_cols.append("syöttökeskiarvo")
            
            leaderboard_df = top_players[leaderboard_cols].copy()
            
            # Muuta sarakkeiden nimet suomeksi
            column_mapping = {
                "player_name": "Pelaaja",
                "seasons": "Kaudet",
                "goals": "Maalit",
                "assists": "Syötöt",
                "points": "Pisteet",
                "pistekeskiarvo": "Pistekeskiarvo",
                "maalikeskiarvo": "Maalikeskiarvo",
                "syöttökeskiarvo": "Syöttökeskiarvo"
            }
            leaderboard_df = leaderboard_df.rename(columns=column_mapping)
            
            # Lisää numerointi
            leaderboard_df.insert(0, "#", range(1, len(leaderboard_df) + 1))
            
            # Pyöristä keskiarvot
            for col in leaderboard_df.columns:
                if "keskiarvo" in col.lower():
                    leaderboard_df[col] = leaderboard_df[col].round(2)
            
            st.dataframe(leaderboard_df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # NIMIHAKU JA TÄYDELLINEN TAUULUKKO
    search_name = st.text_input("Hae pelaajaa", key="player_search")
    if search_name:
        if "player_name" in stats_df.columns:
            stats_df = stats_df[
                stats_df["player_name"].str.contains(search_name, case=False, na=False)
            ]
    
    # Laske pisteet jos saatavilla (ennen keskiarvojen laskentaa)
    if "goals" in stats_df.columns and "assists" in stats_df.columns:
        if "pisteet" not in stats_df.columns:
            stats_df["pisteet"] = stats_df["goals"] + stats_df["assists"]
    elif "points" in stats_df.columns:
        stats_df["pisteet"] = stats_df["points"]
    
    # Lisää kausinimet
    if "season_id" in stats_df.columns:
        stats_df["kausi"] = stats_df["season_id"].apply(
            lambda x: get_season_name(x, data)
        )
    
    # Laske keskiarvot per kausi pelaajittain
    if "player_id" in stats_df.columns:
        # Laske kausien määrä per pelaaja
        player_season_counts = stats_df.groupby("player_id")["season_id"].nunique().reset_index()
        player_season_counts.columns = ["player_id", "kausia"]
        stats_df = stats_df.merge(player_season_counts, on="player_id", how="left")
        
        # Laske keskiarvot
        stats_df["pistekeskiarvo"] = (
            stats_df["pisteet"] / stats_df["kausia"]
            if "pisteet" in stats_df.columns else 0
        )
        stats_df["maalikeskiarvo"] = (
            stats_df["goals"] / stats_df["kausia"]
            if "goals" in stats_df.columns else 0
        )
        stats_df["syöttökeskiarvo"] = (
            stats_df["assists"] / stats_df["kausia"]
            if "assists" in stats_df.columns else 0
        )
    
    # Valmistele näytettävä taulukko
    display_cols = ["player_name"] if "player_name" in stats_df.columns else []
    if "kausi" in stats_df.columns:
        display_cols.insert(1, "kausi")
    if "goals" in stats_df.columns:
        display_cols.append("goals")
    if "assists" in stats_df.columns:
        display_cols.append("assists")
    
    # Pisteet on jo laskettu yllä
    if "pisteet" in stats_df.columns:
        display_cols.append("pisteet")
    
    # Lisää keskiarvot
    if "pistekeskiarvo" in stats_df.columns:
        display_cols.append("pistekeskiarvo")
    if "maalikeskiarvo" in stats_df.columns:
        display_cols.append("maalikeskiarvo")
    if "syöttökeskiarvo" in stats_df.columns:
        display_cols.append("syöttökeskiarvo")
    
    # Lisää ottelumäärä jos saatavilla
    if "games_played" in stats_df.columns or "gp" in stats_df.columns:
        gp_col = "games_played" if "games_played" in stats_df.columns else "gp"
        display_cols.append(gp_col)
    
    display_df = stats_df[display_cols].copy()
    
    # Muuta sarakkeiden nimet suomeksi
    column_mapping = {
        "player_name": "Pelaaja",
        "kausi": "Kausi",
        "goals": "Maalit",
        "assists": "Syötöt",
        "pisteet": "Pisteet",
        "pistekeskiarvo": "Pistekeskiarvo",
        "maalikeskiarvo": "Maalikeskiarvo",
        "syöttökeskiarvo": "Syöttökeskiarvo",
        "games_played": "Ottelut",
        "gp": "Ottelut"
    }
    display_df = display_df.rename(columns=column_mapping)
    
    # Pyöristä keskiarvot
    for col in display_df.columns:
        if "keskiarvo" in col.lower():
            display_df[col] = display_df[col].round(2)
    
    # Järjestä pisteiden mukaan
    if "Pisteet" in display_df.columns:
        display_df = display_df.sort_values("Pisteet", ascending=False)
    
    st.subheader("Kaikki pelaajat")
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # HIGHLIGHTS PER PELAAJA
    st.divider()
    st.subheader("Highlights per pelaaja")
    
    if "player_id" in stats_df.columns and "player_name" in stats_df.columns:
        # Valitse pelaaja
        player_options = sorted(stats_df["player_name"].unique().tolist())
        if player_options:
            selected_player_highlights = st.selectbox(
                "Valitse pelaaja highlightsille",
                options=player_options,
                key="selected_player_highlights"
            )
            
            if selected_player_highlights:
                player_id_hl = stats_df[stats_df["player_name"] == selected_player_highlights]["player_id"].iloc[0]
                player_data = stats_df[stats_df["player_id"] == player_id_hl].copy()
                
                if not player_data.empty:
                    # Paras kausi
                    if "pisteet" in player_data.columns:
                        best_season = player_data.loc[player_data["pisteet"].idxmax()]
                        worst_season = player_data.loc[player_data["pisteet"].idxmin()]
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(
                                "Paras kausi",
                                f"{best_season.get('kausi', 'N/A')}",
                                delta=f"{int(best_season.get('pisteet', 0))} pisteetä"
                            )
                        with col2:
                            st.metric(
                                "Heikoin kausi",
                                f"{worst_season.get('kausi', 'N/A')}",
                                delta=f"{int(worst_season.get('pisteet', 0))} pistettä"
                            )
                        with col3:
                            avg_points = player_data["pisteet"].mean() if "pisteet" in player_data.columns else 0
                            st.metric(
                                "Keskiarvo pisteitä",
                                f"{avg_points:.1f}"
                            )
                    
                    # Yhteensä
                    col4, col5, col6 = st.columns(3)
                    with col4:
                        total_goals = player_data["goals"].sum() if "goals" in player_data.columns else 0
                        st.metric("Maalit yhteensä", int(total_goals))
                    with col5:
                        total_assists = player_data["assists"].sum() if "assists" in player_data.columns else 0
                        st.metric("Syötöt yhteensä", int(total_assists))
                    with col6:
                        total_points = player_data["pisteet"].sum() if "pisteet" in player_data.columns else 0
                        st.metric("Pisteet yhteensä", int(total_points))
                    
                    # Keskiarvot
                    col7, col8, col9 = st.columns(3)
                    with col7:
                        avg_goals = player_data["goals"].mean() if "goals" in player_data.columns else 0
                        st.metric("Keskiarvo maaleja/kausi", f"{avg_goals:.1f}")
                    with col8:
                        avg_assists = player_data["assists"].mean() if "assists" in player_data.columns else 0
                        st.metric("Keskiarvo syöttöjä/kausi", f"{avg_assists:.1f}")
                    with col9:
                        total_seasons = len(player_data)
                        st.metric("Kausia yhteensä", total_seasons)
                    
                    # Näytä kuvaaja highlights-pelaajalle
                    if "season_id" in player_data.columns:
                        # Luo kausinimet
                        player_data["season_name"] = player_data["season_id"].apply(
                            lambda x: get_season_name(x, data)
                        )
                        # Järjestä start_year:n mukaan jos saatavilla
                        if "Seasons" in data and not data["Seasons"].empty and "start_year" in data["Seasons"].columns:
                            seasons_df = data["Seasons"][["season_id", "start_year"]]
                            player_data = player_data.merge(seasons_df, on="season_id", how="left")
                            player_data = player_data.sort_values("start_year")
                        else:
                            player_data = player_data.sort_values("season_id")
                        
                        # Interaktiivinen kuvaaja
                        chart_data = player_data[["season_name"]].copy()
                        if "goals" in player_data.columns:
                            chart_data["Maalit"] = player_data["goals"]
                        if "assists" in player_data.columns:
                            chart_data["Syötöt"] = player_data["assists"]
                        if "pisteet" in player_data.columns:
                            chart_data["Pisteet"] = player_data["pisteet"]
                        elif "goals" in player_data.columns and "assists" in player_data.columns:
                            chart_data["Pisteet"] = player_data["goals"] + player_data["assists"]
                        
                        fig = go.Figure()
                        
                        if "Maalit" in chart_data.columns:
                            fig.add_trace(go.Bar(
                                x=chart_data["season_name"],
                                y=chart_data["Maalit"],
                                name="Maalit",
                                marker_color='#1f77b4'
                            ))
                        if "Syötöt" in chart_data.columns:
                            fig.add_trace(go.Bar(
                                x=chart_data["season_name"],
                                y=chart_data["Syötöt"],
                                name="Syötöt",
                                marker_color='#ff7f0e'
                            ))
                        if "Pisteet" in chart_data.columns:
                            fig.add_trace(go.Scatter(
                                x=chart_data["season_name"],
                                y=chart_data["Pisteet"],
                                name="Pisteet",
                                mode='lines+markers',
                                line=dict(color='#2ca02c', width=3),
                                marker=dict(size=10)
                            ))
                        
                        fig.update_layout(
                            title=f"{selected_player_highlights} - Kausittaiset tilastot",
                            xaxis_title="Kausi",
                            yaxis_title="Määrä",
                            barmode='group',
                            height=500,
                            hovermode='x unified'
                        )
                        st.plotly_chart(fig, use_container_width=True, key="player_highlights_chart")
    


def render_rosters_tab(
    data: Dict[str, pd.DataFrame],
    season_ids: Optional[List[int]],
    team_id: Optional[int]
) -> None:
    """
    Renderöi rosterit-tabin.
    
    Args:
        data: Sanakirja kaikista sheeteistä
        season_ids: Lista kausi-ID:itä
        team_id: Valitun joukkueen ID
    """
    st.header("Rosterit - Mailajokeissa pelanneet")
    
    if "Rosters" not in data or data["Rosters"].empty:
        st.info("Ei roostereita saatavilla.")
        return
    
    rosters_df = data["Rosters"].copy()
    
    # Tarkista onko suodattimia käytössä
    has_filters = False
    original_rosters_df = data["Rosters"].copy()
    
    # Suodata kausi
    if season_ids is not None and len(season_ids) > 0:
        has_filters = True
        if "season_id" in rosters_df.columns:
            rosters_df = rosters_df[rosters_df["season_id"].isin(season_ids)]
    
    # Suodata joukkue
    if team_id is not None:
        has_filters = True
        if "team_id" in rosters_df.columns:
            rosters_df = rosters_df[rosters_df["team_id"] == team_id]
    
    if rosters_df.empty:
        st.info("Ei roostereita valituilla suodattimilla.")
        return
    
    # KORTIT ALUSSA: Pelaajat yhteensä, Kenttäpelaajat, MaaliVahdit
    if "role" in rosters_df.columns:
        unique_players = rosters_df["player_id"].nunique() if "player_id" in rosters_df.columns else 0
        field_players = rosters_df[rosters_df["role"].isin(["Puolustaja", "Hyökkääjä", "Kenttäpelaaja"])]["player_id"].nunique() if "player_id" in rosters_df.columns else 0
        goalies = rosters_df[rosters_df["role"] == "Maalivahti"]["player_id"].nunique() if "player_id" in rosters_df.columns else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Pelaajat yhteensä", unique_players)
        with col2:
            st.metric("Kenttäpelaajat", field_players)
        with col3:
            st.metric("MaaliVahdit", goalies)
        
        st.divider()
    
    # Liitä pelaajien nimet
    if "Players" in data and not data["Players"].empty:
        players_df = data["Players"]
        if "player_id" in rosters_df.columns and "player_id" in players_df.columns:
            rosters_df = rosters_df.merge(
                players_df[["player_id", "full_name"]],
                on="player_id",
                how="left"
            )
            rosters_df["player_name"] = rosters_df["full_name"].fillna("Tuntematon")
    
    # Kausittainen pelaajien määrä ja keskiarvo - PIILOTA JOS SUODATTIMIA KÄYTETÄÄN
    if not has_filters:
        st.subheader("Kausittainen pelaajien määrä rosterissa")
        
        # Laske rosterin koko eri kausina (käytä alkuperäistä dataa)
        roster_sizes = {}
        if "season_id" in original_rosters_df.columns:
            for season_id, group in original_rosters_df.groupby("season_id"):
                season_name = get_season_name(season_id, data)
                roster_sizes[season_name] = len(group)
        
        if roster_sizes:
            roster_df = pd.DataFrame(list(roster_sizes.items()), columns=["Kausi", "Pelaajia"])
            roster_df = roster_df.sort_values("Kausi")
            
            # Laske keskiarvo
            avg_players = roster_df["Pelaajia"].mean()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Keskiarvo pelaajia/kausi", f"{avg_players:.1f}")
            with col2:
                st.metric("Suurin rosteri", int(roster_df["Pelaajia"].max()))
            
            # Kuvaaja
            fig = px.line(
                roster_df,
                x="Kausi",
                y="Pelaajia",
                title="Pelaajien määrä kausittain",
                labels={"Kausi": "Kausi", "Pelaajia": "Pelaajia"},
                markers=True
            )
            fig.add_hline(y=avg_players, line_dash="dash", line_color="gray", 
                         annotation_text=f"Keskiarvo: {avg_players:.1f}")
            fig.update_traces(line_width=3, marker_size=8)
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True, key="roster_size_chart")
        
        st.divider()
    
    # LEADERBOARD: Pelaajat kausien mukaan (lasketaan PlayerSeasonStats:sta) - YLIMMÄISEKSI
    st.subheader("Leaderboard - Pelaajat kausien mukaan")
    
    # Laske pelaajatason kautta PlayerSeasonStats:sta
    if "PlayerSeasonStats" in data and not data["PlayerSeasonStats"].empty:
        player_stats_df = data["PlayerSeasonStats"].copy()
        # Suodata joukkue ja kausi
        if team_id is not None and "team_id" in player_stats_df.columns:
            player_stats_df = player_stats_df[player_stats_df["team_id"] == team_id]
        if season_ids is not None and len(season_ids) > 0 and "season_id" in player_stats_df.columns:
            player_stats_df = player_stats_df[player_stats_df["season_id"].isin(season_ids)]
        
        if "player_id" in player_stats_df.columns and "season_id" in player_stats_df.columns:
            # Ryhmittele pelaajittain ja laske uniikit kausit
            player_seasons = player_stats_df.groupby("player_id").agg({
                "season_id": "nunique",  # Uniikit kausit
            }).reset_index()
            player_seasons.columns = ["player_id", "kausia"]
            
            # Liitä pelaajien nimet
            if "Players" in data and not data["Players"].empty:
                players_df = data["Players"]
                player_seasons = player_seasons.merge(
                    players_df[["player_id", "full_name"]],
                    on="player_id",
                    how="left"
                )
                player_seasons["player_name"] = player_seasons["full_name"].fillna("Tuntematon")
            
            player_seasons = player_seasons.sort_values("kausia", ascending=False)
            
            top_players = player_seasons.head(10)
            
            if not top_players.empty:
                # Leaderboard-kuvaaja (ilman tekstibokseja)
                fig = px.bar(
                    top_players.head(10),
                    x="player_name",
                    y="kausia",
                    title="Top 10 pelaajaa - Kausien määrä",
                    labels={"player_name": "Pelaaja", "kausia": "Kausia"},
                    text="kausia"
                )
                fig.update_layout(height=600, xaxis_tickangle=-45)
                fig.update_traces(textposition='outside')
                st.plotly_chart(fig, use_container_width=True, key="roster_leaderboard_chart")
    
    st.divider()
    
    # RYHMITTELY: Maalivahdit, Kenttäpelaajat, Toimihenkilöt
    if "role" in rosters_df.columns:
        # Määrittele roolien kategoriat
        def categorize_role(role):
            if pd.isna(role):
                return "Muut"
            role_str = str(role).lower()
            if "maalivahti" in role_str or "mv" in role_str:
                return "Maalivahdit"
            elif "toimihenkilö" in role_str or "staff" in role_str or "is_staff" in role_str:
                return "Toimihenkilöt"
            else:
                return "Kenttäpelaajat"
        
        rosters_df["role_category"] = rosters_df["role"].apply(categorize_role)
        
        # Tarkista myös is_staff-sarake
        if "is_staff" in rosters_df.columns:
            rosters_df.loc[rosters_df["is_staff"] == True, "role_category"] = "Toimihenkilöt"
        
        role_categories = ["Maalivahdit", "Kenttäpelaajat", "Toimihenkilöt"]
        
        for category in role_categories:
            category_players = rosters_df[rosters_df["role_category"] == category].copy()
            
            if not category_players.empty:
                # Laske uniikit pelaajat tässä kategoriassa
                unique_in_category = category_players["player_id"].nunique() if "player_id" in category_players.columns else len(category_players)
                st.subheader(f"{category} ({unique_in_category})")
                
                # Valmistele näytettävä taulukko
                display_cols = ["player_name"]
                if "jersey_number" in category_players.columns or "number" in category_players.columns:
                    num_col = "jersey_number" if "jersey_number" in category_players.columns else "number"
                    display_cols.append(num_col)
                if "role" in category_players.columns:
                    display_cols.append("role")
                
                display_df = category_players[display_cols].copy()
                display_df.columns = [col.replace("_", " ").title() for col in display_df.columns]
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                st.divider()
    else:
        st.warning("Rosters-taulukossa ei ole role-saraketta.")
        
        # Näytä kaikki pelaajat ilman rooliryhmitystä
        display_cols = ["player_name"]
        if "jersey_number" in rosters_df.columns or "number" in rosters_df.columns:
            num_col = "jersey_number" if "jersey_number" in rosters_df.columns else "number"
            display_cols.append(num_col)
        
        display_df = rosters_df[display_cols].copy()
        display_df.columns = [col.replace("_", " ").title() for col in display_df.columns]
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

