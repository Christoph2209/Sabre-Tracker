"""
    This is a League Stat Tracker using Riots API
    It will just take in average Champs, Average Roles
    Average CS, Win/Loss Record

"""
from http.client import responses

import pandas as pd
import requests
from dotenv import load_dotenv
import os
import pygsheets
import tkinter

load_dotenv()
gameName = 'geonbu'
tagLine = '0618'
api_key = os.environ.get('riot_api_key')


def get_puuuid(summonerId=None, gameName=None, tagLine=None, api_key=None):
    """
    Gets the puuid from a summonerId or riot_id and riot_tag.
    :param gameName:
    :param tagLine:
    :param api_key:
    :return:
    """
    if summonerId is not None:
        root_url = f'https://americas.api.riotgames.com/'
        endpoint = 'lol/summoner/v4/summoners'
        print(root_url+endpoint+summonerId+"?api_key="+api_key)
        response = requests.get(root_url+endpoint+summonerId+"?api_key="+api_key)

        return response.json()['puuid']
    else:
        link = f'https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}?api_key={api_key}'

        response = requests.get(link)

        return response.json()['puuid']

def get_match_history(puuid=None,start=0, count=20):
    root_url = f'https://americas.api.riotgames.com/'
    endpoint = f'lol/match/v5/matches/by-puuid/{puuid}/ids'
    query_params = f'?start={start}&count={count}'
    response = requests.get(root_url + endpoint + query_params +"&api_key=" + api_key)

    return response.json()

def get_match_data_from_id(matchId = None):
    root_url = f'https://americas.api.riotgames.com/'
    endpoint = f'lol/match/v5/matches/{matchId}'
    print(root_url+endpoint+'?api_key=' +api_key)
    response = requests.get(root_url+endpoint+'?api_key=' +api_key)

    return response.json()

#userName = input("Enter Username: ")
#userTag = input("Enter Tag: ")

userP = get_puuuid(gameName=gameName,tagLine=tagLine,api_key=api_key)
print(userP)
z = get_match_history(userP, start=0, count=10)

def process_match_json(match_json, puuid):
    metadata= match_json['metadata']

    match_id = metadata['matchId']
    info = match_json['info']
    players = info['participants']
    participants = metadata['participants']
    teams = info['teams']
    player = players[participants.index(puuid)]
    perks = player['perks']
    stats = perks['statPerks']
    styles = perks['styles']

    side_dict = {
        100:'Blue',
        200:'Red'
    }

    side = side_dict[player['teamId']]

    game_creation = info['gameCreation']
    game_duration = info['gameDuration']
    game_start_time = info['gameStartTimestamp']
    game_end = info['gameEndTimestamp']
    patch = info['gameVersion']


    role = player['role']
    champ_lvl = player['champLevel']
    champ_id = player['championId']
    champ_transform = player['championTransform']
    deaths = player['deaths']
    assists = player['assists']
    kills = player['kills']

    first_blood = player['firstBloodKill']
    early_surrender = player['gameEndedInEarlySurrender']
    surrender = player['gameEndedInSurrender']

    gold_earned = player['goldEarned']

    item0 = player['item0']
    item1 = player['item1']
    item2 = player['item2']
    item3 = player['item3']
    item4 = player['item4']
    item5 = player['item5']
    item6 = player['item6']

    neutral_minions_killed = player['neutralMinionsKilled']

    summoner_id = player['summonerId']
    summoner_name = player['summonerName']

    total_damage_dealt = player['totalDamageDealtToChampions']
    total_damage_shielded = player['totalDamageShieldedOnTeammates']
    total_damage_taken = player['totalDamageTaken']
    total_damage_healed = player['totalHealsOnTeammates']
    total_time_cc_dealt = player['totalTimeCCDealt']
    total_minions_killed = player['totalMinionsKilled']


    wards_placed = player['wardsPlaced']
    wards_killed = player['wardsKilled']
    vision_score = player['visionScore']
    win = player['win']


    primary = styles[0]
    secondary = styles[1]

    defense = stats['defense']
    offense = stats['offense']
    flex = stats['flex']

    primary_style = primary['style']
    secondary_style = secondary['style']

    primary_keystone = primary['selections'][0]['perk']
    primary_perk1 = primary['selections'][1]['perk']
    primary_perk2 = primary['selections'][2]['perk']
    primary_perk3 = primary['selections'][3]['perk']


    secondary_perk1 = secondary['selections'][0]['perk']
    secondary_perk2 = secondary['selections'][1]['perk']


    objectives_stolen = player['objectivesStolen']
    objectives_stolen_assists = player['objectivesStolenAssists']
    for team in teams:
        if team['teamId'] == player['teamId']:
            objs = team['objectives']
            baron = objs['baron']
            dragon = objs['dragon']
            grubs = objs['horde']
            rift_harold = objs['riftHerald']
            tower = objs['tower']
            inhibitor = objs['inhibitor']

    matchDF = pd.DataFrame({
        'match_id': [match_id],
        'participants': [participants],
        'game_creation': [game_creation],
        'game_duration': [game_duration],
        'game_start_time' : [game_start_time],
        'game_end' : [game_end],
        'patch' : [patch],
        'puuid': [puuid],
        'win': [win],
        'side': [side],
        'role': [role],
        'champ_lvl':[champ_lvl],
        'champion':[champ_id],
        'champ_transform':[champ_transform],
        'deaths': [deaths],
        'assists':[assists],
        'kills':[kills],
        'first_blood':[first_blood],
        'early_surrender':[early_surrender],
        'surrender':[surrender],
        'gold_earned':[gold_earned],
        'item0':[item0],
        'item1':[item1],
        'item2':[item2],
        'item3':[item3],
        'item4':[item4],
        'item5':[item5],
        'item6':[item6],
        'neutral_minions_killed': [neutral_minions_killed],
        'summoner_id': [summoner_id],
        'summoner_name':[summoner_name],
        'total_damage_dealt': [total_damage_dealt],
        'total_damage_shielded': [total_damage_shielded],
        'total_damage_taken': [total_damage_taken],
        'total_damage_healed': [total_damage_healed],
        'total_time_cc_dealt': [total_time_cc_dealt],
        'total_minions_killed': [total_minions_killed],
        'wards_placed': [wards_placed],
        'wards_killed': [wards_killed],
        'vision_score': [vision_score],
        'defense': [defense],
        'offense':[offense],
        'flex':[flex],
        'primary_style':[primary_style],
        'secondary_style':[secondary_style],
        'primary_keystone':[primary_keystone],
        'primary_perk1':[primary_perk1],
        'primary_perk2':[primary_perk2],
        'primary_perk3':[primary_perk3],
        'secondary_perk1':[secondary_perk1],
        'secondary_perk2':[secondary_perk2],
        'objectives_stolen':[objectives_stolen],
        'objectives_stolen_assists':[objectives_stolen_assists],
    })
    return matchDF
df = pd.DataFrame()
for a in z:
    game = get_match_data_from_id(a)
    mat = process_match_json(game, userP)
    df = pd.concat([df, mat])
#service_account = pygsheets.authorize(service_account_file='JSONs\\spreadsheet-automator-476214-29c53ecbafc7.json')
print(df.to_string())
#sheet = service_account.open_by_url('https://docs.google.com/spreadsheets/d/1WiaxzdPN6mucwCFS4FqtFpUpTxefoqHq0_dH0c3nRIc/edit?usp=sharing')
