"""
    This is a League Stat Tracker using Riots API
    It will just take in average Champs, Average Roles
    Average CS, Win/Loss Record

"""

from helpers import get_summoner_info

summoner_name = "Chr1st0ph"

summoner = get_summoner_info(summoner_name)
print(summoner)
print(summoner['name'])