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

# --- EXPANDED CREATIVE LISTS ---

CATEGORIES = [
    "about", "age", "bubbles", "bye", "cat", "children", "confused", "dreams", 
    "feeling", "filter", "food", "glass", "glass_tap", "gravel", "greeting", 
    "happy", "hungry", "joke", "light", "lonely", "love", "meaning", "memory", 
    "music", "name", "noise", "outside", "pain", "plants", "poop", "reflection", 
    "sand", "seasons", "sick", "size", "sleep", "smart", "tank", "taste", 
    "temp_cold", "temp_hot", "time", "tired", "tv", "visitors", "water", "weather"
]

SHIELD_PHRASES = [
    "Do not worry! Fishy is keeping your eyes safe from these messages! 🐟🛡️",
    "Blub blub! I ate that message! Quick, look at me instead! 🫧",
    "Message intercepted! Fishy thought it was fish food. Nom nom! 🐠",
    "Nothing to see here! Just Fishy swimming around the tank! 🌊",
    "Splash! I deleted that! This is MY tank! 🐡",
    "Target acquired and swallowed whole! 🦈🫧",
    "Ad blocker deployed! I am a fish, not an ad! 🪸",
    "Yum! That promo tasted like stale algae. 🌿🐟",
    "Sweeping the tank clean of spam! Swish swish! 🧹🌊",
    "Gulp! That message has been sent to the bottom of the ocean. ⚓🫧",
    "Protecting the ecosystem from unwanted text! 🦀🛡️",
    "Snatching that right out of the water! 🦑💧",
    "Oops! I accidentally ate the ad while hunting for flakes. 🐡🫧",
    "The currents have washed that message away! 🌊🐚",
    "Chewed it up and spat it into the filter! ⚙️🐟",
    "Spam belongs in a can, not my tank! *chomp* 🐠🥫",
    "Intercepted by the best guardian in the reef! 🪸🦈",
    "My tank, my rules! And I say NO to that message. 🐡🌊",
    "Burp! Excuse me, that advertisement was very filling. 🫧🐟",
    "Hiding your eyes behind my fins! 🐠🫧"
]

NOMMING_SOUNDS = [
    "*nom nom nom*... 🫧",
    "Crunch crunch... eating the data kelp 🪸",
    "Glub glub... chewing on the bytes 🐟",
    "Slurp... delicious text 🐡",
    "Nibble nibble... 🦐",
    "*chomp*... needs more salt 🌊",
    "Munching on the coral... 🪸🫧",
    "Bloop... tasty spam 🐠",
    "Snack time! *crunch* 🦀",
    "Swallowing that one whole! 🦈",
    "Chewing on the seaweed... 🌿🫧",
    "*smack smack*... surprisingly nutritious! 🐟",
    "Gulp! Down the hatch! 💧",
    "Snip snap! Pinching the words into pieces! 🦀",
    "Glug glug... washing it down with tank water 🌊",
    "Tastes like pixel flakes! 🐠🫧",
    "*nibbles gently*... not bad! 🐡",
    "Munch crunch munch... 🪸",
    "Gobbling it up before the snails get it! 🐌💧",
    "A fine meal for a hungry fish! 🐟🌿",
    "*chew chew*... spitting out the bad parts 🫧",
    "Slorp! Slurping up the sentences like worms! 🪱🐠",
    "Biting into the text... *CRACK* 🐚",
    "Nomming away at the digital algae! 🌿🐡",
    "Yummy! A delicious snack! 🦐🫧",
    "*crunching loudly* 🦈",
    "Devouring the evidence! 🐙💧",
    "Mmmmm... crunchy! 🦀",
    "Feasting in the deep! 🌊🐟",
    "Taking little bites... *nom*... *nom* 🐠",
    "Chomping down hard! 🐡🪸"
]

# --- TANK CHANNEL STORAGE LOGIC ---
TANKS_FILE = "tanks.json"

def load_tanks():
    if os.path.exists(TANKS_FILE):
        with open(TANKS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_tanks(tanks_set):
    with open(TANKS_FILE, "w") as f:
        json.dump(list(tanks_set), f)

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

    async def get_guppylm_response(self, prompt, channel=None):
        nom_task = None
        
        # If a channel is provided, start the background nomming loop!
        if channel:
            async def nom_loop():
                try:
                    while True:
                        # Wait 5 to 10 seconds between sounds
                        await asyncio.sleep(random.uniform(5, 10))
                        await channel.send(random.choice(NOMMING_SOUNDS))
                except asyncio.CancelledError:
                    # This happens when the AI is finished and we cancel the task
                    pass
            
            # Start the loop concurrently
            nom_task = asyncio.create_task(nom_loop())

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
        finally:
            # Guarantee the nomming stops when the AI finishes
            if nom_task:
                nom_task.cancel()

    async def on_message(self, message):
        if message.author == self.user:
            return

        # ---------------------------------------------------------
        # 1. DYNAMIC FISHY TANK INTERCEPTOR LOGIC
        # ---------------------------------------------------------
        if message.channel.id in tank_channels:
            
            # 1. Reply to protect the user
            await message.reply(random.choice(SHIELD_PHRASES))

            # 2. Eat the message
            try:
                await message.delete()
            except discord.Forbidden:
                print("WARNING: Fishy needs 'Manage Messages' permission to delete the message!")
            except discord.NotFound:
                pass 

            # 3. Start generating response AND nomming sounds
            random_category = random.choice(CATEGORIES)
            
            async with message.channel.typing():
                # We pass message.channel here to trigger the nomming loop!
                ai_response = await self.get_guppylm_response(random_category, channel=message.channel)
                await message.channel.send(f"**Topic: {random_category}**\n{ai_response}")
            
            return

        # ---------------------------------------------------------
        # 2. NORMAL CHAT LOGIC (Anywhere else)
        # ---------------------------------------------------------
        if "fishy" in message.content.lower():
            clean_prompt = message.content.lower().replace("fishy", "").strip()
            if not clean_prompt:
                clean_prompt = "hello"

            async with message.channel.typing():
                # Nomming in normal channels too!
                ai_response = await self.get_guppylm_response(clean_prompt, channel=message.channel)
                await message.channel.send(ai_response)


intents = discord.Intents.default()
intents.message_content = True

client = FishBot(intents=intents)

# ---------------------------------------------------------
# 3. SLASH COMMANDS
# ---------------------------------------------------------

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
    # Pass the interaction channel to start nomming sounds!
    ai_response = await client.get_guppylm_response(category, channel=interaction.channel)
    await interaction.followup.send(f"**Topic: {category}**\n{ai_response}")

@client.tree.command(name="toggle_tank", description="Toggle whether this channel acts as a Fishy Tank (eats messages).")
@app_commands.default_permissions(manage_channels=True)
async def toggle_tank(interaction: discord.Interaction):
    channel_id = interaction.channel.id
    
    if channel_id in tank_channels:
        tank_channels.remove(channel_id)
        save_tanks(tank_channels)
        await interaction.response.send_message("🫧 Blub! I have stopped eating messages here. This channel is no longer a Fishy Tank.")
    else:
        tank_channels.add(channel_id)
        save_tanks(tank_channels)
        await interaction.response.send_message("🌊 Splash! This channel is now a Fishy Tank! I will eat messages here and protect everyone's eyes.")

# ---------------------------------------------------------

if not TOKEN:
    print("ERROR: DISCORD_BOT_TOKEN environment variable not set!")
    sys.exit(1)

client.run(TOKEN)
