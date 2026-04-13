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
    if not uri: return ""
    try:
        scheme_split = uri.split("://", 1)
        if len(scheme_split) != 2: return uri
        scheme, rest = scheme_split[0], scheme_split[1]
        if "@" not in rest: return uri
        creds, host_part = rest.rsplit("@", 1)
        if ":" not in creds: return uri
        user, pwd = creds.split(":", 1)
        user_quoted = urllib.parse.quote_plus(urllib.parse.unquote(user))
        pwd_quoted = urllib.parse.quote_plus(urllib.parse.unquote(pwd))
        return f"{scheme}://{user_quoted}:{pwd_quoted}@{host_part}"
    except Exception:
        return uri

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
MONGO_URI = escape_mongo_uri(os.getenv('MONGO_URI'))
ERROR_WEBHOOK_URL = "https://discord.com/api/webhooks/1493251412304330783/N8E3t_u-tSYBIP9k2KRlj1due8opyZDXXWhZwcdSVRwTE2h0vVsLy4m6s4upit6-mjNn"

# ==========================================
# KEEP YOUR CATEGORIES, SHIELD_PHRASES, AND NOMMING_SOUNDS HERE!
# Do not delete your local arrays!
# ==========================================

# --- MONGODB SETUP ---
tank_channels = set()
shield_only_channels = set()
enabled_noms = set() # This replaces 'disabled_noms'. Since it's empty, nomming is OFF by default everywhere.

if MONGO_URI:
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    db = mongo_client.fishy_db
    settings_col = db.settings
else:
    settings_col = None

async def send_error_to_webhook(error_title, error_message):
    async with ClientSession() as session:
        payload = {
            "embeds":[{
                "title": f"❌ Fishy Error: {error_title}",
                "description": f"```python\n{error_message[:1900]}```",
                "color": 15158332,
                "footer": {"text": "Fishy Tank Emergency System"}
            }]
        }
        try: await session.post(ERROR_WEBHOOK_URL, json=payload)
        except Exception: pass

async def load_settings_from_db():
    global tank_channels, shield_only_channels, enabled_noms
    if settings_col is None: return  
    try:
        doc = await settings_col.find_one({"id": "global_config"})
        if doc:
            tank_channels = set(doc.get("tank_channels",[]))
            shield_only_channels = set(doc.get("shield_only_channels", []))
            enabled_noms = set(doc.get("enabled_noms",[]))
    except Exception as e:
        await send_error_to_webhook("Database Load Failure", traceback.format_exc())

async def sync_to_db():
    if settings_col is None: return  
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

# --- WEB SERVER ---
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
            # ONLY runs if the channel was explicitly toggled ON
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
                process = await asyncio.create_subprocess_exec(
                    sys.executable, '-m', 'guppylm', 'chat', '--prompt', prompt,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120.0)

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

        if cid in tank_channels:
            try: await message.delete()
            except: pass
            msg = await message.channel.send(random.choice(SHIELD_PHRASES))
            async with message.channel.typing():
                cat = random.choice(CATEGORIES)
                resp = await self.get_guppylm_response(cat, channel=message.channel)
                # FIX: Removed the "Topic:" prefix so it only sends the AI's response
                await msg.edit(content=resp)
            return

        elif cid in shield_only_channels:
            try: await message.delete()
            except: pass
            await message.channel.send(random.choice(SHIELD_PHRASES), delete_after=10) 
            return

        if "fishy" in message.content.lower():
            p = message.content.lower().replace("fishy", "").strip() or "hello"
            async with message.channel.typing():
                resp = await self.get_guppylm_response(p, channel=message.channel)
                await message.reply(resp)

intents = discord.Intents.default()
intents.message_content = True
client = FishBot(intents=intents)

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
