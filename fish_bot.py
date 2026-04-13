import discord
from discord import app_commands
import asyncio
import sys
import re
import traceback
import os
import random
import urllib.parse
from aiohttp import web, ClientSession
from motor.motor_asyncio import AsyncIOMotorClient

def escape_mongo_uri(uri: str) -> str:
    """Safely escapes the username and password in a MongoDB URI to fix PyMongo crashes."""
    if not uri: return ""
    try:
        scheme_split = uri.split("://", 1)
        if len(scheme_split) != 2: return uri
        scheme, rest = scheme_split[0], scheme_split[1]
        
        if "@" not in rest: return uri
        
        # Split at the last '@' to cleanly separate credentials from the host
        creds, host_part = rest.rsplit("@", 1)
        if ":" not in creds: return uri
            
        user, pwd = creds.split(":", 1)
        # Unquote first to prevent double-encoding, then quote properly
        user_quoted = urllib.parse.quote_plus(urllib.parse.unquote(user))
        pwd_quoted = urllib.parse.quote_plus(urllib.parse.unquote(pwd))
        
        return f"{scheme}://{user_quoted}:{pwd_quoted}@{host_part}"
    except Exception:
        return uri

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
MONGO_URI = escape_mongo_uri(os.getenv('MONGO_URI'))
ERROR_WEBHOOK_URL = "https://discord.com/api/webhooks/1493251412304330783/N8E3t_u-tSYBIP9k2KRlj1due8opyZDXXWhZwcdSVRwTE2h0vVsLy4m6s4upit6-mjNn"

# --- CATEGORIES ---
CATEGORIES =["about", "age", "bubbles", "bye", "cat", "children", "confused", "dreams", "feeling", "filter", "food", "glass", "glass_tap", "gravel", "greeting", "happy", "hungry", "joke", "light", "lonely", "love", "meaning", "memory", "music", "name", "noise", "outside", "pain", "plants", "poop", "reflection", "sand", "seasons", "sick", "size", "sleep", "smart", "tank", "taste", "temp_cold", "temp_hot", "time", "tired", "tv", "visitors", "water", "weather"]

# --- CREATIVE OCEANIC ARRAYS ---
SHIELD_PHRASES =[
    "Do not worry! Fishy is keeping your eyes safe from these messages! 🐟🛡️",
    "Blub blub! I ate that message! Quick, look at me instead! 🫧",
    "Message intercepted! Fishy thought it was fish food. Nom nom! 🐠",
    "Nothing to see here! Just Fishy swimming around the tank! 🌊",
    "Splash! I deleted that! This is MY tank! 🐡",
    "Bubble barrier activated! No ads getting through this reef! 🫧🪸",
    "I’ve buried that message deep under the seafloor sand. 🐚🏝️",
    "Gulp! I thought that was a juicy worm. My mistake! 🪱🐠",
    "The current swept that away before I could even blink. 🌊🐟",
    "Engaging the bioluminescent distraction protocol! 🐙✨",
    "Washed it right out with a big splash! 🐋🌊",
    "That message was too salty for this tank. *patooey!* 🐡💦",
    "Dragging that promo down to the abyss. ⚓🕳️",
    "Hiding your eyes behind my fins until the bad text is gone! 🐠🫧",
    "Spam belongs in a can, not my tank! *chomp* 🐠🥫",
    "Intercepted by the best guardian in the reef! 🪸🦈",
    "Burp! Excuse me, that advertisement was very filling. 🫧🐟",
    "Sweeping the tank clean of spam! Swish swish! 🧹🌊",
    "Snatching that right out of the water! 🦑💧",
    "Deployed the ink cloud! You can't see the spam anymore! 🐙💨",
    "Camouflage mode: ON. I've blended that message into the rocks. 🪨🐡",
    "Feeding the spam to the hungry anemones! 🪸🍴",
    "The kraken has claimed that message for the deep! 🐙⚓",
    "Diverting the current! That text is heading for another server. 🌊🚢"
]

