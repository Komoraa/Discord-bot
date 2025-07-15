import asyncio
from config import *
import discord
from discord.ext import commands, tasks
import datetime
from datetime import timedelta
from mcstatus import JavaServer
import os
import json
from zoneinfo import ZoneInfo
import subprocess
import requests
import random

intents = discord.Intents.default()
intents.message_content = True
intents.guild_scheduled_events = True
intents.voice_states = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

utc = datetime.timezone.utc
ping_time = datetime.time(hour=7, minute=0, tzinfo=utc) #its utc+0 time
JSON_FILE = 'event_overrides.json'

def load_overrides():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_overrides(overrides):
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(overrides, f, indent=4, ensure_ascii=False)

overrides = load_overrides()

def get_overrided_events(events):
    now = datetime.datetime.now(utc)
    result = []

    for event in events:
        event_id = str(event.id)
        override = overrides.get(event_id, {})
        override_start = override.get('start_time')

        if override_start:
            try:
                parsed_override = datetime.datetime.fromisoformat(override_start)
                if parsed_override > now:
                    event.start_time = parsed_override
            except Exception:
                pass

        result.append(event)

    return result
def get_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as file:
            temperature = file.read()
        return round(int(temperature) / 1000, 2)
    except Exception as e:
        return f"Error reading temperature: {e}"

class ServerStatusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.server_status_message = None  # Message to update player count
        self.last_status = None  # Track last known server status
        self.bot.loop.create_task(self.send_initial_message())
        self.check_server_status.start()  # Start the background task

    async def send_initial_message(self):
        """Send an initial status message when the bot starts."""
        await self.bot.wait_until_ready()  # Ensure bot is ready before sending
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            print("Error: Channel not found.")
            return

        embed = discord.Embed(
            title="⌛ Checking Minecraft Server Status...",
            description="Please wait while we fetch the latest server status.",
            color=discord.Color.blue()
        )

        self.server_status_message = await channel.send(embed=embed)

    
    def cog_unload(self):
        """Stop the task when the cog is unloaded."""
        if self.check_server_status.is_running():
            self.check_server_status.cancel()

    @tasks.loop(seconds=300)
    async def check_server_status(self):
        """Checks the server status and updates messages accordingly."""
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            print("Error: Channel not found.")
            return
        
        try:
            server = JavaServer.lookup(miencraft_ip)
            status = server.status()
            server_online = True
            player_count = status.players.online
            max_players = status.players.max

            embed = discord.Embed(
                title="✅ Minecraft Server is Online",
                description=f"**Players Online:** {player_count}/{max_players}",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url="https://static.wikia.nocookie.net/minecraft_gamepedia/images/1/12/Grass_Block_JE2.png/revision/latest?cb=20200830142618")
            embed.set_footer(text="Status updates every 5 minutes")

        except:
            server_online = False
            embed = discord.Embed(
                title="❌ Minecraft Server is Offline",
                description="**The server is currently unreachable.**",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url="https://cdn-icons-png.freepik.com/512/4225/4225690.png")
            embed.set_footer(text="Status updates every 5 minutes")

        if self.last_status != server_online:
        # If status changed, send a new message
            self.server_status_message = await channel.send(embed=embed)
        else:
            await self.server_status_message.edit(embed=embed)
        # Update last known status
        self.last_status = server_online

    @check_server_status.before_loop
    async def before_check(self):
        """Wait until the bot is ready before starting the task."""
        await self.bot.wait_until_ready()


