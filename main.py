from config import *
import discord
from discord.ext import commands, tasks
import datetime, calendar, time
from datetime import timedelta

intents = discord.Intents.default()
intents.message_content = True
intents.guild_scheduled_events = True
bot = commands.Bot(command_prefix='!', intents=intents)

utc = datetime.timezone.utc
ping_time = datetime.time(hour=7, minute=0, tzinfo=utc) #remember its utc+0 time

def get_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as file:
            temperature = file.read()
        return round(int(temperature) / 1000, 2)
    except Exception as e:
        return f"Error reading temperature: {e}"

async def get_event_details(events):
    event_details=[]
    for event in events:
        users_list = []
        async for user in event.users():
            users_list.append(user.mention)
        date=calendar.timegm(time.strptime(str(event.start_time)[:-6], '%Y-%m-%d %H:%M:%S'))
        users_list_string=''.join(users_list)
        details = f"**{event.name}**\n> Date: <t:{date}:R> \n> Participants: {users_list_string}"
        event_details.append(details)
    return event_details

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.my_task.start()

    def cog_unload(self):
        if self.my_task and self.my_task.is_running():
            self.my_task.cancel()

    @tasks.loop(time=ping_time)
    async def my_task(self):
        today=datetime.datetime.now(utc)
        channel = self.bot.get_channel(channel_id)
        if channel:
            guild = self.bot.get_guild(server_id)
            events = await guild.fetch_scheduled_events()
            if today.weekday() == 0 and events: #set day 0 is monday
                await channel.send(f"**Cotygodniowa przypominajka** \n\n")
            else:
                soon=today+timedelta(days=2)
                events = [event for event in events if event.start_time <= soon]
                if events:
                    await channel.send(f"**Nadchodzące wydarzenia** \n\n")
            event_details = await get_event_details(events)
            if event_details:
                await channel.send("\n\n".join(event_details))

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.add_cog(MyCog(bot))

@bot.command()
async def temp(ctx):
    temperature = get_temp()
    await ctx.send(f"The current Raspberry Pi temperature is {temperature}°C")

@bot.command()
async def ping(ctx):
    user = await bot.fetch_user(165763943552253952)
    await ctx.send(f"{user.mention}")

@bot.command()
async def sens_istnienia(ctx):
    await ctx.send(f"https://cdn.discordapp.com/attachments/913365628285489182/1034156679689928724/caption.gif?ex=677e0d36&is=677cbbb6&hm=272607044a4cef0477c1ff3df1d4573b1789acfd366889db41b0d7e45e6c249e&")

@bot.command()
async def list_events(ctx):
    guild = ctx.guild
    if not guild:
        await ctx.send("This command can only be used in a server.")
        return

    events = guild.scheduled_events
    if not events:
        await ctx.send("No scheduled events found.")
        return

    event_details = await get_event_details(events)
    await ctx.send("\n\n".join(event_details))

bot.run(token)