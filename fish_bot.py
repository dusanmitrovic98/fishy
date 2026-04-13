import discord
import asyncio
import sys
import re
import traceback
import os
import random
from aiohttp import web

TOKEN = os.getenv('DISCORD_BOT_TOKEN')

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
    async def setup_hook(self):
        # Start the dummy web server to keep Render happy
        self.loop.create_task(start_dummy_server())

    async def on_ready(self):
        print(f'Blub blub! Logged in as {self.user}')

    # Helper function to generate AI responses to prevent duplicate code
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

        TARGET_PROMO_CHANNEL = 1492658172240986142

        # ---------------------------------------------------------
        # 1. BUMPER BOT INTERCEPTOR LOGIC
        # ---------------------------------------------------------
        # If a bot posts in the specific channel...
        if message.channel.id == TARGET_PROMO_CHANNEL and message.author.bot:
            
            # Fun, creative anti-spam phrases
            shield_phrases = [
                "Do not worry! Fishy is keeping your eyes safe from these ads! 🐟🛡️",
                "Blub blub! Quick, look at me instead of this promo! 🫧",
                "Spam detected! Fishy is eating the advertisement. Nom nom! 🐠",
                "Nothing to see here! Just Fishy swimming over the ads to protect the server! 🌊",
                "Ad blocker deployed! I am a fish, not an ad! 🐡"
            ]
            
            # Hidden prompts sent to the AI to distract the server
            random_ai_prompts = [
                "Tell me a random interesting fact about the ocean or fish.",
                "Say something incredibly funny and random to distract from an ad.",
                "Make up a very short story about a brave fish.",
                "Give me a random inspiring quote.",
                "Sing a short song about swimming in the sea."
            ]

            # Reply to the bumper bot's message directly
            await message.reply(random.choice(shield_phrases))

            # Trigger the AI for a random response to follow up
            ai_prompt = random.choice(random_ai_prompts)
            async with message.channel.typing():
                ai_response = await self.get_guppylm_response(ai_prompt)
                await message.channel.send(ai_response)
            
            # Stop here so we don't trigger the regular chat logic
            return

        # ---------------------------------------------------------
        # 2. NORMAL CHAT LOGIC (Anywhere else, or from humans)
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

if not TOKEN:
    print("ERROR: DISCORD_BOT_TOKEN environment variable not set!")
    sys.exit(1)

client.run(TOKEN)
