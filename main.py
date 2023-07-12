import asyncio
import datetime
import sqlite3
import logging
from os import getenv, path, makedirs

from langdetect import detect
import discord
import deepl
from discord import app_commands
from discord.app_commands import Choice
from dotenv import load_dotenv

with open(".env", 'w') as f:
    # Add ENV keys from Discord and DeepL
    f.write("DISCORD_TOKEN=")
    f.write("DEEPL_AUTH_KEY")

load_dotenv()
discord_token = getenv("DISCORD_TOKEN")
deepl_auth_key = getenv("DEEPL_AUTH_KEY")

languages = [
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
]

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

if not path.exists("logs"):
    makedirs("logs")


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.synced = False

    async def setup_hook(self) -> None:
        self.bg_task = self.loop.create_task(self.new_log())

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync()
            self.synced = True
        print("Logged on as {0}".format(self.user))
        logging.log(logging.INFO, "Logged on")

        await self.change_presence(activity=discord.Game("to translate... /help"))

    async def on_disconnect(self):
        print("Disconnected from discord")
        logging.log(logging.WARNING, "Disconnected from Discord")

    async def on_message(self, message):
        if message.author.id == self.user.id:
            return

        # Verify if a limit with DeepL has been reached
        if not deepl_usage.any_limit_reached:
            # Get the translation language of the server
            cur.execute("SELECT language FROM languages WHERE guild_id = ?;", (message.guild.id,))
            translation_language = cur.fetchone()

            # Verify that the administrators have set up a language
            if translation_language:
                text_language: str = detect(message.content)
                text_language = text_language.upper()

                # if text_translated.detected_source_lang != translation_language[0]:
                if text_language != translation_language[0]:    # To try
                    text_translated = translator.translate_text(message.content, target_lang=translation_language[0])
                    await message.reply(
                        "{0} said in {1}: \n\n \"{2}\"".format(message.author, text_translated.detected_source_lang,
                                                               text_translated.text))
        else:
            await message.reply("Sorry, I am not able to translate this at the moment :'(")
            print("Character usage count: {0}".format(deepl_usage.character))
            logging.log(logging.WARNING, "Character usage count: {0}".format(deepl_usage.character))

    async def on_guild_remove(self, guild):
        """Remove guild's users from the database when the guild is removed or the bot is kicked / banned"""
        cur.execute("DELETE FROM languages WHERE guild_id = ?;", (guild.id,))
        con.commit()

    async def new_log(self):
        """Make a new log file"""
        now = datetime.datetime.now()
        # s_logger = logging.StreamHandler()
        # f_logger = logging.FileHandler(filename="logs/{0}.log".format(now.strftime("%Y-%m-%d %H:%M:%S")), encoding="utf-8")
        logging.basicConfig(filename="logs/{0}.log".format(now.strftime("%Y-%m-%d %H:%M:%S")), encoding="utf-8",
                            level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s',
                            datefmt="%Y-%m-%d %H:%M:%S")
        await asyncio.sleep(86400)  # Wait a day
        # Things to do here


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
    /translate [string] - Send a message in a specific language
    Made by Tristan Bony --> https://www.tristanbony.me
    """, ephemeral=True)


@tree.command(name="set_language", description="Set the language you don't want to be translated")
@app_commands.choices(language=languages)
async def set_language(interaction: discord.Interaction, language: Choice[str]):
    cur.execute("INSERT OR REPLACE INTO languages (guild_id, language) VALUES (?, ?);",
                (interaction.guild.id, language.value))
    con.commit()

    await interaction.response.send_message("You have added {0} language.".format(language.name), ephemeral=True)


@tree.command(name="translate", description="Send a translated text")
@app_commands.choices(language=languages)
async def translate(interaction: discord.Interaction, language: Choice[str], text: str):
    await interaction.response.send_message(
        "{0} wants to say something in {1}:\n{2}".format(interaction.user.mention, language.name,
                                                         translator.translate_text(text, target_lang=language.value)))


client.run(discord_token)
