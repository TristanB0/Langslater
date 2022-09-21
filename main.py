import asyncio
import sqlite3
from os import getenv

import discord
import requests
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
discord_token = getenv("DISCORD_TOKEN")
deepl_auth_key = getenv("DEEPL_AUTH_KEY")

con = sqlite3.connect("database.db3")
cur = con.cursor()
cur.execute("drop table user;")    # for debugging only
cur.execute("""CREATE TABLE IF NOT EXISTS languages (
                guild_id INTEGER NOT NULL,
				language VARCHAR NOT NULL,
                PRIMARY KEY (guild_id));""")
con.commit()
