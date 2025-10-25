#IMPORTS
import requests
from urllib.parse import urlencode
import settings


def get_summoner_info(summoner_name=None, region=settings.DEFAULT_REGION_CODE):
    """
    Wrapper for SUMMONER-V4 API portal
    :param summoner_name: the summoners name
    :param region: the original region
    :return: Summoner information as a dictionary or None if there is an issue
    """

    if not summoner_name:
        summoner_name = input("Summoner Name:")

    params = {
        'X-Riot-Token': settings.API_KEY
    }
    api_url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}"

    try:
        response = requests.get(api_url, params=urlencode(params))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f'Issue getting summoner data from API: {e}')
        return None
