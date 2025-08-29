# filename: fantasy_dashboard.py
import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

st.set_page_config(page_title="MMD Fantasy Premier League Dashboard", layout="wide")
st.title("MMD Fantasy Premier League Dashboard")

# === CONFIG: your league team IDs ===
team_ids = [6804305, 6475616, 7630478, 8284156, 5970120, 8621739, 8162807, 
            129602, 6464602, 6355768, 6487225, 8391124, 2127924, 9312964, 
            3425760, 7541474, 3332403, 6543964, 8446521, 8659796, 6349390, 
            7439912, 6334273, 6390807, 8664581, 9569428, 9623810]

# === FETCH CURRENT AND HISTORICAL DATA ===
team_data = []
all_history = {}

with st.spinner("Fetching FPL data..."):
    for tid in team_ids:
        team_url = f"https://fantasy.premierleague.com/api/entry/{tid}/"
        hist_url = f"https://fantasy.premierleague.com/api/entry/{tid}/history/"

        team_summary = requests.get(team_url).json()
        history = requests.get(hist_url).json()["current"]

        # Current GW is the last in history
        current_gw_points = history[-1]["points"] if history else 0
        total_points = team_summary["summary_overall_points"]

        team_data.append({
            "Team Name": team_summary["name"],
            "Manager": f"{team_summary['player_first_name']} {team_summary['player_last_name']}",
            "Current GW Points": current_gw_points,
            "Total Points": total_points
        })

        gw_df = pd.DataFrame(history)[["event", "points", "total_points"]]
        gw_df["Team Name"] = team_summary["name"]
        gw_df["Manager"] = f"{team_summary['player_first_name']} {team_summary['player_last_name']}"
        all_history[tid] = gw_df

# --- Current League Standings with Gold Highlight ---
standings_df = pd.DataFrame(team_data).sort_values("Total Points", ascending=False).reset_index(drop=True)
standings_df.index += 1

# Find max Current GW Points
max_gw_points = standings_df["Current GW Points"].max()

# Styling function for top scorer
def highlight_top(s):
    return ['background-color: gold; font-weight: bold' if v == max_gw_points else '' for v in s]

# Center alignment styles
styles = [
    dict(selector="td", props=[("text-align", "center")]),
    dict(selector="th", props=[("text-align", "center")])
]

st.subheader("Current League Standings")
st.dataframe(
    standings_df.style.apply(highlight_top, subset=["Current GW Points"])
                   .set_table_styles(styles),
    height=1016  # adjust height to fit all rows
)

# === FULL GW POINTS HISTORY TABLE ===
hist_df = pd.concat(all_history.values())

# Pivot so rows = teams, columns = gameweeks
hist_points_table = hist_df.pivot(index="Team Name", columns="event", values="points").fillna(0)

# Convert points to integers
hist_points_table = hist_points_table.astype(int)

# Function to highlight top scorer(s) in each GW
def highlight_top_scorers(s):
    is_max = s == s.max()
    return ['background-color: gold; font-weight: bold' if v else '' for v in is_max]

st.subheader("Gameweek Points History")
st.dataframe(
    hist_points_table.style.apply(highlight_top_scorers, axis=0)
                           .set_table_styles(styles),
    height=1016  # adjust as needed for all rows
)

# === LEAGUE POSITIONS BY GW (for plot) ===
league_table = hist_df.groupby("event").apply(
    lambda x: x.sort_values("total_points", ascending=False).assign(Position=range(1, len(x)+1))
).reset_index(drop=True)

# --- Plot league positions over time ---
st.subheader("League Positions Over Time")
fig, ax = plt.subplots(figsize=(12,6))
for team in league_table["Team Name"].unique():
    team_data_plot = league_table[league_table["Team Name"] == team]
    ax.plot(team_data_plot["event"], team_data_plot["Position"], marker="o", label=team)

ax.invert_yaxis()
ax.set_xlabel("Game Week")
ax.set_ylabel("League Position")
ax.set_title("League Positions Over Time")
ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
st.pyplot(fig)

# --- Manager of the Week ---
gw_points = hist_df.groupby(["event", "Team Name", "Manager"])["points"].sum().reset_index()

# Find idxmax per event
idx = gw_points.groupby("event")["points"].idxmax()

# Create new DataFrame from those rows, reset index properly
manager_of_week = pd.DataFrame(gw_points.loc[idx]).reset_index(drop=True)

# Keep only the columns we want
manager_of_week = manager_of_week[["event", "Team Name", "Manager", "points"]]

# Center alignment for manager table
st.subheader("Manager of the Week Each Game Week")
st.dataframe(manager_of_week.style.set_table_styles(styles))

# --- Highest single GW score ---
highest_gw = gw_points.loc[gw_points["points"].idxmax()]
st.subheader("Highest Single Gameweek Score")
st.write(f"Game Week {highest_gw['event']}: {highest_gw['Manager']} ({highest_gw['Team Name']}) scored {highest_gw['points']} points")
