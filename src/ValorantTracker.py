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