from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import leaguedashplayerbiostats, playerprofilev2, commonteamroster, commonplayerinfo, commonallplayers

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

"""--------------------------------------------------------------------
     STORING AND ACCESSING DATAFRAMES
--------------------------------------------------------------------"""
save_path = "./nba_data/raw/"

def save_df(df, filename):
	df.to_csv(save_path + filename + ".csv")

def is_df_saved(filename):
	return os.path.isfile(save_path + filename + ".csv")

def get_df(filename):
	if(not is_df_saved(filename)):
		return None
	else:
		return pd.read_csv(save_path + filename  + ".csv")

"""--------------------------------------------------------------------
     GETTER FUNCTIONS
--------------------------------------------------------------------"""
"""
def func():
	filename = 
	if(is_df_saved(filename)):
		df = get_df(filename)
	else:
		df = get the df
		save_df(df, filename)
	return df

"""
def get_team_id(team_abbr):
	return teams.find_team_by_abbreviation(team_abbr)["id"]

def get_common_all_players(season="2017-18", is_only_current_season=False):
	filename = ("CommonAllPlayers__isonlycurrentseason-%d_season-%s" % (is_only_current_season, season))
	if(is_df_saved(filename)):
		df = get_df(filename)
	else:
		all_players = commonallplayers.CommonAllPlayers(is_only_current_season=0, league_id="00", season="2017-18")
		df = all_players.common_all_players.get_data_frame()
		save_df(df, filename)
	return df

def get_roster_stats(team_id, season, per_mode="Totals"):
	filename = ("LeagueDashPlayerBioStats__team-%s_season-%s_permode-%s" % (team_id, season, per_mode))
	print("Getting roster stats of %s for %s..." % (team_id, season))
	if(is_df_saved(filename)):
		df = get_df(filename)
	else:
		roster_stats = leaguedashplayerbiostats.LeagueDashPlayerBioStats(
			per_mode_simple="Totals",
			season=season,
			season_type_all_star="Regular Season",
			team_id_nullable=team_id)
		df = roster_stats.get_data_frames()[0]
		save_df(df, filename)
	return df


def get_player_stats(player_id, per_mode="Per36"):
	filename = ("PlayerProfileV2__player-%s_permode-%s" % (player_id, per_mode))
	print("Getting player stats of %s..." % (player_id))
	if(is_df_saved(filename)):
		df = get_df(filename)
	else:
		profile = playerprofilev2.PlayerProfileV2(per_mode36="Per36", player_id=player_id)
		df = profile.season_totals_regular_season.get_data_frame()
		save_df(df, filename)
	return df

""" TODO"""
def get_all_teammates(player_id, per_mode="Per36"):
	df = get_player_stats(player_id, per_mode)
	for idx, (season, team_id) in df[["SEASON_ID", "TEAM_ID"]].iterrows():
		print(get_roster_stats(team_id, season))

def get_roster_experience(team_id, season, min_total_exp=0, exclude=[]):
	df = get_common_roster(team_id, season)
	df = df[~df.PLAYER_ID.isin(exclude)]
	if(min_total_exp):
		exp_list = []
		common_all_df = get_common_all_players()
		for idx, (player_id, exp) in df[["PLAYER_ID", "EXP"]].iterrows():
			from_year, to_year = common_all_df[common_all_df["PERSON_ID"] == player_id][["FROM_YEAR", "TO_YEAR"]].values.tolist()[0]
			if(int(to_year) - int(from_year) >= min_total_exp):
				if(exp == "R"):
					exp_list.append(0)
				else:
					exp_list.append(int(exp))
		exp_list = np.array(exp_list)
	else:
		exp_list = np.array([int(exp) for exp in df["EXP"].replace("R", '0').tolist()])
	print(exp_list)
	return np.histogram(exp_list, bins=list(range(max(exp_list))))

def get_common_roster(team_id, season):
	filename = ("CommonTeamRoster__team-%s_season-%s" % (team_id, season))
	if(is_df_saved(filename)):
		df = get_df(filename)
	else:
		roster = commonteamroster.CommonTeamRoster(season=season, team_id=team_id)
		df = roster.common_team_roster.get_data_frame()
		save_df(df, filename)
	return df


raw_cum_hist = np.zeros(25)
min5_cum_hist = np.zeros(25)
lebron_id = players.find_players_by_first_name('lebron')[0]["id"]
df = get_player_stats(lebron_id)

for idx,(season, team_id) in df[["SEASON_ID", "TEAM_ID"]].iterrows():
	if(season == "2018-19"):
		continue
	print("Getting the roster of %s for %s..." % (team_id, season))
	raw_hist, _ = get_roster_experience(team_id, season, exclude=[lebron_id])
	for idx, val in enumerate(raw_hist):
		raw_cum_hist[idx] += val

	min5_hist, _ = get_roster_experience(team_id, season,min_total_exp=5, exclude=[lebron_id])
	for idx, val in enumerate(min5_hist):
		min5_cum_hist[idx] += val

plt.clf()
plt.rc('axes', axisbelow=True)
plt.grid()

max_idx = np.max(np.where(raw_cum_hist))
raw_cum_hist = raw_cum_hist[:max_idx+1]
plt.bar(list(range(len(raw_cum_hist))), raw_cum_hist, color="b")
plt.bar(list(range(len(min5_cum_hist))), min5_cum_hist, color="r")


plt.xlim([0, max_idx])
plt.title("Experience of LeBron James's Teammates")
plt.xlabel("NBA Experience (years)")
plt.ylabel("Number of Teammates")
plt.legend(["All", "Min. 5 Year Total Experience"],loc=1)
plt.show()