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

load_dotenv()
gameName = '877CRASHOUT'
tagLine = 'call'
api_key = os.environ.get('riot_api_key')


def get_name_from_puuid(puuid=None, api_key= None):
    link = f'https://americas.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}?api_key={api_key}'

    response = requests.get(link)
    gameNam = response.json()['gameName']
    return f'{gameNam}'

def get_puuid(summonerId=None, gameName=None, tagLine=None, api_key=None):
    """
    Gets the puuid from a summonerId or riot_id and riot_tag.
    :param gameName: In game name
    :param tagLine: Riot Tagline
    :param api_key: the API key
    :return: the puuid
    """
    if summonerId is not None:
        link = f"https://americas.api.riotgames.com/lol/summoner/v4/summoners/{summonerId}?api_key={api_key}"
    else:
        link = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}?api_key={api_key}"

    response = requests.get(link)

    # If response isn't 200 OK, handle gracefully
    if response.status_code != 200:
        print(f"⚠️ Riot API error {response.status_code}: {response.text}")
        return None

    data = response.json()
    if "puuid" not in data:
        print("⚠️ No 'puuid' in response:", data)
        return None

    return data["puuid"]

def get_match_history(puuid=None,start=0, count=20):
    root_url = f'https://americas.api.riotgames.com/'
    endpoint = f'lol/match/v5/matches/by-puuid/{puuid}/ids'
    query_params = f'?start={start}&count={count}'
    response = requests.get(root_url + endpoint + query_params +"&api_key=" + api_key)

    return response.json()

def get_match_data_from_id(matchId = None):
    root_url = f'https://americas.api.riotgames.com/'
    endpoint = f'lol/match/v5/matches/{matchId}'
    response = requests.get(root_url+endpoint+'?api_key=' +api_key)
    #print(root_url+endpoint+'?api_key=' +api_key)
    return response.json()

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


    role = player['teamPosition']
    game_queue = player['role']
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
    summoner_name = player['riotIdGameName']

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
        'queue': [game_queue],
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

def make_it_pretty(df):
    #perk = 'https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/perks.json'
    #perkstyles = 'https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/perkstyles.json'
    character = 'https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-summary.json'
    items = 'https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/items.json'

    #perk_json = requests.get(perk).json()
    #perk_style_json = requests.get(perkstyles).json()
    character_json = requests.get(character).json()
    item_json = requests.get(items).json()

    #perk_ids = json_extract(perk_json, 'id')
    #perk_names = json_extract(perk_json, 'name')
    #perk_dict = dict(map(lambda i, j: (int(i), j), perk_ids, perk_names))

    #perk_styles_ids = json_extract(perk_style_json, 'id')
    #perk_style_names = json_extract(perk_style_json, 'name')
    #perk_style_dict = dict(map(lambda i, j: (int(i), j), perk_styles_ids, perk_style_names))

    character_names = json_extract(character_json, 'name')
    character_ids = json_extract(character_json, 'id')
    character_dict = dict(map(lambda i, j: (int(i), j), character_ids, character_names))

    item_names = json_extract(item_json, 'name')
    item_ids = json_extract(item_json, 'id')
    item_dict = dict(map(lambda i, j: (int(i), j), item_ids, item_names))
    for i in range(7):
        df[f'item{i}'] = df[f'item{i}'].replace(item_dict)

    #df = df.replace(perk_dict).replace(perk_style_dict)
    df['champion'] = df['champion'].replace(character_dict)

    #player_id = df['participants'].to_list()
    #player_id = flatten_list(player_id)
    #player_dict = {}
    #for p in set(player_id):  # unique only
    #    player_dict[p] = get_name_from_puuid(p, api_key)

    # Replace puuids with Riot names in the DataFrame
    #df["participants"] = df["participants"].apply(
    #    lambda lst: [player_dict.get(p, p) for p in lst]
    #)

    return df

from concurrent.futures import ThreadPoolExecutor, as_completed

def get_player_stats(puuid, match_count=1):
    match_ids = get_match_history(puuid, start=0, count=match_count)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(get_match_data_from_id, mid) for mid in match_ids]
        match_data = [f.result() for f in as_completed(futures)]

    df = pd.concat([process_match_json(game, puuid) for game in match_data])
    df = make_it_pretty(df)
    return df


def flatten_list(nested_list):
    flat_list = []
    for sublist in nested_list:
        flat_list.extend(sublist)
    return flat_list

def json_extract(obj, key):
    arr = []
    def extract(obj,arr,key):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == key:
                    arr.append(v)
                elif isinstance(v, (dict,list)):
                    extract(v,arr,key)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    values = extract(obj, arr, key)
    return values

if __name__ == '__main__':
    #userName = input("Enter Username: ")
    #userTag = input("Enter Tag: ")

    userP = get_puuid(gameName=gameName,tagLine=tagLine,api_key=api_key)
    df = get_player_stats(userP, 5)

    print(df.to_string())
