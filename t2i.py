from diffusers import DiffusionPipeline, AutoPipelineForText2Image
import torch
from PIL import Image
import discord
import io
import asyncio
from passwords import discord_channel, discord_client

# default permissions
intents = discord.Intents.default()
# setting paremeters and model for image generation
pipe = AutoPipelineForText2Image.from_pretrained('stabilityai/stable-diffusion-xl-base-1.0', torch_dtype=torch.float16, use_safetensors=True, variant="fp16", device="cpu")
# slower but allows for low memory usage (can be used on a laptop)
pipe.enable_sequential_cpu_offload()

# temporary data hold
data_hold = []

# function for generating information 
async def imagine_gen(text):
    # connect to client with permissions
    client = discord.Client(intents=intents)
    # clearing data hold
    data_hold.clear()
    # defining the incoming text as prompt
    prompt = text
    # saving best generated image to variable
    images = pipe(prompt=prompt).images[0]
    # defining image path based on prompt name
    image_path = f"ai_images/{prompt}.png"
    # saving image to path
    images.save(image_path)
    buf = io.BytesIO()
    images.save(buf, format='PNG')
    buf.seek(0)

    # open image
    img = Image.open(image_path)
    img.show()
    # temporary hold image and prompt
    data_hold.append(buf)
    data_hold.append(prompt)
    print(data_hold)

    @client.event
    # when bot is turned on, send image
    async def on_ready():
        # grab channel to send to
        channel = client.get_channel(discord_channel)
        print('Bot is ready.')
        try:
            # find image to send
            buf.seek(0)  
            # send image prompt
            await channel.send(f"prompt: {prompt}")
            # send generated image
            await channel.send(file=discord.File(fp=buf, filename=f'{prompt}.png'))
            # empty cuda cache for sanity
            torch.cuda.empty_cache()
            # close discord client once task is done
            await client.close()
        # if error, print error and close client
        except Exception as e:
            print(e)
            await client.close()
    # start client
    await client.start(discord_client)