async def send_event_details(events, ctx):
    sorted_events = sorted(events, key=lambda event: event.start_time)
    event_details=[]
    ghost_ping_list=[] #embeds can't ping so need for workaround

    for event in sorted_events:
        users_list = []

        async for user in event.users():
            users_list.append(user.mention +', ')

        date=event.start_time
        date=int(date.timestamp())

        users_list_string=''.join(users_list)
        users_list_string=users_list_string[:-2] # remove last ", "

        embed = discord.Embed(
            #title=event.name,
            color=discord.Color.blue(),
            description=f"**[{event.name}]({event.url})**"
        )

        if event.cover_image:
            embed.set_image(url=event.cover_image)
        if event.description:
            embed.add_field(name="Description", value=event.description, inline=False)
        embed.add_field(name="Participants", value=users_list_string)
        embed.add_field(name="Date", value=f"<t:{date}:F>")
        ghost_ping_list.append(users_list) #eh
        event_details.append(embed)
    for event in event_details:
        await ctx.send(embed=event)
    #workaround pinging
    if ghost_ping_list:
        ghost_message= await ctx.send(f"{ghost_ping_list}")
        await ghost_message.delete()

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.my_task.start()

    def cog_unload(self):
        if self.my_task and self.my_task.is_running():
            self.my_task.cancel()

    @tasks.loop(time=ping_time)
    async def my_task(self):
        now=datetime.datetime.now(utc)
        channel = self.bot.get_channel(channel_id)
        if channel:
            guild = self.bot.get_guild(server_id)
            events = await guild.fetch_scheduled_events()
            events = get_overrided_events(events)
            #somehow api maneged sent me event from the past so i guess i need to check for this apparently
            events = [event for event in events if event.start_time > now] 

            if now.weekday() == 0 and events: #set day 0 is monday
                await channel.send(f"**Cotygodniowa przypominajka** \n\n")
            else:
                soon=now+timedelta(days=2)
                events = [event for event in events if event.start_time <= soon]
                if events:
                    await channel.send(f"**Nadchodzące wydarzenia** \n\n")
            await send_event_details(events,channel)

class MemeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.my_task.start()
        self.meme_queue = [] 

    def cog_unload(self):
        if self.my_task and self.my_task.is_running():
            self.my_task.cancel()

    @tasks.loop(minutes = 243)
    async def my_task(self):
        if not self.meme_queue:
            response = requests.get('https://meme-api.com/gimme/dankmemes/40')
            data = response.json()
            self.meme_queue = [meme['url'] for meme in data.get('memes', [])]
        channel = self.bot.get_channel(meme_channel_id)
        meme_url = self.meme_queue.pop(0)
        await channel.send(meme_url)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()
    if 'MyCog' not in bot.cogs:
        await bot.add_cog(MyCog(bot))
    if 'ServerStatusCog' not in bot.cogs:
        await bot.add_cog(ServerStatusCog(bot))
    if 'MemeCog' not in bot.cogs:
        await bot.add_cog(MemeCog(bot))
@bot.hybrid_command()
async def temp(ctx):
    temperature = get_temp()
    await ctx.send(f"The current Raspberry Pi temperature is {temperature}°C")

@bot.hybrid_command(description="Mordo dawaj na ligę")
async def ping(ctx, member: discord.Member, number: int):
    if number < 1:
        number = 1
    if number > 10:
        number = 10
    for i in range (number):
        await ctx.send(f"{member.mention}")
        await asyncio.sleep(1)

@bot.hybrid_command(description="Why is this still here")
async def sens_istnienia(ctx):
    await ctx.send(f"https://cdn.discordapp.com/attachments/913365628285489182/1034156679689928724/caption.gif?ex=677e0d36&is=677cbbb6&hm=272607044a4cef0477c1ff3df1d4573b1789acfd366889db41b0d7e45e6c249e&")

@bot.hybrid_command(description="Fisk")
async def fisk(ctx):
    await ctx.send(f"https://tenor.com/view/the-kingpin-wilson-fisk-the-kingpin-wilson-fisk-marvel-comics-spider-man-gif-27081152")

@bot.hybrid_command(description="ksiF")
async def ksif(ctx):
    await ctx.send("https://cdn.discordapp.com/attachments/913365628285489182/1388092602846281758/reverse.gif")

@bot.hybrid_command(description="List all scheduled events in this server")
async def list_events(ctx):
    guild = ctx.guild
    if not guild:
        await ctx.send("This command can only be used in a server.")
        return

    if ctx.interaction:
        await ctx.interaction.response.defer()

    events = await guild.fetch_scheduled_events()
    #events=get_overrided_events(events)
    if not events:
        await ctx.send("No scheduled events found.")
        return

    await send_event_details(events,ctx)

