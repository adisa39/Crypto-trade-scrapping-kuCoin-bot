from kucoin.client import Client
import os
# from telethon import TelegramClient

os.environ['API_KEY']
api_key = os.environ['API_KEY']
api_secret = os.environ['API_SECRET']  # 'Your Kucoin API secret'
api_passphrase = os.environ['API_PASSPHRASE']

# KuCoin Client creation
kc_client = Client(api_key, api_secret, api_passphrase)