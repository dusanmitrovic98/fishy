import discord
import random
import os
import sys

# Hardcoded Target
TARGET_CHANNEL_ID = 1492187958206533834
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Creative Oceanic Phrases
FISHY_REPLIES = [
    "Nom nom! That message tasted like high-quality fish flakes! 🐠🫧",
    "Gulp! I sent that one straight to the bottom of the Mariana Trench. ⚓🌊",
    "Chomp! I thought that was a juicy sea worm. My mistake! 🪱🐟",
    "Splash! Your message has been washed away by a giant wave. 🐋🌊",
    "Bubble shield activated! No spam is getting past my reef! 🫧🪸",
    "Burp! Excuse me, I'm a very hungry fish today. 🐡💨",
    "Target acquired and swallowed whole! Nom! 🦈🫧",
    "I've buried that text deep under the seafloor sand. 🐚🏝️",
    "That message was too salty for this tank. *Patooey!* 🐡💦",
    "Camouflage mode: ON. I've blended that message into the rocks. 🪨🐠",
    "Feeding the spam to the hungry anemones! 🪸🍴",
    "The kraken has claimed your message for the deep! 🐙⚓",
    "My tank, my rules! And I say NO to that message. 🐠🚫",
    "Intercepted by the best guardian in the reef! 🪸🦈",
    "Dragging that promo down to the abyss. Bye bye! 🕳️🐟",
    "Snatched that right out of the water! 🦑💧",
    "Deployed the ink cloud! You can't see the spam anymore! 🐙💨",
    "Washed it right out with a big splash! 🐳💦",
    "Nothing to see here! Just Fishy swimming around the tank! 🌊🐡",
    "Oops! I accidentally chewed that up while looking for coral. 🪸🐟",
    "Spam belongs in a can, not my beautiful tank! *Crunch* 🐠🥫",
    "The currents have swept that message to a different ocean. 🌊🚢",
    "I'm keeping your eyes safe! *Nom nom nom* 🐟🛡️",
    "That text looked like a shiny lure, but I ate it anyway! 🎣🐠",
    "Cleaning the tank! One message at a time! 🧹🫧",
    "Swallowed that one like a pelican! 🦆🐟",
    "Snip snap! I pinched that message into tiny pieces! 🦀✂️",
    "Tastes like digital algae. Delicious! 🌿🐠",
    "Hiding your eyes behind my fins until the bad text is gone! 🐠👐",
    "Bloop... another one bites the dust. 🫧💀"
]

class FishyBot(discord.Client):
    async def on_ready(self):
        print(f'Fishy is hungry. Monitoring channel: {TARGET_CHANNEL_ID}')

    async def on_message(self, message):
        # Ignore self
        if message.author == self.user:
            return

        # ONLY this specific channel
        if message.channel.id == TARGET_CHANNEL_ID:
            # 1. Reply first
            try:
                await message.reply(random.choice(FISHY_REPLIES))
                
                # 2. Delete original AFTER replying
                await message.delete()
            except Exception as e:
                print(f"Error eating message: {e}")

# Set intents (Needs Message Content to see what to delete)
intents = discord.Intents.default()
intents.message_content = True

client = FishyBot(intents=intents)

if not TOKEN:
    print("Error: DISCORD_BOT_TOKEN not set.")
    sys.exit(1)

client.run(TOKEN)
