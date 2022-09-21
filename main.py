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


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)


intents = discord.Intents.none()
intents.guilds = True
intents.message_content = True

client = MyClient(intents=intents)

tree = app_commands.CommandTree(client)

@tree.command(name="help", description="Get help")
async def help(interaction: discord.Interaction):
    await interaction.response.send_message("""
    /help - Show this message \n
    /set_languages [string] - Set the languages for which the bot will NOT translate the message \n
    Made by Tristan BONY --> https://www.tristanbony.me
    """, ephemeral=True)
