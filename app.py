"""Mailajoket Tilastoselain - Pääsovellus."""

import streamlit as st
from pathlib import Path
from typing import Dict, Optional

from src.io import load_excel_data, validate_sheet_columns, get_team_aliases_map
from src.model import enrich_matches, parse_match_dates, filter_matches
from src.ui import (
    render_sidebar_filters,
    render_summary_tab,
    render_matches_tab,
    render_standings_tab,
    render_players_tab,
    render_rosters_tab
)


# Sivun konfiguraatio
st.set_page_config(
    page_title="Mailajoket Tilastoselain",
    page_icon="🏒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Excel-tiedoston polku
EXCEL_FILE_PATH = "mailajoket_2014_2026_dataworkbook.xlsx"


def main() -> None:
    """Pääfunktio."""
    st.title("🏒 Mailajoket Tilastoselain")
    st.markdown("Selaa Mailajokkejen tilastoja vuosilta 2014-2025")
    
    # Tarkista että tiedosto on olemassa
    excel_path = Path(EXCEL_FILE_PATH)
    if not excel_path.exists():
        st.error(f"Excel-tiedostoa ei löydy: {EXCEL_FILE_PATH}")
        st.info("Varmista että tiedosto on projektikansiossa.")
        return
    
    # Lataa data
    try:
        data = load_excel_data(str(excel_path))
    except Exception as e:
        st.error(f"Virhe datan lataamisessa: {e}")
        return
    
    # Validoi data
    is_valid, error_msg = validate_sheet_columns(data)
    if not is_valid:
        st.error(error_msg)
        st.warning("Sovellus voi toimia rajoitetusti puuttuvien sarakkeiden kanssa.")
    
    # Renderöi sidebar-suodattimet
    season_ids, team_id, opponent_id, home_away = render_sidebar_filters(data)
    
    # Hae ja suodata ottelut
    if "Matches" in data and not data["Matches"].empty:
        matches_df = data["Matches"].copy()
        
        # Suodata ottelut
        filtered_matches = filter_matches(
            matches_df,
            data,
            season_ids=season_ids,
            team_id=team_id,
            stage=None,
            opponent_id=opponent_id,
            home_away=home_away
        )
        
        # Rikasta ottelut
        enriched_matches = enrich_matches(filtered_matches, data, selected_team_id=team_id)
        
        # Parsii päivämäärät ja järjestä
        enriched_matches = parse_match_dates(enriched_matches)
    else:
        enriched_matches = None
        st.warning("Matches-taulukko puuttuu tai on tyhjä.")
    
    # Logo oikeaan yläkulmaan hehkureunoilla
    import base64
    
    logo_paths = [
        Path("mj logo.jpeg"),
        Path("assets/logo.png"),
        Path("assets/logo.jpg"),
        Path("assets/logo.jpeg")
    ]
    logo_found = False
    logo_path_str = None
    for logo_path in logo_paths:
        if logo_path.exists():
            logo_path_str = str(logo_path)
            logo_found = True
            break
    
    if logo_found:
        # Lue logo ja muunna base64:ksi
        with open(logo_path_str, "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode()
            img_ext = logo_path_str.split('.')[-1].lower()
            mime_type = f"image/{img_ext}" if img_ext in ['png', 'jpg', 'jpeg'] else "image/jpeg"
        
        st.markdown(f"""
        <div style="
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 999;
            opacity: 0.85;
        ">
            <img src="data:{mime_type};base64,{img_data}" 
                 style="
                     width: 100px;
                     height: auto;
                     filter: drop-shadow(0 0 10px rgba(231, 76, 60, 0.5)) 
                             drop-shadow(0 0 20px rgba(231, 76, 60, 0.3))
                             drop-shadow(0 0 30px rgba(231, 76, 60, 0.2));
                     border-radius: 8px;
                 " />
        </div>
        """, unsafe_allow_html=True)
    else:
        # Placeholder logo HTML/CSS
        st.markdown("""
        <div style="
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 999;
            opacity: 0.85;
        ">
            <div style="
                background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
                border: 3px solid #e74c3c;
                border-radius: 8px;
                padding: 10px 15px;
                text-align: center;
                box-shadow: 0 0 10px rgba(231, 76, 60, 0.5),
                           0 0 20px rgba(231, 76, 60, 0.3),
                           0 0 30px rgba(231, 76, 60, 0.2);
                transform: rotate(-2deg);
            ">
                <h1 style="
                    color: #1a237e;
                    font-weight: bold;
                    font-size: 24px;
                    margin: 0;
                    font-family: 'Arial Black', sans-serif;
                    letter-spacing: 2px;
                ">JOKET</h1>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Infopainike (collapsible)
    with st.expander("💡 Voit muuttaa suodattimia vasemmasta laidasta", expanded=False):
        st.write("Käytä vasemman laidan suodattimia rajoittaaksesi näytettävää dataa:")
        st.write("• **Kausi**: Valitse yksi tai useampi kausi")
        st.write("• **Vastustaja**: Suodata ottelut tiettyä vastustajaa vastaan")
        st.write("• **Koti/Vieras**: Näytä vain kotipelit tai vierasottelut")
    
    # Päänäkymän tabit
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Yhteenveto",
        "Ottelut",
        "Sarjataulukot",
        "Pelaajat",
        "Rosterit"
    ])
    
    with tab1:
        if enriched_matches is not None and not enriched_matches.empty and team_id is not None:
            render_summary_tab(enriched_matches, data, team_id)
        else:
            st.info("Valitse joukkue nähdäksesi yhteenvedon.")
    
    with tab2:
        if enriched_matches is not None and not enriched_matches.empty:
            render_matches_tab(enriched_matches, data, team_id, team_perspective=True)
        else:
            st.info("Ei otteluita valituilla suodattimilla.")
    
    with tab3:
        render_standings_tab(data, season_ids, team_id)
    
    with tab4:
        render_players_tab(data, season_ids, team_id)
    
    with tab5:
        render_rosters_tab(data, season_ids, team_id)


if __name__ == "__main__":
    main()

