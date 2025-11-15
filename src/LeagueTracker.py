"""
    This is a League Stat Tracker using Riots API
    It will just take in average Champs, Average Roles
    Average CS, Win/Loss Record

"""
import pandas as pd
import requests
from dotenv import load_dotenv
import os
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

api_key = os.environ.get('riot_api_key')
character = 'https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-summary.json'
items = 'https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/items.json'

_item_data_cache = None  # cache globally so we only fetch once
_character_data_cache = None  # cache character data

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
        print(f"Riot API error {response.status_code}: {response.text}")
        return None

    data = response.json()
    if "puuid" not in data:
        print("No 'puuid' in response:", data)
        return None

    return data["puuid"]

def get_match_history(puuid=None,start=0, count=20):
    root_url = f'https://americas.api.riotgames.com/'
    endpoint = f'lol/match/v5/matches/by-puuid/{puuid}/ids'
    query_params = f'?start={start}&count={count}'
    response = requests.get(root_url + endpoint + query_params +"&api_key=" + api_key, timeout=10)

    return response.json()

def get_match_data_from_id(matchId = None):
    root_url = f'https://americas.api.riotgames.com/'
    endpoint = f'lol/match/v5/matches/{matchId}'
    response = requests.get(root_url+endpoint+'?api_key=' +api_key, timeout=10)

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
    minions = player['totalMinionsKilled']
    minions += neutral_minions_killed
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
        'minions':[minions],
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
    """
    This is the way we are making the character names instead of the id numbers.
    It takes in the dataframe, finds the names and ids from thee character json file (community dragon)
    and puts them into the dataframe
    :param df: the user dataframe
    :return: an updated user dataframe that will have champion names instead of ids
    """
    global _character_data_cache

    # Cache character data
    if _character_data_cache is None:
        character_json = requests.get(character, timeout=10).json()
        character_names = json_extract(character_json, 'name')
        character_ids = json_extract(character_json, 'id')
        _character_data_cache = dict(map(lambda i, j: (int(i), j), character_ids, character_names))

    df['champion'] = df['champion'].replace(_character_data_cache)

    return df



def get_images(data_frame):
    """
    Given a row or dict-like object containing item0..item6,
    return a list of valid CommunityDragon item URLs using item_id.
    Skips missing or zero items.
    """
    global _item_data_cache

    if _item_data_cache is None:
        items_url = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/items.json"
        try:
            _item_data_cache = requests.get(items_url, timeout=10).json()
        except Exception as e:
            print(f"Error fetching item JSON: {e}")
            return []

    # Build item_id -> icon_path dict from the JSON
    image_dict = {}
    for item in _item_data_cache:
        try:
            item_id = int(item["id"])
            # The iconPath in the JSON looks like: "/lol-game-data/assets/ASSETS/Items/Icons2D/1001_healthpotion.png"
            icon_path = item.get("iconPath", "")
            if not icon_path:
                continue

            # Remove the /lol-game-data/assets/ prefix and convert to lowercase
            # CommunityDragon URLs are case-sensitive and all lowercase
            icon_path = icon_path.replace("/lol-game-data/assets/", "").lstrip('/').lower()
            url = f"https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/{icon_path}"
            image_dict[item_id] = url
        except (ValueError, KeyError, TypeError):
            continue

    # Extract valid item IDs from row
    image_paths = []
    for i in range(7):
        try:
            item_val = data_frame.get(f"item{i}") if isinstance(data_frame, dict) else data_frame[f"item{i}"]
            item_id = int(item_val)
            if item_id != 0 and item_id in image_dict:
                image_paths.append(image_dict[item_id])
        except (ValueError, TypeError, KeyError):
            continue

    return image_paths

def get_player_stats(puuid, match_count=1):
    match_ids = get_match_history(puuid, start=0, count=match_count)

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(get_match_data_from_id, mid) for mid in match_ids]
        match_data = [f.result() for f in futures]

    df = pd.concat([process_match_json(game, puuid) for game in match_data], ignore_index=True)
    df = make_it_pretty(df)
    return df

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
