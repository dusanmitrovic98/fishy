import discord
import asyncio
import os
import sys
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer
from aiohttp import web
import traceback

TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# --- DUMMY WEB SERVER FOR RENDER ---
async def handle_ping(request):
    return web.Response(text="Blub! Fishy is alive and running natively on ONNX.")

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
    tokenizer = Tokenizer.from_file("docs/tokenizer.json")
    session = ort.InferenceSession("docs/model.onnx")
    input_name = session.get_inputs()[0].name
    print("ONNX Model loaded successfully!")
except Exception as e:
    print(f"FAILED TO LOAD ONNX: {e}")
    sys.exit(1)

def run_fish_inference(prompt):
    # GuppyLM was trained on pure lowercase text separated by newlines.
    # No "You>" or "Guppy>" labels allowed!
    clean_text = prompt.lower().strip()
    text = f"{clean_text}\n"
    
    input_ids = tokenizer.encode(text).ids
    
    # Try to find an End-Of-Sequence token if the tokenizer has one
    eos_token_id = tokenizer.token_to_id("<|endoftext|>")
    if eos_token_id is None:
        eos_token_id = tokenizer.token_to_id("</s>")
        
    generated_ids =[]
    max_length = 128 
    
    # Run the generation loop
    for _ in range(max_length - len(input_ids)):
        x = np.array([input_ids], dtype=np.int64)
        
        # Predict the next word
        logits = session.run(None, {input_name: x})[0]
        next_token = int(np.argmax(logits[0, -1, :]))
        
        # Stop condition 1: It generated an official End-Of-Sequence token
        if eos_token_id is not None and next_token == eos_token_id:
            break
            
        generated_ids.append(next_token)
        input_ids.append(next_token)
        
        # Stop condition 2: The fish finished its sentence and generated a newline
        decoded_so_far = tokenizer.decode(generated_ids)
        if "\n" in decoded_so_far:
            break
            
    # Clean up the final output
    response = tokenizer.decode(generated_ids).strip()
    return response
# ---------------------

class FishBot(discord.Client):
    async def setup_hook(self):
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
                    loop = asyncio.get_running_loop()
                    response = await loop.run_in_executor(None, run_fish_inference, clean_prompt)
                        
                    if not response:
                        response = "blub. empty water."

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
