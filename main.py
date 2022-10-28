import sqlite3
from os import getenv

import discord
import deepl
from discord import app_commands
from discord.app_commands import Choice
from dotenv import load_dotenv

load_dotenv()
discord_token = getenv("DISCORD_TOKEN")
deepl_auth_key = getenv("DEEPL_AUTH_KEY")


con = sqlite3.connect("database.db3")
cur = con.cursor()
# cur.execute("drop table languages;")    # for debugging only
cur.execute("""CREATE TABLE IF NOT EXISTS languages (
                guild_id INTEGER NOT NULL,
                language VARCHAR NOT NULL,
                PRIMARY KEY (guild_id));""")
con.commit()

translator = deepl.Translator(deepl_auth_key)
deepl_usage = translator.get_usage()


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync()
            self.synced = True
        print("Logged on as {0}".format(self.user))

        await self.change_presence(activity=discord.Game("to translate... /help"))

    async def on_disconnect(self):
        print("Disconnected from discord")

    async def on_message(self, message):
        if message.author.id == self.user.id:
            return

        if not deepl_usage.any_limit_reached:
            # Get the translation language of the server
            cur.execute("SELECT language FROM languages WHERE guild_id = ?;", (message.guild.id,))
            translation_language = cur.fetchone()

            # Verify that the administrator have set up a language
            if translation_language[0] in translator.get_source_languages():
                text_translated = translator.translate_text(message.content, target_lang=translation_language[0])

                if text_translated.detected_source_lang != translation_language[0]:
                    await message.reply("""This user said: \n\n""" + text_translated.text)
        else:
            await message.reply("""Sorry, I am not able to translate more this month :'(""")
            print(f"Character usage: {deepl_usage.character}")


intents = discord.Intents.none()
intents.guilds = True
intents.message_content = True
intents.messages = True

client = MyClient(intents=intents)

tree = app_commands.CommandTree(client)


@tree.command(name="help", description="Get help")
async def help(interaction: discord.Interaction):
    await interaction.response.send_message("""
    /help - Show this message \n
    /set_languages [string] - Set the languages for which the bot will NOT translate the message \n
    Made by Tristan Bony --> https://www.tristanbony.me
    """, ephemeral=True)


@tree.command(name="set_language", description="Set the language you don't want to be translated")
@app_commands.choices(language=[
    Choice(name="Bulgarian", value="BG"),
    Choice(name="Chinese", value="ZH"),
    Choice(name="Czech", value="CS"),
    Choice(name="Danish", value="DA"),
    Choice(name="Dutch", value="NL"),
    Choice(name="English", value="EN"),
    # Choice(name="Estonian", value="ET"),
    Choice(name="Finnish", value="FI"),
    Choice(name="French", value="FR"),
    Choice(name="German", value="GE"),
    Choice(name="Greek", value="EL"),
    Choice(name="Hungarian", value="HU"),
    Choice(name="Indonesian", value="ID"),
    Choice(name="Italian", value="IT"),
    Choice(name="Japanese", value="JA"),
    # Choice(name="Latvian", value="LV"),
    Choice(name="Lithuanian", value="LT"),
    Choice(name="Polish", value="PL"),
    Choice(name="Portuguese", value="PT"),
    Choice(name="Romanian", value="RO"),
    Choice(name="Russian", value="RU"),
    Choice(name="Slovak", value="SK"),
    Choice(name="Slovenian", value="SL"),
    Choice(name="Spanish", value="ES"),
    Choice(name="Swedish", value="SV"),
    Choice(name="Turkish", value="TR"),
    Choice(name="Ukrainian", value="UK")
])
async def set_language(interaction: discord.Interaction, language: Choice[str]):
    cur.execute("INSERT OR REPLACE INTO languages (guild_id, language) VALUES (?, ?);", (interaction.guild.id, language.value))
    con.commit()

    await interaction.response.send_message("You have added {0} language.".format(language.name), ephemeral=True)


client.run(discord_token)
