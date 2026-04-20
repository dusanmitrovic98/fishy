import discord
import random
import os
import asyncio
from aiohttp import web

# --- THE CONFIG ---
TARGET_CHANNEL_ID = 1492658172240986142
MINOR_ROLE_ID = 1495196051123077341

# Pull from Environment Variables (Render or .env)
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DASHBOARD_PASS = os.getenv('DASHBOARD_PASS', 'fishy123')

REPLIES = [
    "*Giggles and hides behind a sea fan* Hehe, a shark was chasing me, but I led him straight to your message! GULP! 🦈🫧",
    "Is this organic? *Pokes message with a fin* Tastes like... delete button. *Wiggles tail excitedly* 🐡✨",
    "Shhh! I'm pretending to be a rock so the ads don't find me... *Munch* Too late! I ate it! 🪨🐡",
    "Nom nom! That message tasted like high-quality fish flakes with a hint of spicy seaweed! 🐠🫧",
    # ... (Keep the rest of your 70+ replies here. I've shortened it for readability, 
    # but paste your full REPLIES list back in here!) ...
    "Final boss of the tank! You shall not pass! *Munch* 🛡️🐠"
]

# --- THE BOT CLASS ---
class FishyBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = discord.app_commands.CommandTree(self)

    async def on_ready(self):
        print(f"Fishy logged in as {self.user} and is swimming in {TARGET_CHANNEL_ID}")
        self.tree.clear_commands(guild=None)
        await self.tree.sync()
        print("Cleared all old slash commands from Discord!")

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.channel.id == TARGET_CHANNEL_ID:
            try:
                await message.reply(random.choice(REPLIES))
                await message.delete()
            except Exception as e:
                print(f"Error eating message: {e}")

    # --- ADD THIS NEW EVENT ---
    async def on_member_update(self, before, after):
        # Check if they just received the minor role
        had_role_before = any(role.id == MINOR_ROLE_ID for role in before.roles)
        has_role_now = any(role.id == MINOR_ROLE_ID for role in after.roles)

        if not had_role_before and has_role_now:
            print(f"Detected minor role added to {after.name} ({after.id}). Initiating ban sequence.")
            
            # 1. Try to DM the user
            try:
                await after.send("I am sorry but for safety reasons we do not allow minors in our server")
            except discord.Forbidden:
                # This happens if the user has DMs disabled or blocked the bot.
                print(f"Could not DM {after.name}. They have DMs disabled. Proceeding to ban.")
            except Exception as e:
                print(f"Unexpected error DMing {after.name}: {e}")

            # 2. Ban the user (Banning automatically kicks them from the server)
            try:
                await after.ban(reason="Safety reasons: Assigned the minor role.")
                print(f"Successfully banned {after.name}.")
            except discord.Forbidden:
                print(f"ERROR: I don't have permission to ban {after.name}! Check my role hierarchy/permissions.")
            except Exception as e:
                print(f"Unexpected error banning {after.name}: {e}")

# --- GLOBAL STATE MANAGER ---
bot_task = None
bot_instance = None
is_bot_running = False

async def run_bot():
    global bot_instance, is_bot_running
    is_bot_running = True
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    bot_instance = FishyBot(intents=intents)
    
    try:
        print("Starting bot...")
        await bot_instance.start(TOKEN)
    except asyncio.CancelledError:
        print("Bot shutdown requested...")
    except Exception as e:
        print(f"Bot encountered an error: {e}")
    finally:
        is_bot_running = False
        print("Bot has successfully disconnected.")

