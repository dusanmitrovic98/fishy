import discord
import asyncio
import os
import sys
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer
from aiohttp import web

TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# --- DUMMY WEB SERVER ---
async def handle_ping(request):
    return web.Response(text="Blub! Fishy is alive and FAST on ONNX.")

async def start_dummy_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# --- ONNX AI SETUP (LOADS ONCE) ---
print("Loading Fast ONNX model...")
try:
    tokenizer = Tokenizer.from_file("docs/tokenizer.json")
    session = ort.InferenceSession("docs/model.onnx")
    input_name = session.get_inputs()[0].name
except Exception as e:
    print(f"ERROR: Could not find ONNX files in docs/ folder: {e}")
    sys.exit(1)

def run_fish_inference(prompt):
    # GuppyLM was trained ONLY on lowercase text + newline
    text = f"{prompt.lower().strip()}\n"
    input_ids = tokenizer.encode(text).ids
    
    generated_ids = []
    for _ in range(64): # Max response length
        x = np.array([input_ids], dtype=np.int64)
        logits = session.run(None, {input_name: x})[0]
        next_token = int(np.argmax(logits[0, -1, :]))
        
        generated_ids.append(next_token)
        input_ids.append(next_token)
        
        if "\n" in tokenizer.decode(generated_ids): break
            
    return tokenizer.decode(generated_ids).strip()

class FishBot(discord.Client):
    async def setup_hook(self):
        self.loop.create_task(start_dummy_server())

    async def on_message(self, message):
        if message.author == self.user or "fishy" not in message.content.lower():
            return

        clean_prompt = message.content.lower().replace("fishy", "").strip() or "hello"
        async with message.channel.typing():
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, run_fish_inference, clean_prompt)
            await message.channel.send(response or "blub.")

intents = discord.Intents.default()
intents.message_content = True
client = FishBot(intents=intents)
client.run(TOKEN)
