"""Datan rikastus, joinit ja metriikkafunktiot."""

from typing import Dict, List, Optional, Tuple
import pandas as pd

from .io import get_team_name, get_competition_stage


def enrich_matches(
    matches_df: pd.DataFrame,
    data: Dict[str, pd.DataFrame],
    selected_team_id: Optional[int] = None
) -> pd.DataFrame:
    """
    Rikastaa ottelutiedot joukkueiden nimillä ja laskee metriikat.
    
    Args:
        matches_df: Ottelut DataFrame
        data: Sanakirja kaikista sheeteistä
        selected_team_id: Valitun joukkueen ID (jos None, ei lasketa outcomea)
        
    Returns:
        Rikastettu DataFrame
    """
    if matches_df.empty:
        return matches_df.copy()
    
    df = matches_df.copy()
    
    # Lisää joukkueiden nimet
    if "home_team_id" in df.columns:
        df["home_team_name"] = df["home_team_id"].apply(
            lambda x: get_team_name(x, data) if pd.notna(x) else "Tuntematon"
        )
    
    if "away_team_id" in df.columns:
        df["away_team_name"] = df["away_team_id"].apply(
            lambda x: get_team_name(x, data) if pd.notna(x) else "Tuntematon"
        )
    
    # Käsittele puuttuva competition_id
    if "competition_id" in df.columns:
        df["competition_id"] = df["competition_id"].fillna(-1)
        df["competition_stage"] = df["competition_id"].apply(
            lambda x: get_competition_stage(x, data) if x != -1 else "Tuntematon"
        )
    else:
        df["competition_stage"] = "Tuntematon"
    
    # Laske outcome valitun joukkueen näkökulmasta
    if selected_team_id is not None:
        def calculate_outcome(row):
            home_id = row.get("home_team_id")
            away_id = row.get("away_team_id")
            home_goals = row.get("home_goals", 0)
            away_goals = row.get("away_goals", 0)
            
            if pd.isna(home_id) or pd.isna(away_id):
                return None
            
            if home_id == selected_team_id:
                goals_for = home_goals
                goals_against = away_goals
            elif away_id == selected_team_id:
                goals_for = away_goals
                goals_against = home_goals
            else:
                return None
            
            if goals_for > goals_against:
                return "W"
            elif goals_for < goals_against:
                return "L"
            else:
                return "D"
        
        def calculate_goals_for(row):
            home_id = row.get("home_team_id")
            away_id = row.get("away_team_id")
            home_goals = row.get("home_goals", 0)
            away_goals = row.get("away_goals", 0)
            
            if pd.isna(home_id) or pd.isna(away_id):
                return None
            
            if home_id == selected_team_id:
                return home_goals
            elif away_id == selected_team_id:
                return away_goals
            return None
        
        def calculate_goals_against(row):
            home_id = row.get("home_team_id")
            away_id = row.get("away_team_id")
            home_goals = row.get("home_goals", 0)
            away_goals = row.get("away_goals", 0)
            
            if pd.isna(home_id) or pd.isna(away_id):
                return None
            
            if home_id == selected_team_id:
                return away_goals
            elif away_id == selected_team_id:
                return home_goals
            return None
        
        df["outcome"] = df.apply(calculate_outcome, axis=1)
        df["goals_for"] = df.apply(calculate_goals_for, axis=1)
        df["goals_against"] = df.apply(calculate_goals_against, axis=1)
        df["goal_diff"] = df["goals_for"] - df["goals_against"]
        
        # Laske pisteet (voitto=2, tasuri=1, tappio=0)
        def calculate_points(row):
            outcome = row.get("outcome")
            if outcome == "W":
                return 2
            elif outcome == "D":
                return 1
            elif outcome == "L":
                return 0
            return None
        
        df["points_from_match"] = df.apply(calculate_points, axis=1)
    else:
        # Jos ei valittua joukkuetta, näytä raaka data
        df["outcome"] = None
        df["goals_for"] = None
        df["goals_against"] = None
        df["goal_diff"] = None
        df["points_from_match"] = None
    
    return df