# --- WEB DASHBOARD ROUTES ---
async def handle_home(request):
    """Serves the HTML Dashboard"""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FishyBot Dashboard</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1e1e2e; color: #cdd6f4; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .container { background-color: #313244; padding: 30px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); text-align: center; width: 350px; }
            h1 { margin-top: 0; color: #89b4fa; }
            .status { margin: 20px 0; font-size: 18px; font-weight: bold; display: flex; align-items: center; justify-content: center; gap: 10px; }
            .dot { height: 15px; width: 15px; background-color: #f38ba8; border-radius: 50%; display: inline-block; }
            .dot.online { background-color: #a6e3a1; box-shadow: 0 0 10px #a6e3a1; }
            input[type="password"] { width: 100%; padding: 10px; margin-bottom: 20px; border-radius: 6px; border: 1px solid #45475a; background-color: #181825; color: #fff; box-sizing: border-box; }
            button { width: 48%; padding: 10px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; transition: 0.2s; color: #11111b; }
            button:disabled { opacity: 0.5; cursor: not-allowed; }
            .btn-start { background-color: #a6e3a1; }
            .btn-start:hover:not(:disabled) { background-color: #94cc90; }
            .btn-stop { background-color: #f38ba8; }
            .btn-stop:hover:not(:disabled) { background-color: #d97d96; }
            .controls { display: flex; justify-content: space-between; }
            #message { margin-top: 15px; font-size: 14px; color: #f9e2af; height: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🐟 FishyBot Control</h1>
            <div class="status">
                <span id="status-dot" class="dot"></span>
                <span id="status-text">Checking Status...</span>
            </div>
            <input type="password" id="password" placeholder="Enter Dashboard Password">
            <div class="controls">
                <button class="btn-start" id="btn-start" onclick="sendAction('start')">START BOT</button>
                <button class="btn-stop" id="btn-stop" onclick="sendAction('stop')">STOP BOT</button>
            </div>
            <div id="message"></div>
        </div>

        <script>
            async function fetchStatus() {
                try {
                    const res = await fetch('/api', { method: 'POST', body: JSON.stringify({ action: 'status' }) });
                    const data = await res.json();
                    
                    const dot = document.getElementById('status-dot');
                    const text = document.getElementById('status-text');
                    const btnStart = document.getElementById('btn-start');
                    const btnStop = document.getElementById('btn-stop');

                    if (data.running) {
                        dot.classList.add('online');
                        text.innerText = "Bot is ONLINE";
                        btnStart.disabled = true;
                        btnStop.disabled = false;
                    } else {
                        dot.classList.remove('online');
                        text.innerText = "Bot is OFFLINE";
                        btnStart.disabled = false;
                        btnStop.disabled = true;
                    }
                } catch (e) {
                    document.getElementById('status-text').innerText = "Server Unreachable";
                }
            }

            async function sendAction(action) {
                const pwd = document.getElementById('password').value;
                const msg = document.getElementById('message');
                msg.innerText = "Sending command...";
                
                try {
                    const res = await fetch('/api', {
                        method: 'POST',
                        body: JSON.stringify({ action: action, password: pwd })
                    });
                    
                    if (res.status === 401) {
                        msg.innerText = "❌ Incorrect Password!";
                        return;
                    }
                    
                    const data = await res.json();
                    msg.innerText = "✅ Command successful!";
                    setTimeout(() => msg.innerText = "", 3000);
                    fetchStatus();
                } catch (e) {
                    msg.innerText = "❌ Network Error";
                }
            }

            // Fetch status on load and every 5 seconds
            fetchStatus();
            setInterval(fetchStatus, 5000);
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def handle_api(request):
    """Handles Start/Stop/Status requests from the dashboard"""
    global bot_task, bot_instance, is_bot_running
    
    try:
        data = await request.json()
    except:
        # Pinger services like UptimeRobot sending empty GET/POST requests
        return web.json_response({'running': is_bot_running})

    # Public route to check status (used by JS to update UI)
    if data.get('action') == 'status':
        return web.json_response({'running': is_bot_running})

    # Protected routes (Require password)
    if data.get('password') != DASHBOARD_PASS:
        return web.json_response({'error': 'Unauthorized'}, status=401)

    action = data.get('action')
    
    if action == 'start':
        if not is_bot_running:
            bot_task = asyncio.create_task(run_bot())
            return web.json_response({'status': 'started'})
        return web.json_response({'status': 'already running'})

    elif action == 'stop':
        if is_bot_running and bot_instance:
            await bot_instance.close()
            # Note: We don't wait for the task to fully exit here so the web request doesn't hang
            return web.json_response({'status': 'stopping'})
        return web.json_response({'status': 'already stopped'})

    return web.json_response({'error': 'Bad Request'}, status=400)


# --- MAIN EXECUTION ---
async def main():
    global bot_task

    # 1. Setup the Web Server
    app = web.Application()
    app.router.add_get('/', handle_home)
    app.router.add_post('/api', handle_api)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8081))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web Dashboard running on port {port}")

    # 2. Start the Discord Bot in the background by default
    print("Auto-starting Discord bot...")
    bot_task = asyncio.create_task(run_bot())

    # 3. Keep the web server running forever
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    # Fix for some environments where event loops clash
    asyncio.run(main())