NOMMING_SOUNDS =[
    "*nom nom nom*... 🫧",
    "Crunch crunch... eating the data kelp 🪸",
    "Glub glub... chewing on the bytes 🐟",
    "Slurp... delicious text 🐡",
    "Nibble nibble... 🦐",
    "*chomp*... needs more salt 🌊",
    "*Pop pop pop*... popping the spam bubbles! 🫧",
    "Chewing on some tasty metadata flakes... 🐟",
    "*Tail splash*... just tidying up the gravel! 🌊",
    "Munching on a digital shrimp... *crunch* 🦐",
    "Bloop... blop... swallowing the bytes... 💧",
    "*Click click*... talking to the dolphins while I eat... 🐬",
    "Feasting on the seaweed forest... 🌿🐠",
    "Cracking open a cold text-shell... 🐚",
    "Gurgle gurgle... the filter is extra hungry today! ⚙️🫧",
    "*Chomp*... oh, that one was spicy! 🌶️🐠",
    "Nibbling at the edges of the conversation... 🐟",
    "Taking a big bite out of the ocean floor! 🏝️🦀",
    "*Slurp slurp*... drinking up the ink! 🦑",
    "Devouring the evidence! 🐙💧",
    "*Munch munch*... tastes like fresh plankton! 🌊🦠",
    "Sifting through the sand for more words... 🏖️🐠",
    "Grinding up the message like a parrotfish! 🐡🪸",
    "Is this organic? *chew chew* 🌿🐟"
]

# --- MONGODB SETUP ---
tank_channels = set()
shield_only_channels = set()
enabled_noms = set()

if MONGO_URI:
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    db = mongo_client.fishy_db
    settings_col = db.settings
else:
    settings_col = None

async def send_error_to_webhook(error_title, error_message):
    """Sends a detailed error report to the provided Discord Webhook."""
    async with ClientSession() as session:
        payload = {
            "embeds":[{
                "title": f"❌ Fishy Error: {error_title}",
                "description": f"```python\n{error_message[:1900]}```",
                "color": 15158332, # Red
                "footer": {"text": "Fishy Tank Emergency System"}
            }]
        }
        try:
            await session.post(ERROR_WEBHOOK_URL, json=payload)
        except Exception:
            pass

async def load_settings_from_db():
    global tank_channels, shield_only_channels, enabled_noms
    if not settings_col: return
    try:
        doc = await settings_col.find_one({"id": "global_config"})
        if doc:
            tank_channels = set(doc.get("tank_channels",[]))
            shield_only_channels = set(doc.get("shield_only_channels", []))
            enabled_noms = set(doc.get("enabled_noms",[]))
    except Exception as e:
        await send_error_to_webhook("Database Load Failure", traceback.format_exc())

async def sync_to_db():
    if not settings_col: return
    try:
        await settings_col.update_one(
            {"id": "global_config"},
            {"$set": {
                "tank_channels": list(tank_channels),
                "shield_only_channels": list(shield_only_channels),
                "enabled_noms": list(enabled_noms)
            }}, upsert=True
        )
    except Exception as e:
        await send_error_to_webhook("Database Sync Failure", traceback.format_exc())

# --- WEB SERVER (Render) ---
async def handle_ping(request): return web.Response(text="Fishy is alive.")
async def start_dummy_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080))).start()

class FishBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = app_commands.CommandTree(self)
        self.ai_lock = asyncio.Lock()

    async def setup_hook(self):
        self.loop.create_task(start_dummy_server())
        await load_settings_from_db()
        await self.tree.sync()

    async def on_ready(self): 
        print(f'Logged in as {self.user}')

    async def get_guppylm_response(self, prompt, channel=None):
        nom_task = None
        async with self.ai_lock:
            # Nomming is now OFF by default, explicitly check inclusion list
            if channel and channel.id in enabled_noms:
                async def nom_loop():
                    try:
                        while True:
                            await asyncio.sleep(random.uniform(5, 10))
                            await channel.send(random.choice(NOMMING_SOUNDS))
                    except asyncio.CancelledError: pass
                nom_task = asyncio.create_task(nom_loop())

            process = None
            try:
                # Natively runs GuppyLM PyTorch Chat Workflow without ONNX
                process = await asyncio.create_subprocess_exec(
                    sys.executable, '-m', 'guppylm', 'chat', '--prompt', prompt,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=45.0)

                if process.returncode != 0:
                    err_msg = stderr.decode('utf-8', errors='ignore')
                    await send_error_to_webhook("GuppyLM Subprocess Crash", err_msg)
                    return "🫧 *cough* My brain feels like it's in a whirlpool. (AI Error)"

                out = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])').sub('', stdout.decode('utf-8', errors='ignore'))
                final = [l.split("Guppy>")[-1].strip() for l in out.split('\n') if "Guppy>" in l]
                return "\n".join(final)[:1900] or "blub. (no output from model)"
            except asyncio.TimeoutError:
                if process: process.kill()
                return "🫧 I thought too hard and ran out of bubbles. (AI Timeout)"
            except Exception:
                await send_error_to_webhook("AI Processing Error", traceback.format_exc())
                return "🫧 *Glub*... Error in the tank."
            finally:
                if nom_task: nom_task.cancel()

    async def on_message(self, message):
        if message.author == self.user: return
        cid = message.channel.id

        # 1. Full Tank Mode (AI)
        if cid in tank_channels:
            try: await message.delete()
            except: pass
            
            # Send the shield phrase then cleanly EDIT it to the AI response (Prevents "Reply to deleted message" visual bugs)
            msg = await message.channel.send(random.choice(SHIELD_PHRASES))
            async with message.channel.typing():
                cat = random.choice(CATEGORIES)
                resp = await self.get_guppylm_response(cat, channel=message.channel)
                await msg.edit(content=f"**Topic: {cat}**\n{resp}")
            return

        # 2. Shield Mode (Quiet)
        elif cid in shield_only_channels:
            try: await message.delete()
            except: pass
            # Auto deletes shield notifications after 10s so it doesn't clutter chat
            await message.channel.send(random.choice(SHIELD_PHRASES), delete_after=10) 
            return

        # 3. Mentioned Chat
        if "fishy" in message.content.lower():
            p = message.content.lower().replace("fishy", "").strip() or "hello"
            async with message.channel.typing():
                resp = await self.get_guppylm_response(p, channel=message.channel)
                await message.reply(resp)

intents = discord.Intents.default()
intents.message_content = True
client = FishBot(intents=intents)

# --- SLASH COMMANDS ---
@client.tree.command(name="toggle_tank", description="AI mode: Eats messages and makes Fishy talk.")
@app_commands.default_permissions(manage_channels=True)
async def toggle_tank(interaction: discord.Interaction):
    cid = interaction.channel.id
    shield_only_channels.discard(cid)
    if cid in tank_channels:
        tank_channels.remove(cid)
        msg = "🫧 Tank Mode: **OFF**."
    else:
        tank_channels.add(cid)
        msg = "🌊 Tank Mode: **ON**. I am now eating ads and talking about the reef!"
    await sync_to_db(); await interaction.response.send_message(msg)

@client.tree.command(name="toggle_shield", description="Quiet mode: Eats messages but Fishy stays quiet.")
@app_commands.default_permissions(manage_channels=True)
async def toggle_shield(interaction: discord.Interaction):
    cid = interaction.channel.id
    tank_channels.discard(cid)
    if cid in shield_only_channels:
        shield_only_channels.remove(cid)
        msg = "🛡️ Shield Mode: **OFF**."
    else:
        shield_only_channels.add(cid)
        msg = "🛡️ Shield Mode: **ON**. I will delete messages quietly without AI spam."
    await sync_to_db(); await interaction.response.send_message(msg)

@client.tree.command(name="toggle_nomming", description="Toggle sounds while Fishy is thinking.")
@app_commands.default_permissions(manage_channels=True)
async def toggle_nom(interaction: discord.Interaction):
    cid = interaction.channel.id
    if cid in enabled_noms:
        enabled_noms.remove(cid)
        msg = "🫧 Nomming: **OFF**. *Silent bubbles...*"
    else:
        enabled_noms.add(cid)
        msg = "🐟 Nomming: **ON**. *Chomp chomp!*"
    await sync_to_db(); await interaction.response.send_message(msg)

if __name__ == "__main__":
    if not TOKEN or not MONGO_URI:
        print("❌ Set your DISCORD_BOT_TOKEN and MONGO_URI Environment Variables!")
        sys.exit(1)
    client.run(TOKEN)
