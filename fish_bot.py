import discord
import asyncio
import os
import sys
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer
from aiohttp import web
import traceback



# IMPORTANT: You need to import the text generation function from the GuppyLM code.
# Based on the screenshot of the repo structure, you will likely need to import
# their inference script or copy their chat logic here.
# For example (pseudo-code):
# from guppylm.inference import generate_text, load_model
# model, tokenizer = load_model("path/to/guppylm/model")

# Replace this with your NEW token
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# --- DUMMY WEB SERVER FOR RENDER ---
async def handle_ping(request):
    return web.Response(text="Blub! Fishy is alive and running on ONNX.")

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

# --- ONNX AI SETUP ---
print("Loading 10MB Quantized ONNX model...")
try:
    # Load files from the docs/ folder
    tokenizer = Tokenizer.from_file("docs/tokenizer.json")
    session = ort.InferenceSession("docs/model.onnx")
    input_name = session.get_inputs()[0].name
    print("ONNX Model loaded successfully!")
except Exception as e:
    print(f"FAILED TO LOAD ONNX: {e}")
    print("Ensure 'docs/model.onnx' and 'docs/tokenizer.json' exist!")
    sys.exit(1)

def run_fish_inference(prompt):
    # Format exactly how the model was trained
    text = f"You> {prompt}\nGuppy>"
    input_ids = tokenizer.encode(text).ids
    
    # 128 is the max context window for this tiny model
    max_length = 128 
    
    for _ in range(max_length - len(input_ids)):
        x = np.array([input_ids], dtype=np.int64)
        
        # Run the ONNX math to predict the next word
        logits = session.run(None, {input_name: x})[0]
        next_token = int(np.argmax(logits[0, -1, :]))
        input_ids.append(next_token)
        
        # Stop condition: if it tries to generate a new user prompt
        full_decoded = tokenizer.decode(input_ids)
        if "You>" in full_decoded.split("Guppy>")[-1]:
            break
            
    # Clean up and return just the fish's response
    final_output = tokenizer.decode(input_ids)
    response = final_output.split("Guppy>")[-1].replace("You>", "").strip()
    return response
# ---------------------

class FishBot(discord.Client):
    async def setup_hook(self):
        # Start the web server alongside the bot
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
                    # Run the ONNX AI generation without freezing Discord
                    loop = asyncio.get_running_loop()
                    response = await loop.run_in_executor(None, run_fish_inference, clean_prompt)
                        
                    if not response:
                        response = "blub. brain empty."

                    await message.channel.send(response[:1900])
                    
                except Exception as e:
                    tb = traceback.format_exc()
                    await message.channel.send(f"ONNX Error:\n```python\n{tb[:1900]}\n```")

intents = discord.Intents.default()
intents.message_content = True

client = FishBot(intents=intents)

if not TOKEN:
    print("ERROR: DISCORD_BOT_TOKEN environment variable not set!")
    sys.exit(1)

client.run(TOKEN)
