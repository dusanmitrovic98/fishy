import discord
from discord import app_commands
import asyncio
import sys
import re
import traceback
import os
import random
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
        # Create a command tree for slash commands
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Start the dummy web server to keep Render happy
        self.loop.create_task(start_dummy_server())
        # Sync slash commands to Discord
        await self.tree.sync()
        print("Slash commands synced!")

    async def on_ready(self):
        print(f'Blub blub! Logged in as {self.user}')

    # Helper function to generate AI responses
    async def get_guppylm_response(self, prompt):
        try:
            # Use the official working PyTorch CLI command
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

            # Remove terminal color codes
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            out_str = ansi_escape.sub('', out_str)

            final_lines = []
            for line in out_str.split('\n'):
                clean_line = line.strip()

                # Filter out the model loading text and user echo
                if "GuppyLM loaded" in clean_line or clean_line.startswith("You>"):
                    continue

                # Grab only the fish's response
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
        # Ignore messages from ourselves
        if message.author == self.user:
            return

        # ID of the "Fishy Tank" channel
        TARGET_PROMO_CHANNEL = 1492658172240986142

        # ---------------------------------------------------------
        # 1. FISHY TANK INTERCEPTOR LOGIC
        # ---------------------------------------------------------
        if message.channel.id == TARGET_PROMO_CHANNEL:
            
            shield_phrases = [
                "Do not worry! Fishy is keeping your eyes safe from these messages! 🐟🛡️",
                "Blub blub! I ate that message! Quick, look at me instead! 🫧",
                "Message intercepted! Fishy thought it was fish food. Nom nom! 🐠",
                "Nothing to see here! Just Fishy swimming around the tank! 🌊",
                "Splash! I deleted that! This is MY tank! 🐡"
            ]

            # 1. Reply to the message first
            await message.reply(random.choice(shield_phrases))

            # 2. DELETE the original message so no one sees it!
            try:
                await message.delete()
            except discord.Forbidden:
                print("WARNING: Fishy needs 'Manage Messages' permission to delete the message!")
            except discord.NotFound:
                pass 

            # 3. Trigger the AI using a random category from your list
            random_category = random.choice(CATEGORIES)
            ai_prompt = f"Talk to me about {random_category}."
            
            async with message.channel.typing():
                ai_response = await self.get_guppylm_response(ai_prompt)
                await message.channel.send(ai_response)
            
            # Stop here so we don't trigger the regular chat logic
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
# 3. /FISHY SLASH COMMAND WITH AUTOCOMPLETE SELECTOR
# ---------------------------------------------------------
async def category_autocomplete(interaction: discord.Interaction, current: str):
    """Filters the 47 categories based on what the user is typing in the slash command"""
    return [
        app_commands.Choice(name=cat, value=cat)
        for cat in CATEGORIES if current.lower() in cat.lower()
    ][:25] # Discord only allows returning 25 items at a time

@client.tree.command(name="fishy", description="Make Fishy talk about a specific category!")
@app_commands.autocomplete(category=category_autocomplete)
async def fishy_slash(interaction: discord.Interaction, category: str):
    # If the user types something not in the list manually, handle it gently
    if category not in CATEGORIES:
        await interaction.response.send_message(f"Blub! '{category}' isn't a valid category. Try selecting from the list!", ephemeral=True)
        return

    # Acknowledge the command immediately because AI generation takes time
    await interaction.response.defer()
    
    # Generate response based on the selected category
    prompt = f"Talk to me about {category}."
    ai_response = await client.get_guppylm_response(prompt)
    
    # Send the final result
    await interaction.followup.send(f"**Topic: {category}**\n{ai_response}")


if not TOKEN:
    print("ERROR: DISCORD_BOT_TOKEN environment variable not set!")
    sys.exit(1)

client.run(TOKEN)