@bot.hybrid_command(name='event_date_fuckery', description='format: "%Y-%m-%d %H:%M"', guild=discord.Object(id=server_id))
async def event_date_fuckery(ctx, event_id: str, start_time: str = None):
    overrides[event_id] = overrides.get(event_id, {})

    if ctx.interaction:
        await ctx.interaction.response.defer()

    if start_time:
        try:
            # Użycie ZoneInfo do poprawnej obsługi czasu letniego i zimowego
            poland_tz = ZoneInfo("Europe/Warsaw")
            parsed_time_pl = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M").replace(tzinfo=poland_tz)
            parsed_time_utc = parsed_time_pl.astimezone(utc)

            now = datetime.datetime.now(utc)
            if parsed_time_utc < now:
                await ctx.send(f'Nie można ustawić przeszłej daty dla wydarzenia {event_id}.')
                return
            
            # Zapis do pliku w UTC
            overrides[event_id]['start_time'] = parsed_time_utc.isoformat()
            save_overrides(overrides)

            # Pobranie nazwy wydarzenia
            guild = ctx.guild
            event_name = event_id
            if guild:
                try:
                    event = await guild.fetch_scheduled_event(int(event_id))
                    event_name = event.name
                except Exception:
                    pass

            # Wyświetlenie użytkownikowi daty w czasie polskim
            formatted_time_pl = parsed_time_pl.strftime("%Y-%m-%d %H:%M")
            await ctx.send(f'Nadpisano datę dla wydarzenia **{event_name}** na **{formatted_time_pl}**.')
        
        except ValueError:
            await ctx.send('Niepoprawny format daty. Użyj formatu YYYY-MM-DD HH:MM.')
            return

@bot.hybrid_command(name="schody", description="Użytkownik był nieśmieszny.")
async def rotacja(ctx: commands.Context, member: discord.Member):
    guild = ctx.guild
    channels = [guild.get_channel(cid) for cid in VOICE_CHANNEL_IDS]

    if not member.voice or not member.voice.channel:
        await ctx.reply("❌ Użytkownik nie jest na żadnym kanale głosowym.", ephemeral=True)
        return

    start_channel = member.voice.channel
    if start_channel.id not in VOICE_CHANNEL_IDS:
        await ctx.reply("❌ Kanał użytkownika nie znajduje się na liście rotacji.", ephemeral=True)
        return

    await ctx.defer()

    start_index = VOICE_CHANNEL_IDS.index(start_channel.id)

    # na samo dno
    for i in range(start_index + 1, len(channels)):
        await member.move_to(channels[i])
        await asyncio.sleep(1)

    # i do góry
    for i in range(len(channels) - 2, start_index - 1, -1):
        await member.move_to(channels[i])
        await asyncio.sleep(1)

    await ctx.followup.send(f"Następnym razem bądź smieszniejszy")

#funny
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    role_name = "Don't Starve Together"
    role = discord.utils.get(message.guild.roles, name = role_name)

    if role in message.role_mentions or "Don't Starve Together" in message.content:
        await message.channel.send("https://tenor.com/view/kekwtf-gif-18599263")

    meme_channel = bot.get_channel(meme_channel_id)
    if message.channel == meme_channel and random.randint(0, 5) == 0 and message.attachments:
        await message.add_reaction(bot.get_emoji(675110692113874974))

@bot.tree.command()
async def play(interaction: discord.Interaction):
    user = interaction.user

    # Sprawdź, czy użytkownik jest w kanale głosowym
    if not user.voice or not user.voice.channel:
        await interaction.response.send_message("Musisz być na kanale głosowym.")
        return

    channel = user.voice.channel
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)

    if voice_client is None:
        voice_client = await channel.connect()
    elif voice_client.channel != channel:
        await voice_client.move_to(channel)

    if voice_client.is_playing():
        await interaction.response.send_message("Już coś gra.")
        return

    def after_playing(error):
        if error:
            print("Błąd odtwarzania:", error)
        else:
            print("Odtwarzanie zakończone.")

    try:
        source = discord.FFmpegPCMAudio("song.mp3")
        voice_client.play(source, after=after_playing)
    except Exception as e:
        print("Exception:", e)
        await interaction.response.send_message("Wystąpił błąd przy odtwarzaniu.")
        return

    await interaction.response.send_message("Odtwarzam `song.mp3`...")

    while voice_client.is_playing():
        await asyncio.sleep(1)

    await voice_client.disconnect()

@bot.hybrid_command(name="restart", description="Restart and update")
@commands.is_owner() 
async def updatebot(ctx):
    await ctx.reply("Restart")
    await asyncio.sleep(2)
    subprocess.Popen(['bash', 'update_bot.sh'])

bot.run(token)