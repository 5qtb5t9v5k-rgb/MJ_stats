"""Excel-datan luku ja validointi."""

from typing import Dict, Optional, Set, Tuple
import pandas as pd
import streamlit as st
from pathlib import Path


# Vaaditut sarakkeet kullekin sheetille (päivitetty todellisten sarakkeiden mukaan)
REQUIRED_COLUMNS: Dict[str, Set[str]] = {
    "Seasons": {"season_id", "start_year", "end_year"},
    "Teams": {"team_id", "team_name"},
    "TeamAliases": {"alias_name", "team_id"},  # Voi olla tyhjä
    "Competitions": {"competition_id", "competition_name", "season_id", "stage"},
    "Matches": {"match_id", "season_id", "date", "home_team_id", "away_team_id", 
                "home_goals", "away_goals"},
    "Standings": {"standing_id", "season_id", "competition_id", "team_id", "rank"},
    "Players": {"player_id", "full_name"},
    "Rosters": {"roster_id", "season_id", "team_id", "player_id", "role"},
    "PlayerSeasonStats": {"stat_id", "season_id", "team_id", "player_id", "goals", "assists"},
}


@st.cache_data
def load_excel_data(file_path: str) -> Dict[str, pd.DataFrame]:
    """
    Lataa Excel-työkirjan kaikki välilehdet pandas DataFrameeksi.
    
    Args:
        file_path: Polku Excel-tiedostoon
        
    Returns:
        Sanakirja, jossa avaimena sheetin nimi ja arvona DataFrame
        
    Raises:
        FileNotFoundError: Jos tiedostoa ei löydy
        ValueError: Jos tiedostoa ei voi lukea
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Tiedostoa ei löydy: {file_path}")
    
    try:
        excel_file = pd.ExcelFile(file_path, engine='openpyxl')
        data = {}
        
        for sheet_name in excel_file.sheet_names:
            try:
                df = pd.read_excel(excel_file, sheet_name=sheet_name, engine='openpyxl')
                # Poista tyhjät rivit
                df = df.dropna(how='all')
                data[sheet_name] = df
            except Exception as e:
                st.error(f"Virhe sheetin '{sheet_name}' lukemisessa: {e}")
                data[sheet_name] = pd.DataFrame()
        
        return data
    except Exception as e:
        raise ValueError(f"Excel-tiedoston lukeminen epäonnistui: {e}")


def validate_sheet_columns(data: Dict[str, pd.DataFrame]) -> Tuple[bool, Optional[str]]:
    """
    Tarkistaa että jokaisessa sheetissä on vaaditut sarakkeet.
    
    Args:
        data: Sanakirja sheet-nimistä DataFrameeksi
        
    Returns:
        Tuple (onko_validi, virheilmoitus)
    """
    missing_columns = []
    
    for sheet_name, required_cols in REQUIRED_COLUMNS.items():
        if sheet_name not in data:
            missing_columns.append(f"Sheet '{sheet_name}' puuttuu kokonaan")
            continue
        
        df = data[sheet_name]
        if df.empty:
            continue
        
        missing = required_cols - set(df.columns)
        if missing:
            missing_columns.append(
                f"Sheet '{sheet_name}': puuttuvat sarakkeet {', '.join(sorted(missing))}"
            )
    
    if missing_columns:
        error_msg = "Datan validointi epäonnistui:\n" + "\n".join(f"- {msg}" for msg in missing_columns)
        return False, error_msg
    
    return True, None


def get_team_aliases_map(data: Dict[str, pd.DataFrame]) -> Dict[str, int]:
    """
    Luo mappauksen TeamAliases-taulusta canonical team_id:hen.
    
    Args:
        data: Sanakirja sheet-nimistä DataFrameeksi
        
    Returns:
        Sanakirja, jossa avaimena alias (str) ja arvona team_id (int)
    """
    if "TeamAliases" not in data:
        return {}
    
    aliases_df = data["TeamAliases"]
    if aliases_df.empty:
        return {}
    
    # Tarkista että vaaditut sarakkeet ovat olemassa
    if "alias_name" not in aliases_df.columns or "team_id" not in aliases_df.columns:
        return {}
    
    # Poista NaN-arvot
    aliases_df = aliases_df.dropna(subset=["alias_name", "team_id"])
    
    # Muunna alias stringiksi ja team_id intiksi
    aliases_df["alias_name"] = aliases_df["alias_name"].astype(str).str.strip()
    aliases_df["team_id"] = pd.to_numeric(aliases_df["team_id"], errors='coerce')
    aliases_df = aliases_df.dropna(subset=["team_id"])
    
    # Luo mappaus
    alias_map = {}
    for _, row in aliases_df.iterrows():
        alias = str(row["alias_name"]).strip()
        team_id = int(row["team_id"])
        if alias:
            alias_map[alias.lower()] = team_id
    
    return alias_map


def normalize_team_names(
    data: Dict[str, pd.DataFrame],
    alias_map: Dict[str, int]
) -> Dict[str, pd.DataFrame]:
    """
    Normalisoi joukkueiden nimet TeamAliases-kautta.
    
    Tämä funktio voi olla hyödyllinen, jos tarvitaan normalisointia.
    Tällä hetkellä palautetaan data muuttumattomana.
    
    Args:
        data: Sanakirja sheet-nimistä DataFrameeksi
        alias_map: Mappaus aliaksista team_id:hen
        
    Returns:
        Sama data-sanakirja (tulevaisuudessa voisi normalisoida)
    """
    # Toteutus voidaan laajentaa tarvittaessa
    return data


def get_team_name(team_id: int, data: Dict[str, pd.DataFrame]) -> str:
    """
    Hae joukkueen nimi team_id:llä.
    
    Args:
        team_id: Joukkueen ID
        data: Sanakirja sheet-nimistä DataFrameeksi
        
    Returns:
        Joukkueen nimi tai "Tuntematon" jos ei löydy
    """
    if "Teams" not in data:
        return f"Tuntematon ({team_id})"
    
    teams_df = data["Teams"]
    if teams_df.empty or "team_id" not in teams_df.columns:
        return f"Tuntematon ({team_id})"
    
    match = teams_df[teams_df["team_id"] == team_id]
    if not match.empty and "team_name" in match.columns:
        return str(match.iloc[0]["team_name"])
    
    return f"Tuntematon ({team_id})"


def get_competition_name(competition_id: int, data: Dict[str, pd.DataFrame]) -> str:
    """
    Hae kilpailun nimi competition_id:llä.
    
    Args:
        competition_id: Kilpailun ID
        data: Sanakirja sheet-nimistä DataFrameeksi
        
    Returns:
        Kilpailun nimi tai "Tuntematon" jos ei löydy
    """
    if "Competitions" not in data:
        return "Tuntematon"
    
    comps_df = data["Competitions"]
    if comps_df.empty or "competition_id" not in comps_df.columns:
        return "Tuntematon"
    
    match = comps_df[comps_df["competition_id"] == competition_id]
    if not match.empty and "competition_name" in match.columns:
        return str(match.iloc[0]["competition_name"])
    
    return "Tuntematon"


def get_competition_stage(competition_id: int, data: Dict[str, pd.DataFrame]) -> str:
    """
    Hae kilpailun vaihe competition_id:llä.
    
    Args:
        competition_id: Kilpailun ID
        data: Sanakirja sheet-nimistä DataFrameeksi
        
    Returns:
        Kilpailun vaihe tai "Tuntematon" jos ei löydy
    """
    if "Competitions" not in data:
        return "Tuntematon"
    
    comps_df = data["Competitions"]
    if comps_df.empty or "competition_id" not in comps_df.columns:
        return "Tuntematon"
    
    match = comps_df[comps_df["competition_id"] == competition_id]
    if not match.empty and "stage" in match.columns:
        stage = match.iloc[0]["stage"]
        if pd.notna(stage):
            return str(stage)
    
    return "Tuntematon"


def get_season_name(season_id: int, data: Dict[str, pd.DataFrame]) -> str:
    """
    Hae kausinimi season_id:llä. Luo nimen start_year ja end_year:sta jos tarvitaan.
    
    Args:
        season_id: Kauden ID
        data: Sanakirja sheet-nimistä DataFrameeksi
        
    Returns:
        Kausinimi tai "Tuntematon" jos ei löydy
    """
    if "Seasons" not in data:
        return f"Kausi {season_id}"
    
    seasons_df = data["Seasons"]
    if seasons_df.empty or "season_id" not in seasons_df.columns:
        return f"Kausi {season_id}"
    
    match = seasons_df[seasons_df["season_id"] == season_id]
    if not match.empty:
        # Yritä luoda nimi start_year ja end_year:sta
        if "start_year" in match.columns and "end_year" in match.columns:
            start = match.iloc[0]["start_year"]
            end = match.iloc[0]["end_year"]
            if pd.notna(start) and pd.notna(end):
                return f"{int(start)}-{int(end)}"
        # Tai käytä primary_team_name jos saatavilla
        if "primary_team_name" in match.columns:
            primary = match.iloc[0]["primary_team_name"]
            if pd.notna(primary):
                return str(primary)
    
    return f"Kausi {season_id}"

