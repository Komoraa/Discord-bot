from config import *
import discord
from discord.ext import commands
import os
import sys
import time

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix='!', intents=intents)
def get_temp():
    try:
        # Read the temperature from the Raspberry Pi's system file
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as file:
            temp = file.read()
        # Return the temperature in Celsius
        return round(int(temp) / 1000, 2)  # Convert from millidegrees Celsius to Celsius
    except Exception as e:
        return f"Error reading temperature: {e}"

def restart_bot():
    print("Restarting bot...")
    os.execv(__file__, ['python3'] + sys.argv)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.command()
async def temp(ctx):
    temperature = get_temp()
    await ctx.send(f"The current Raspberry Pi temperature is {temperature}°C")

while True:
    try:
        client.run(token)
    except Exception as e:
        print(f"Error occurred: {e}")
        time.sleep(5)  # Wait a bit before restarting
        restart_bot()