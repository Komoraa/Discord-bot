from config import *
import discord
from discord.ext import commands, tasks
import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.guild_scheduled_events = True
client = commands.Bot(command_prefix='!', intents=intents)

utc = datetime.timezone.utc
ping_time = datetime.time(hour=17, minute=0, tzinfo=utc)

def get_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as file:
            temperature = file.read()
        return round(int(temperature) / 1000, 2)
    except Exception as e:
        return f"Error reading temperature: {e}"

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.my_task.start()

    def cog_unload(self):
        self.my_task.cancel()

    @tasks.loop(time=ping_time)
    async def my_task(self):
        now = datetime.datetime.now(utc)
        if now.weekday() == 2: #set day 0 is monday
            channel = self.bot.get_channel(channel_id)
            if channel:
                guild = self.bot.get_guild(server_id)
                events = await guild.fetch_scheduled_events()
                event_details = []
                for event in events:
                    users_list = []
                    async for user in event.users():
                        users_list.append(user.mention)
                    details = f"**{event.name}**\n> Starts: {event.start_time}\n> Ends: {event.end_time or 'N/A'}\n> User_list: {users_list}"
                    event_details.append(details)
                await channel.send(f"**Cotygodniowa przypominajka** \n\n")
                await channel.send("\n\n".join(event_details))

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.command()
async def temp(ctx):
    temperature = get_temp()
    await ctx.send(f"The current Raspberry Pi temperature is {temperature}°C")

@client.command()
async def ping(ctx):
    user = await client.fetch_user(165763943552253952)
    await ctx.send(f"{user.mention}")

@client.command()
async def sens_istnienia(ctx):
    await ctx.send(f"https://cdn.discordapp.com/attachments/913365628285489182/1034156679689928724/caption.gif?ex=677e0d36&is=677cbbb6&hm=272607044a4cef0477c1ff3df1d4573b1789acfd366889db41b0d7e45e6c249e&")

@client.command()
async def list_events(ctx):
    guild = ctx.guild
    if not guild:
        await ctx.send("This command can only be used in a server.")
        return

    events = guild.scheduled_events
    if not events:
        await ctx.send("No scheduled events found.")
        return

    event_details = []
    for event in events:
        users_list = []
        async for user in event.users():
            users_list.append(user.mention)
        details = f"**{event.name}**\n> Starts: {event.start_time}\n> Ends: {event.end_time or 'N/A'}\n> User_list: {users_list}"
        event_details.append(details)

    await ctx.send("\n\n".join(event_details))

client.run(token)