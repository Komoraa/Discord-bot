import asyncio
from config import *
import discord
from discord.ext import commands, tasks
import datetime
from datetime import timedelta

intents = discord.Intents.default()
intents.message_content = True
intents.guild_scheduled_events = True
bot = commands.Bot(command_prefix='!', intents=intents)

utc = datetime.timezone.utc
ping_time = datetime.time(hour=7, minute=0, tzinfo=utc) #its utc+0 time

def get_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as file:
            temperature = file.read()
        return round(int(temperature) / 1000, 2)
    except Exception as e:
        return f"Error reading temperature: {e}"

async def send_event_details(events,ctx):
    sorted_events = sorted(events, key=lambda event: event.start_time)
    event_details=[]
    ghost_ping_list=[] #embeds can't ping so need for workaround
    now=datetime.datetime.now(utc)
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
        if event.start_time > (now + timedelta(days=7)):
            embed.add_field(name="Date", value=f"<t:{date}:F>")
        else:
            embed.add_field(name="Date", value=f"<t:{date}:R>")
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

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()
    if 'MyCog' not in bot.cogs:
        await bot.add_cog(MyCog(bot))
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

@bot.hybrid_command(description="List all scheduled events in this server")
async def list_events(ctx):
    guild = ctx.guild
    if not guild:
        await ctx.send("This command can only be used in a server.")
        return

    if ctx.interaction:
        await ctx.interaction.response.defer()

    events = await guild.fetch_scheduled_events()
    if not events:
        await ctx.send("No scheduled events found.")
        return

    await send_event_details(events,ctx)

bot.run(token)