def parse_match_dates(matches_df: pd.DataFrame) -> pd.DataFrame:
    """
    Parsii päivämäärät datetimeiksi ja järjestää aikajärjestykseen.
    
    Args:
        matches_df: Ottelut DataFrame
        
    Returns:
        Järjestetty DataFrame
    """
    if matches_df.empty or "date" not in matches_df.columns:
        return matches_df.copy()
    
    df = matches_df.copy()
    
    # Yritä parsia päivämäärät
    df["date"] = pd.to_datetime(df["date"], errors='coerce')
    
    # Järjestä päivämäärän mukaan
    df = df.sort_values("date", na_position='last')
    
    return df


def filter_matches(
    matches_df: pd.DataFrame,
    data: Dict[str, pd.DataFrame],
    season_ids: Optional[List[int]] = None,
    team_id: Optional[int] = None,
    stage: Optional[str] = None,
    opponent_id: Optional[int] = None,
    home_away: Optional[str] = None
) -> pd.DataFrame:
    """
    Suodattaa ottelut kriteereillä.
    
    Args:
        matches_df: Ottelut DataFrame
        data: Sanakirja kaikista sheeteistä
        season_ids: Lista kausi-ID:itä (None = kaikki)
        team_id: Joukkueen ID (None = kaikki)
        stage: Sarjavaihe (None tai "All" = kaikki)
        opponent_id: Vastustajan ID (None = kaikki)
        home_away: "Home", "Away" tai None/"All"
        
    Returns:
        Suodatettu DataFrame
    """
    if matches_df.empty:
        return matches_df.copy()
    
    df = matches_df.copy()
    
    # Suodata kausi
    if season_ids is not None and len(season_ids) > 0:
        if "season_id" in df.columns:
            df = df[df["season_id"].isin(season_ids)]
    
    # Suodata joukkue
    if team_id is not None:
        if "home_team_id" in df.columns and "away_team_id" in df.columns:
            df = df[
                (df["home_team_id"] == team_id) | 
                (df["away_team_id"] == team_id)
            ]
    
    # Suodata sarjavaihe
    if stage is not None and stage != "All":
        if "competition_id" in df.columns:
            # Rikasta competition_stage jos ei ole
            if "competition_stage" not in df.columns:
                df["competition_stage"] = df["competition_id"].apply(
                    lambda x: get_competition_stage(x, data) if pd.notna(x) else "Tuntematon"
                )
            df = df[df["competition_stage"] == stage]
    
    # Suodata vastustaja
    if opponent_id is not None:
        if "home_team_id" in df.columns and "away_team_id" in df.columns:
            df = df[
                ((df["home_team_id"] == opponent_id) & (df["away_team_id"] == team_id)) |
                ((df["away_team_id"] == opponent_id) & (df["home_team_id"] == team_id))
            ]
    
    # Suodata koti/vieras
    if home_away is not None and home_away != "All" and team_id is not None:
        if home_away == "Home":
            df = df[df["home_team_id"] == team_id]
        elif home_away == "Away":
            df = df[df["away_team_id"] == team_id]
    
    return df


