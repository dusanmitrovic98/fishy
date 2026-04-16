import discord
import random
import os
import asyncio
from aiohttp import web

# --- THE CONFIG ---
TARGET_CHANNEL_ID = 1492658172240986142
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
# Set a password in Render env vars, or it defaults to 'fishy123'.
DASHBOARD_PASS = os.getenv('DASHBOARD_PASS', 'fishy123') 

REPLIES = [
    "*Giggles and hides behind a sea fan* Hehe, a shark was chasing me, but I led him straight to your message! GULP! 🦈🫧",
    "Is this organic? *Pokes message with a fin* Tastes like... delete button. *Wiggles tail excitedly* 🐡✨",
    "Shhh! I'm pretending to be a rock so the ads don't find me... *Munch* Too late! I ate it! 🪨🐡",
    "Nom nom! That message tasted like high-quality fish flakes with a hint of spicy seaweed! 🐠🫧",
    "Gulp! I sent that one straight to the bottom of the Mariana Trench. It's too dark for spam down there! ⚓🌊",
    "Chomp! I thought that was a juicy sea worm. My mistake! *Wiggles fins happily* 🪱🐟",
    "Splash! Your message has been washed away by a giant whale sneeze! 🐋💦",
    "Bubble shield activated! *Blub blub* No ads are getting past my beautiful coral reef! 🫧🪸",
    "Burp! Excuse me, I'm a very hungry fish today. That message was quite filling! 🐡💨",
    "Target acquired and swallowed whole! *Zips around the tank in a circle* Nom! 🦈🫧",
    "I've buried that text deep under the seafloor sand. The crabs are guarding it now! 🐚🦀",
    "That message was too salty for this tank. *Patooey!* Spat it into the filter! 🐡💦",
    "Feeding the spam to the hungry anemones! They say thank you for the snack! 🪸🍴",
    "The kraken has claimed your message for the deep! *Giggles* He's such a picky eater. 🐙⚓",
    "My tank, my rules! And I say NO to that message. *Blows a big bubble of defiance* 🐠🚫",
    "Intercepted by the best guardian in the reef! *Flexes tiny fish muscles* 🪸🦈",
    "Dragging that promo down to the abyss. It’s glowing now, how pretty! 🕳️✨",
    "Snatched that right out of the water! *Happy tail slaps* 🦑💧",
    "Deployed the ink cloud! You can't see the spam anymore, only my cute face! 🐙💨",
    "Washed it right out with a big splash! *Dives into the gravel* 🐳💦",
    "Nothing to see here! Just a very innocent fishy swimming around! 🌊🐡",
    "Spam belongs in a can, not my beautiful tank! *Crunch crunch crunch* 🐠🥫",
    "I'm keeping your eyes safe! *Nom nom nom* No need to thank me! 🐟🛡️",
    "That text looked like a shiny lure, but I'm too smart for that! *Chomp* 🎣🐠",
    "Cleaning the tank! One message at a time! *Squeaky cleaning noises* 🧹🫧",
    "Swallowed that one like a pelican! *Hiccup* 🦆🐟",
    "Snip snap! I pinched that message into tiny digital pieces! 🦀✂️",
    "Tastes like digital algae. A bit crunchy but very delicious! 🌿🐠",
    "Hiding your eyes behind my fins until the bad text is gone! *Peek-a-blub!* 🐠👐",
    "Bloop... another one bites the dust. *Swims away giggling* 🫧💀",
    "A shark! *Dives into a sunken treasure chest* He missed me, but I didn't miss that ad! GULP! 🏴‍☠️🐠",
    "Is it food? *Nibbles gently* Oh, it's just spam. *Devours it anyway* 😋🐡",
    "Making a bubble nest out of your deleted messages! *Blub blub blub* 🫧🪺",
    "The currents are extra strong today! They just swept that message away! 🌊🌬️",
    "Wait! *Stops mid-swim* I thought I saw a shrimp... oh, it was just a promo. MUNCH! 🦐🐟",
    "Surprise attack! *Lunges at the message* Got it! 🦈💥",
    "I'm a piranha in a guppy's body! *Chomp chomp* 🐟🦷",
    "Sending this message to the Bermuda Triangle. It’ll never be found! 📐🌊",
    "I've turned that message into fish poop. You're welcome! 💩🐠",
    "*Taps on the glass* Hey! Look at me, not that spam! *Munch* 🪟🐡",
    "Riding a sea turtle to victory! We trampled your message! 🐢🏇",
    "That text tasted like a rotten jellyfish. *Shudders and giggles* 🪼🤢",
    "I'm a magic fish! Watch me make this message... DISAPPEAR! 🎩🐠",
    "Singing a sea shanty while I eat your ads! *Da-da-da-blub!* 🎶🫧",
    "Too much text! My fins are tired! *Eats it to save energy* 🐠💤",
    "Doing a backflip! *Splashes everywhere* Oh, and I ate that ad too. 🐬✨",
    "I'm the king of this tank! No trespassing for promos! 👑🐟",
    "Found a shiny pearl! *Hides it* And I lost your message! 🐚💖",
    "*Blows a bubble ring* Perfect shot! The message is gone! 🫧🎯",
    "I'm playing tag with the filter intake! *Slurp* It ate your message! ⚙️🌊",
    "Are you watching? I'm gonna do a big gulp! *GULP* 🐡😮",
    "My tummy is a black hole for bad messages! 🕳️🐠",
    "The dolphins told me a secret... they said eat this message! 🐬🤫",
    "I'm a tiny dragon of the sea! *Fireless burp* MUNCH! 🐉🌊",
    "Exploring the deep sea! *Finds message and eats it* Found treasure! 💎🐟",
    "I'm a pufferfish! *Puffs up* See how big I am? Big enough to eat that! 🐡🎈",
    "Is this a love letter? No? Then it's fish food! 💌🐠",
    "Sprinting through the kelp forest! *Zips past and eats the ad* 🌿🏃",
    "I'm a ninja fish! *Smoke bomb* Now you see the ad, now you don't! 🥷🫧",
    "Wrestling with a giant squid! I'm winning! *Nom* 🦑💪",
    "I've turned that message into a bubble. *Pop!* Now it's gone. 🫧📍",
    "Looking for Nemo! *Finds your message instead* I'll eat this while I wait. 🤡🐟",
    "I'm a detective! *Investigates message* Conclusion: Tasty. 🕵️‍♂️🐠",
    "Surfing on a high-speed current! *Grabbed the ad on the way* 🏄‍♂️🌊",
    "I'm a treasure hunter! *Eats message* This wasn't gold, but it was crunchy. 🪙🐡",
    "Playing hide and seek! *Hides in your delete logs* Hehe! 🙈🫧",
    "I'm a pilot fish! Flying through the water! *Zoom* ✈️🐟",
    "*Does a little dance* Left fin, right fin, now MUNCH! 💃🐠",
    "I'm a starfish! Just kidding, I have fins! *Nom nom* 🌟🐡",
    "The sea snails are slow, but I'm fast! *Grab and gulp* 🐌💨",
    "I'm an electric eel! *Zap!* Just kidding, but I still ate it. ⚡🐍",
    "Writing my own story in the bubbles... yours was a boring one. *Delete* 📖🫧",
    "I'm a hammerhead! *Bonks message and eats it* 🔨🦈",
    "The mermaids told me to keep this place clean. 🧜‍♀️✨",
    "I'm a submarine! *Ping* Target destroyed! ⚓️🚢",
    "Is it a bird? Is it a plane? No, it's a very full fish! 🐦🐠",
    "I'm a pirate! *Yarrr* Hand over the booty—I mean, the spam! 🏴‍☠️🐡",
    "Doing a belly flop! *Splash* Ad gone! 🐬💥",
    "I'm a seahorse! *Gallops through the water* Nom! 🐎🌊",
    "The coral is whispering... it says 'thank you for the snack'. 🪸👂",
    "I'm a blowfish! *Blub* I just blew your message away! 🌬️🐠",
    "Searching for the lost city of Atlantis! *Eats ad* Not there. 🏺🌊",
    "I'm a speed-swimmer! Want to see me do it again? *Nom* 🏊‍♂️🐟",
    "I've turned the ad into a seashell. *Listen*... it says 'delete'. 🐚👂",
    "I'm a moonfish! *Glows* Eating in the dark is fun! 🌕🐡",
    "I'm a butterfly fish! *Flutters fins* Munch munch! 🦋🐠",
    "The tide is coming in! *Swish* Ad washed out! 🌊👋",
    "I'm a parrotfish! *Crunch* Tastes like coral... I mean, spam. 🦜🐠",
    "I'm a lionfish! Fear my roar—I mean, my bubbles! 🦁🫧",
    "I've hidden the ad in a message bottle and thrown it away! 🍾🌊",
    "I'm an angel fish! Doing my good deed for the day! 👼🐟",
    "The reef is happy now that the spam is gone! 🪸💖",
    "I'm a triggerfish! *Pulling the trigger on that ad* 🔫🐠",
    "I'm a flying fish! *Leaps out of water* Look at me go! ✈️🐟",
    "The sea anemones are giggling at how fast I ate that! 🪸😂",
    "I'm a monkfish! *Meditates and then MUNCH* 🧘‍♂️🐡",
    "I'm a stonefish! Don't step on me—or the ads I've hidden! 🪨🐡",
    "The ocean is vast, but I'll find every ad you post! 🌊🔍",
    "I'm a clownfish! *Tells a joke* Why did the ad cross the reef? To get eaten! 🤡🍴",
    "Final boss of the tank! You shall not pass! *Munch* 🛡️🐠"
]

# --- THE BOT CLASS ---
class FishyBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create a command tree for the bot
        self.tree = discord.app_commands.CommandTree(self)

    async def on_ready(self):
        print(f"Fishy logged in as {self.user} and is swimming in {TARGET_CHANNEL_ID}")
        
        # This tells Discord to delete all global slash commands for this bot
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

# --- GLOBAL STATE MANAGER ---
bot_task = None
bot_instance = None
is_bot_running = False

async def run_bot():
    global bot_instance, is_bot_running
    is_bot_running = True
    intents = discord.Intents.default()
    intents.message_content = True
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
    port = int(os.environ.get("PORT", 8080))
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
