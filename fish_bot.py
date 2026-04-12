import discord
import asyncio
import sys
import re
import traceback
import os
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

    async def on_message(self, message):
        if message.author == self.user:
            return

        if "fishy" in message.content.lower():
            clean_prompt = message.content.lower().replace("fishy", "").strip()
            if not clean_prompt:
                clean_prompt = "hello" 

            async with message.channel.typing():
                try:
                    # Use the official working PyTorch CLI command
                    process = await asyncio.create_subprocess_exec(
                        sys.executable, '-m', 'guppylm', 'chat', '--prompt', clean_prompt,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )

                    stdout, stderr = await process.communicate()
                    out_str = stdout.decode('utf-8', errors='ignore').strip()
                    err_str = stderr.decode('utf-8', errors='ignore').strip()
                    
                    if process.returncode != 0:
                        error_msg = f"Crash! Exit code: {process.returncode}\nStderr:\n{err_str}"
                        await message.channel.send(f"```{error_msg[:1900]}```")
                        return

                    # Remove terminal color codes
                    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                    out_str = ansi_escape.sub('', out_str)
                    
                    final_lines =[]
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

                    await message.channel.send(response[:1900])
                    
                except Exception as e:
                    tb = traceback.format_exc()
                    await message.channel.send(f"Python Error:\n```python\n{tb[:1900]}\n```")

intents = discord.Intents.default()
intents.message_content = True

client = FishBot(intents=intents)

if not TOKEN:
    print("ERROR: DISCORD_BOT_TOKEN environment variable not set!")
    sys.exit(1)

client.run(TOKEN)
