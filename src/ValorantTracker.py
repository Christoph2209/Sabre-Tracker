"""
    This is a Valorant Stat Tracker using Riots API
    It will just take in average Agents, K/D/A
    Average CS, Win/Loss Record

"""
import pandas as pd
import requests
from dotenv import load_dotenv
import os

load_dotenv()
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
        print(f"Riot API error {response.status_code}: {response.text}")
        return None

    data = response.json()
    if "puuid" not in data:
        print("No 'puuid' in response:", data)
        return None

    return data["puuid"]

def get_match_history(puuid=None,start=0, count=5):
    root_url = f'https://americas.api.riotgames.com/'
    endpoint = f'val/match/v5/matches/by-puuid/{puuid}/ids'
    query_params = f'?start={start}&count={count}'
    response = requests.get(root_url + endpoint + query_params +"&api_key=" + api_key)

    return response.json()


if __name__ == '__main__':
    userName = input("Enter Username: ")
    userTag = input("Enter Tag: ")

    userP = get_puuid(gameName=userName,tagLine=userTag,api_key=api_key)
    print(userP)
    x = get_match_history(userP)
    print(x)