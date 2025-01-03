from config import *
import discord
#from discord.ext import tasks, commands

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
def get_temp():
    try:
        # Read the temperature from the Raspberry Pi's system file
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as file:
            temp = file.read()
        # Return the temperature in Celsius
        return round(int(temp) / 1000, 2)  # Convert from millidegrees Celsius to Celsius
    except Exception as e:
        return f"Error reading temperature: {e}"

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    # Don't let the bot reply to itself
    if message.author == client.user:
        return

    # Command to get the temperature
    if message.content.startswith('!temp'):
        temp = get_temp()
        await message.channel.send(f"The current Raspberry Pi temperature is {temp}°C")

client.run(token)