def calculate_summary_stats(matches_df: pd.DataFrame) -> Dict[str, float]:
    """
    Laske yhteenvetometriikat.
    
    Args:
        matches_df: Suodatettu ottelut DataFrame (pitää olla rikastettu)
        
    Returns:
        Sanakirja metriikoista
    """
    if matches_df.empty or "outcome" not in matches_df.columns:
        return {
            "GP": 0, "W": 0, "D": 0, "L": 0,
            "GF": 0, "GA": 0, "GD": 0,
            "points": 0, "PPG": 0.0,
            "GF_per_game": 0.0, "GA_per_game": 0.0
        }
    
    # Poista rivit joissa outcome puuttuu
    df = matches_df[matches_df["outcome"].notna()].copy()
    
    if df.empty:
        return {
            "GP": 0, "W": 0, "D": 0, "L": 0,
            "GF": 0, "GA": 0, "GD": 0,
            "points": 0, "PPG": 0.0,
            "GF_per_game": 0.0, "GA_per_game": 0.0
        }
    
    GP = len(df)
    W = len(df[df["outcome"] == "W"])
    D = len(df[df["outcome"] == "D"])
    L = len(df[df["outcome"] == "L"])
    
    GF = df["goals_for"].sum() if "goals_for" in df.columns else 0
    GA = df["goals_against"].sum() if "goals_against" in df.columns else 0
    GD = GF - GA
    
    points = df["points_from_match"].sum() if "points_from_match" in df.columns else 0
    PPG = points / GP if GP > 0 else 0.0
    
    GF_per_game = GF / GP if GP > 0 else 0.0
    GA_per_game = GA / GP if GP > 0 else 0.0
    
    return {
        "GP": GP,
        "W": W,
        "D": D,
        "L": L,
        "GF": GF,
        "GA": GA,
        "GD": GD,
        "points": points,
        "PPG": round(PPG, 2),
        "GF_per_game": round(GF_per_game, 2),
        "GA_per_game": round(GA_per_game, 2)
    }


def calculate_best_worst(
    matches_df: pd.DataFrame,
    data: Dict[str, pd.DataFrame],
    team_id: int
) -> Tuple[Optional[Dict], Optional[Dict]]:
    """
    Laske paras voitto ja rumin tappio.
    
    Args:
        matches_df: Suodatettu ottelut DataFrame
        data: Sanakirja kaikista sheeteistä
        team_id: Valitun joukkueen ID
        
    Returns:
        Tuple (paras_voitto, rumin_tappio) dictit tai None
    """
    if matches_df.empty or "goal_diff" not in matches_df.columns:
        return None, None
    
    df = matches_df[matches_df["goal_diff"].notna()].copy()
    
    if df.empty:
        return None, None
    
    # Apufunktio vastustajan nimen hakemiseen
    def get_opponent_name(row):
        home_id = row.get("home_team_id")
        away_id = row.get("away_team_id")
        if pd.notna(home_id) and pd.notna(away_id):
            if home_id == team_id:
                return row.get("away_team_name", "Tuntematon")
            elif away_id == team_id:
                return row.get("home_team_name", "Tuntematon")
        return "Tuntematon"
    
    # Paras voitto (suurin goal_diff)
    wins = df[df["outcome"] == "W"]
    if not wins.empty:
        best = wins.loc[wins["goal_diff"].idxmax()]
        best_win = {
            "date": best.get("date"),
            "opponent": get_opponent_name(best),
            "goals_for": best.get("goals_for"),
            "goals_against": best.get("goals_against"),
            "goal_diff": best.get("goal_diff")
        }
    else:
        best_win = None
    
    # Rumin tappio (pienin goal_diff)
    losses = df[df["outcome"] == "L"]
    if not losses.empty:
        worst = losses.loc[losses["goal_diff"].idxmin()]
        worst_loss = {
            "date": worst.get("date"),
            "opponent": get_opponent_name(worst),
            "goals_for": worst.get("goals_for"),
            "goals_against": worst.get("goals_against"),
            "goal_diff": worst.get("goal_diff")
        }
    else:
        worst_loss = None
    
    return best_win, worst_loss


def calculate_form(matches_df: pd.DataFrame, n_games: int = 5) -> Dict[str, any]:
    """
    Laske vire viimeisistä N pelistä.
    
    Args:
        matches_df: Suodatettu ottelut DataFrame (järjestettynä päivämäärän mukaan)
        n_games: Montako viimeistä peliä
        
    Returns:
        Sanakirja vire-metriikoista
    """
    if matches_df.empty or "outcome" not in matches_df.columns:
        return {"form": "N/A", "points": 0, "record": "0-0-0"}
    
    df = matches_df[matches_df["outcome"].notna()].copy()
    
    if df.empty:
        return {"form": "N/A", "points": 0, "record": "0-0-0"}
    
    # Ota viimeiset N peliä
    last_n = df.tail(n_games)
    
    if last_n.empty:
        return {"form": "N/A", "points": 0, "record": "0-0-0"}
    
    W = len(last_n[last_n["outcome"] == "W"])
    D = len(last_n[last_n["outcome"] == "D"])
    L = len(last_n[last_n["outcome"] == "L"])
    
    points = last_n["points_from_match"].sum() if "points_from_match" in last_n.columns else 0
    
    form = f"{W}-{D}-{L}"
    record = f"{W}-{D}-{L}"
    
    return {
        "form": form,
        "points": int(points),
        "record": record
    }


