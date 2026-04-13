import discord
from discord import app_commands
import asyncio
import sys
import re
import traceback
import os
import random
import json
from aiohttp import web

TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Your provided list of categories
CATEGORIES = [
    "about", "age", "bubbles", "bye", "cat", "children", "confused", "dreams", 
    "feeling", "filter", "food", "glass", "glass_tap", "gravel", "greeting", 
    "happy", "hungry", "joke", "light", "lonely", "love", "meaning", "memory", 
    "music", "name", "noise", "outside", "pain", "plants", "poop", "reflection", 
    "sand", "seasons", "sick", "size", "sleep", "smart", "tank", "taste", 
    "temp_cold", "temp_hot", "time", "tired", "tv", "visitors", "water", "weather"
]

# --- TANK CHANNEL STORAGE LOGIC ---
TANKS_FILE = "tanks.json"

def load_tanks():
    """Loads the list of Fishy Tank channel IDs from a JSON file."""
    if os.path.exists(TANKS_FILE):
        with open(TANKS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_tanks(tanks_set):
    """Saves the list of Fishy Tank channel IDs to a JSON file."""
    with open(TANKS_FILE, "w") as f:
        json.dump(list(tanks_set), f)

# Load the saved tank channels into memory
tank_channels = load_tanks()
# ----------------------------------

# --- DUMMY WEB SERVER FOR RENDER ---
async def handle_ping(request):
    return web.Response(text="Blub! Fishy is alive (PyTorch version).")

async def start_dummy_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Dummy web server started on port {port}")
# -----------------------------------

class FishBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.loop.create_task(start_dummy_server())
        await self.tree.sync()
        print("Slash commands synced!")

    async def on_ready(self):
        print(f'Blub blub! Logged in as {self.user}')

    async def get_guppylm_response(self, prompt):
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, '-m', 'guppylm', 'chat', '--prompt', prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()
            out_str = stdout.decode('utf-8', errors='ignore').strip()
            err_str = stderr.decode('utf-8', errors='ignore').strip()

            if process.returncode != 0:
                error_msg = f"Crash! Exit code: {process.returncode}\nStderr:\n{err_str}"
                return f"```{error_msg[:1900]}```"

            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            out_str = ansi_escape.sub('', out_str)

            final_lines = []
            for line in out_str.split('\n'):
                clean_line = line.strip()
                if "GuppyLM loaded" in clean_line or clean_line.startswith("You>"):
                    continue
                if "Guppy>" in clean_line:
                    clean_line = clean_line.split("Guppy>")[-1].strip()
                if clean_line:
                    final_lines.append(clean_line)

            response = "\n".join(final_lines)
            if not response:
                response = f"blub. output was empty. Error check:\n{err_str[:500]}"

            return response[:1900]

        except Exception as e:
            tb = traceback.format_exc()
            return f"Python Error:\n```python\n{tb[:1900]}\n```"

    async def on_message(self, message):
        if message.author == self.user:
            return

        # ---------------------------------------------------------
        # 1. DYNAMIC FISHY TANK INTERCEPTOR LOGIC
        # ---------------------------------------------------------
        # Check if the channel is saved in our tank_channels list
        if message.channel.id in tank_channels:
            
            shield_phrases = [
                "Do not worry! Fishy is keeping your eyes safe from these messages! 🐟🛡️",
                "Blub blub! I ate that message! Quick, look at me instead! 🫧",
                "Message intercepted! Fishy thought it was fish food. Nom nom! 🐠",
                "Nothing to see here! Just Fishy swimming around the tank! 🌊",
                "Splash! I deleted that! This is MY tank! 🐡"
            ]

            await message.reply(random.choice(shield_phrases))

            try:
                await message.delete()
            except discord.Forbidden:
                print("WARNING: Fishy needs 'Manage Messages' permission to delete the message!")
            except discord.NotFound:
                pass 

            random_category = random.choice(CATEGORIES)
            
            async with message.channel.typing():
                ai_response = await self.get_guppylm_response(random_category)
                await message.channel.send(ai_response)
            
            return

        # ---------------------------------------------------------
        # 2. NORMAL CHAT LOGIC (Anywhere else)
        # ---------------------------------------------------------
        if "fishy" in message.content.lower():
            clean_prompt = message.content.lower().replace("fishy", "").strip()
            if not clean_prompt:
                clean_prompt = "hello"

            async with message.channel.typing():
                ai_response = await self.get_guppylm_response(clean_prompt)
                await message.channel.send(ai_response)

intents = discord.Intents.default()
intents.message_content = True

client = FishBot(intents=intents)

# ---------------------------------------------------------
# 3. SLASH COMMANDS
# ---------------------------------------------------------

# The Autocomplete function for /fishy
async def category_autocomplete(interaction: discord.Interaction, current: str):
    return [
        app_commands.Choice(name=cat, value=cat)
        for cat in CATEGORIES if current.lower() in cat.lower()
    ][:25] 

@client.tree.command(name="fishy", description="Make Fishy talk about a specific category!")
@app_commands.autocomplete(category=category_autocomplete)
async def fishy_slash(interaction: discord.Interaction, category: str):
    if category not in CATEGORIES:
        await interaction.response.send_message(f"Blub! '{category}' isn't a valid category. Try selecting from the list!", ephemeral=True)
        return

    await interaction.response.defer()
    ai_response = await client.get_guppylm_response(category)
    await interaction.followup.send(f"**Topic: {category}**\n{ai_response}")

# New Command: /toggle_tank
@client.tree.command(name="toggle_tank", description="Toggle whether this channel acts as a Fishy Tank (eats messages).")
@app_commands.default_permissions(manage_channels=True) # Only admins/mods can see and use this!
async def toggle_tank(interaction: discord.Interaction):
    channel_id = interaction.channel.id
    
    if channel_id in tank_channels:
        # If it's already a tank, remove it
        tank_channels.remove(channel_id)
        save_tanks(tank_channels)
        await interaction.response.send_message("🫧 Blub! I have stopped eating messages here. This channel is no longer a Fishy Tank.")
    else:
        # If it's not a tank, add it
        tank_channels.add(channel_id)
        save_tanks(tank_channels)
        await interaction.response.send_message("🌊 Splash! This channel is now a Fishy Tank! I will eat messages here and protect everyone's eyes.")

# ---------------------------------------------------------

if not TOKEN:
    print("ERROR: DISCORD_BOT_TOKEN environment variable not set!")
    sys.exit(1)

client.run(TOKEN)