def calculate_opponent_stats(
    matches_df: pd.DataFrame,
    data: Dict[str, pd.DataFrame],
    team_id: int
) -> pd.DataFrame:
    """
    Laske vastustajien tilastot: eniten pelejä + voittoprosentti.
    
    Args:
        matches_df: Suodatettu ottelut DataFrame
        data: Sanakirja kaikista sheeteistä
        team_id: Valitun joukkueen ID
        
    Returns:
        DataFrame vastustajista järjestettynä pelejen määrän mukaan
    """
    if matches_df.empty or "outcome" not in matches_df.columns:
        return pd.DataFrame(columns=["opponent", "games", "wins", "draws", "losses", "win_pct"])
    
    df = matches_df[matches_df["outcome"].notna()].copy()
    
    if df.empty:
        return pd.DataFrame(columns=["opponent", "games", "wins", "draws", "losses", "win_pct"])
    
    # Määritä vastustaja jokaiselle ottelulle
    def get_opponent(row):
        home_id = row.get("home_team_id")
        away_id = row.get("away_team_id")
        
        if pd.isna(home_id) or pd.isna(away_id):
            return None
        
        if home_id == team_id:
            return away_id
        elif away_id == team_id:
            return home_id
        return None
    
    df["opponent_id"] = df.apply(get_opponent, axis=1)
    df = df[df["opponent_id"].notna()]
    
    if df.empty:
        return pd.DataFrame(columns=["opponent", "games", "wins", "draws", "losses", "win_pct"])
    
    # Ryhmittele vastustajittain
    opponent_stats = []
    for opponent_id, group in df.groupby("opponent_id"):
        opponent_name = get_team_name(int(opponent_id), data)
        games = len(group)
        wins = len(group[group["outcome"] == "W"])
        draws = len(group[group["outcome"] == "D"])
        losses = len(group[group["outcome"] == "L"])
        win_pct = (wins / games * 100) if games > 0 else 0.0
        
        opponent_stats.append({
            "opponent": opponent_name,
            "games": games,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "win_pct": round(win_pct, 1)
        })
    
    result_df = pd.DataFrame(opponent_stats)
    result_df = result_df.sort_values("games", ascending=False)
    
    return result_df


def calculate_cumulative_points(matches_df: pd.DataFrame) -> pd.DataFrame:
    """
    Laske kumulatiiviset pisteet ajan yli.
    
    Args:
        matches_df: Suodatettu ottelut DataFrame (järjestettynä päivämäärän mukaan)
        
    Returns:
        DataFrame päivämäärällä ja kumulatiivisilla pisteillä
    """
    if matches_df.empty or "points_from_match" not in matches_df.columns:
        return pd.DataFrame(columns=["date", "cumulative_points"])
    
    df = matches_df[matches_df["points_from_match"].notna()].copy()
    
    if df.empty:
        return pd.DataFrame(columns=["date", "cumulative_points"])
    
    # Varmista että on päivämäärä
    if "date" not in df.columns:
        return pd.DataFrame(columns=["date", "cumulative_points"])
    
    # Järjestä päivämäärän mukaan
    df = df.sort_values("date")
    
    # Laske kumulatiiviset pisteet
    df["cumulative_points"] = df["points_from_match"].cumsum()
    
    result = df[["date", "cumulative_points"]].copy()
    result = result.dropna(subset=["date"])
    
    return result

