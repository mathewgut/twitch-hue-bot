# main code base for bot functions and commands

import twitchio
from twitchio.ext import commands, pubsub
import asyncio
from ctransformers import AutoModelForCausalLM
import time
from channels import chan_list, cl_id, tok, channel_id, rav_tok
from music import liked, song_current, request_song, remove_song, queue, clear_queue, get_tracks
from context_grab import context_match_adv
from t2i import imagine_gen
import torch
import emoji

reply_history = {}
reply_history_tst = {}
msg_history = {}
msg_history_tst = {}
msg_history['hue'] = []
req_stack = []
chatters = []
client = twitchio.Client(token=rav_tok)
client.pubsub = pubsub.PubSubPool(client)

## TODO: Add a summary for top chatters, donos, subs, etc when end of stream is "detected"
## TODO: Change context system to get the most similar sentence's "similarity value", if below x threshold do not use that context
## TODO: Make NLP tasks async so bot can still function when processing, it could also say busy when another task is working
## TODO: Once playlist hits four songs switch currently playing to the playlist

# s = sentence, i = index
# summary: if a string is over x amount of characters (for twitch we use 400) it will split the text into chunks 
# # based on first . or , found within the last 50 characters of the message
def split_string_into_chunks(s: str, max_length: int = 400, search_distance: int = 50) -> list:
    # store the chunks
    chunks = []
    i = 0
    # while i is smaller than length of input string
    while i < len(s):
        # defines the max length for chunking text
        end = i + max_length
        # if its still within the sentence
        if end < len(s):
            # for x in range of the end length and current placement - the distance to search for punctuation
            for j in range(end, max(i + max_length - search_distance, i), -1):
                # if sentence[x] contains punctuation
                if s[j] in '.,':

                    end = j + 1
                    break
        chunks.append(s[i:end])
        i = end
    return chunks

# checks each message to see if hue was mentioned, checking for ravhue for redundency
def mention_check(message) -> bool:
    if 'ravhue' in message.lower() or 'hue' in message.lower():
        return True
    return False


async def llm_reply(message, name):
    loop = asyncio.get_event_loop()
    # if user has prompted the bot within current runtime
    if name in reply_history:
        print(len(reply_history[name]))
        # store the position of the last message from user to bot
        pos_len = len(reply_history[name]) - 1
        print(pos_len, reply_history[name])
        # responses bot has sent to user
        print("msg_history", msg_history[name], "length:", len(msg_history[name]))
        # if bot has sent 2 or more messages
        if len(msg_history[name]) >= 2:
            # saving latest message from bot to user to use for context matching
            context = msg_history[name]
            # send to context matching system using most recent msg from bot to user, and current msg user to bot
            acc_context = context_match_adv(context, message)
            prompt = f"<<SYS>>Act as Hue. A Twitch chat bot who gives short reactionary replies to/about incoming chats in ItszRaven's live stream. Topics and the nature of questions may change drastically. Do not get too strung up on previous context. Keep your response short, do not explain your answer unless asked.<> Topic is potentially related to this message: {acc_context}. Your last message was: {msg_history[name][pos_len]}. The user's last message was: {reply_history[name][pos_len]}. <>  <</SYS>> [INST] {message} [/INST]"
            # function to nest inside of run_in_executor to allow for bot use during task
            def load_model_and_generate_response(prompt):
                # defining parameters and specific model
                llm = AutoModelForCausalLM.from_pretrained('llama-2-13b-chat.Q3_K_M.gguf', model_type='llama', max_new_tokens=300, stop=['instruction'], temperature=0.4, top_k=30, top_p = 0.8, repetition_penalty = 1.4)
                return llm(prompt)
            # async running of response generation
            response = await loop.run_in_executor(None, load_model_and_generate_response, prompt)
           
        # if bot has only sent one message
        elif len(msg_history[name]) == 1:
            prompt = f"<<SYS>>Act as Hue. A Twitch chat bot who gives short reactionary replies to/about incoming chats in ItszRaven's live stream. Topics and the nature of questions may change drastically. Do not get too strung up on previous context. Keep your response short, do not explain your answer unless asked.<> Your last message to User: {msg_history[name][0]} <> <</SYS>> [INST] {message} [/INST]"
            # function to nest inside of run_in_executor to allow for bot use during task
            def load_model_and_generate_response(prompt):
                # defining parameters and specific model
                llm = AutoModelForCausalLM.from_pretrained('llama-2-13b-chat.Q3_K_M.gguf', model_type='llama', max_new_tokens=300, stop=['instruction'], temperature=0.4, top_k=30, top_p = 0.8, repetition_penalty = 1.1)
                return llm(prompt)
            # async running of response generation
            response = await loop.run_in_executor(None, load_model_and_generate_response, prompt)
    
    # if there is no msg history between user and bot                                                                                                  
    else:
        prompt = f"<<SYS>>Act as Hue. A Twitch chat bot who gives short reactionary replies to/about incoming chats in ItszRaven's live stream. Keep your response short, do not explain your answer unless asked. <</SYS>> [INST] {message} [/INST]"
        # function to nest inside of run_in_executor to allow for bot use during task
        def load_model_and_generate_response(prompt):
            # defining parameters and specific model
            llm = AutoModelForCausalLM.from_pretrained('llama-2-13b-chat.Q3_K_M.gguf', model_type='llama', max_new_tokens=300, stop=['instruction'], temperature=0.4, top_k=30, top_p = 0.8, repetition_penalty = 1.1)
            return llm(prompt)
        # async running of response generation  
        response = await loop.run_in_executor(None, load_model_and_generate_response, prompt)

# if response contains an indicator of response of sorts (mentioning its prompt or its 'character'), split it and grab the part without the indicator

    if "--- as hue ---" in response.lower():
        response = response.lower().split("--- as hue ---", 1)
        response = response[1]
    elif 'hue:' in response.lower():
        response = response.lower().split("hue:", 1)
        response = response[1]
    elif 'response:' in response.lower():
        response = response.lower().split("response:", 1)
        response = response[1] 
    elif 'answer:' in response.lower():
        response = response.lower().split("answer:", 1)
        response = response[1]
    if len(response) > 400:
        # splits output into chunks less than 400 characters so it can be sent through twitch messages
        chunks = split_string_into_chunks(response.lower())
        total_chunk = len(chunks)
        print(chunks)
        print(total_chunk)
    else:
        chunks = response.lower()
    
    return chunks
# for timed jokes in chat about x topic
def llm_joke(message):
    # model set for more creativity as it needs to "joke". mixed results
    llm = AutoModelForCausalLM.from_pretrained('llama-2-13b-chat.ggmlv3.q2_K.bin', model_type='llama', max_new_tokens=300, stop=['instruction'], temperature=0.4, top_k=15, top_p = 0.65, repetition_penalty = 1.2)
    response = (llm(f"SYSTEM: {message}. RESPONSE:"))
    print(response)
    if 'hue:' in response.lower():
        response = response.lower().split("hue:", 1)
        response = response[1]
    elif 'response:' in response.lower():
        response = response.lower().split("response:", 1)
        response = response[1]
    elif 'answer:' in response.lower():
        response = response.lower().split("answer:", 1)
        response = response[1]
    if len(response) > 400:
        chunks = split_string_into_chunks(response.lower())
        total_chunk = len(chunks)
        print(chunks)
        print(total_chunk)
    else:
        chunks = response.lower()
    
    return chunks


# method for responding to first incoming message once timer is set off
def llm_chat(message, name):
    # defining parameters and specific model
    # parameters adjusted here to keep it extremley directed at the prompt and limit length specifically top_k and top_p
    llm = AutoModelForCausalLM.from_pretrained('llama-2-13b-chat.Q3_K_M.gguf', model_type='llama', max_new_tokens=300, stop=['instruction', 'hue', 'system'], temperature=0.5, top_k=30, top_p = 0.65, repetition_penalty = 1.4)
    # to generate response
    response = (llm(f"<<SYS> Respond as Hue. A Twitch chat bot who gives very short reactionary replies to/about incoming chats. Given this, appropriately reply to the following message and do not explain your response. <</SYS> [INST] {message}. [/INST]"))
    print(response)
    # text cleanup (since weights and prompt are different, different cleanup is needed than llm_reply)
    if 'hue:' in response.lower():
        response = response.lower().split("hue:", 1)
        response = response[1]
    elif 'response:' in response.lower():
        response = response.lower().split("response:", 1)
        response = response[1]
    elif 'answer:' in response.lower():
        response = response.lower().split("answer:", 1)
        response = response[1]
    if len(response) > 400:
        chunks = split_string_into_chunks(response.lower())
        total_chunk = len(chunks)
        print(chunks)
        print(total_chunk)
    else:
        chunks = response.lower()
    # chunks of text in a list 
    return chunks

# initialize bot class inheriting from twitchio bot commands
class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            # authorization token
            token= tok,
            # prefix needed to invoke commands
            prefix='!',
            # list of channels bot is active on
            initial_channels=chan_list,
            client_id= cl_id,
        )
        # variable that when set to True, will send next incoming message to llm_chat method
        self.msg_call = False
        # subscribes to incoming events from twitch
        self.pubsub = pubsub.PubSubPool(self)
        # variable that when set to true, will reset timer associated with llm_chat
        self.reset_timer = False
        # variable that indicates when bot is busy
        self.is_busy = False
        # this sets the async background task for the timer used in the llm_chat method
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.timer())

    # timed chat command for sending promotional messages to chat about the discord
    async def discord(self):
        while True:
            # ensuring the bot is only sending the message to the authorised channel
            chan = bot.get_channel(chan_list[0])
            await chan.send('For community and good vibes, join GVG: https://discord.gg/RUxshtmvMj To get annoying notifications when I go live; join my personal discord: https://discord.gg/CPmehW8')
            # this holds the loop so it will only start again after timer finishes (in seconds)
            await asyncio.sleep(3600)     
    
    # timer used for automated reactionary message responding
    async def timer(self):
            while True:
                #print("timer started")
                delay = 15*60
                await asyncio.sleep(delay) # set timer for x seconds
                if not self.reset_timer:
                    self.msg_call = True
                    #print("msg_call true")
                else:
                    self.reset_timer = False
    # resets timer
    def reset(self): 
        self.reset_timer = True

   
    # startup tasks for when bot is ready
    async def event_ready(self):
        # Log in indicator
        print(f'Logged in as | {self.nick}')
        # creates async task for discord messaging in case other methods are being called at the same time
        bot.loop.create_task(self.discord())
        #bot.loop.create_task(self.dad_joke())
        #bot.loop.create_task(main())

        # twitch event topics to subscribe to
        topics = [
            pubsub.channel_points(rav_tok)[channel_id],
            # Add more topics as needed
        ]
        await self.pubsub.subscribe_topics(topics)
    
    # on client event channel point redeem
    # not fully implented
    @client.event
    async def event_pubsub_channel_points(event: pubsub.PubSubChannelPointsMessage):
        # grab user name
        user = event.user['display_name']
        # grab id of event
        redeem_id = event.id
        # sort and save event data
        user_input = event.data['redemption']['user_input']
        # print data for testing
        print(f'User: {user}, Redeem ID: {redeem_id}, User Input: {user_input}')

    # command is callable via !function_name
    @commands.command()
    # most recent and frequently played songs
    async def recent(self, ctx: commands.Context):
        # try and except to handle potential errors
        try:
            # sending most played songs within specified time period and @-ing user who requested
            await ctx.send(f"{ctx.author.name} here are Raven's recent track on repeat: {liked()}")
            #await asyncio.sleep(self.cooldown)
        # if error, send message and error
        except Exception as e:
            await ctx.send(f"Seems there was an issue. Error: {e}")
    
    # command is callable via !function_name
    @commands.command()
    # name and artist of current playing song on specified spotify account
    async def song(self, ctx: commands.Context):
        # saving song name and artist to variable
        current = song_current()
        print(current)
        try:
            # sends current song to chat
            await ctx.send(f"{current}")
        # if error, send message and error
        except Exception as e:
            await ctx.send(f"Seems there was an issue. Error: {e}")

    # command is callable via !function_name
    @commands.command()
    # add specified song to queue
    async def addsong(self, ctx: commands.Context):
        # grabbing and saving message of everything after command invoke
        song = ctx.message.content.split(' ', 1)[1]
        # send request to function, return message if waiting for second song request
        try:
            output = request_song(song, ctx.author.name, req_stack=req_stack)
            # if function returns waiting message indicating waiting for other track
            if output == "waiting":
                await ctx.send("1/2 songs needed to add to queue")
            # if function is not waiting for other track
            else:
                await ctx.send(output)
        # if error, send message to chat with error
        except Exception as e:
            await ctx.send(f"Seems there was an issue. Error: {e}")

    # command is callable via !function_name
    @commands.command()
    async def removesong(self, ctx: commands.Context):
        # grabbing and saving message of everything after command invoke
        song = ctx.message.content.split(' ', 1)[1]
        # send text to function for song removal
        try:
            output = remove_song(song, ctx.author.name)
            # if function indicated song is removed
            if output == "removed":
                # send message to notify the user that song is removed from queue
                await ctx.send(f"Sure, removing {song}")
            # if any other code is sent then "removed"
            else:
                # define Exception as output from function
                Exception = output
                raise Exception
        # if error, send message with error
        except Exception as e:
            await ctx.send(f"Seems there was an issue. Error: {e}")
    
    # command is callable via !function_name
    @commands.command()
    # returns current queue of songs
    async def songlist(self, ctx: commands.Context):
        # requesting song queue from function
        try:
            output = get_tracks()
            # if request returns empty list, send chat that no songs are in queue
            if output == []:
                await ctx.send(f"There are no songs in queue")
            # if no empty list, indicating items in song queue
            else:
                await ctx.send(f"The current songs in queue are: {output}")
        # if error, send message with error
        except Exception as e:
            await ctx.send(f"Seems there was an issue. Error: {e}")

    # command is callable via !function_name
    @commands.command()
    # sends playlist link to chat
    async def playlist(self, ctx: commands.Context):
        await ctx.send(f"The queue playlist can be found here: https://open.spotify.com/playlist/3Hlbqq17xTLIGX6Xp0RcVu?si=dca7b63aaea04066")
    
    # command is callable via !function_name
    @commands.command()
    # goofy command for "jailing user"
    async def jail(self, ctx: commands.Context):
        zany_face = emoji.emojize(":zany_face:")
        jailed_user = ctx.message.content.split(' ', 1)[1]
        await ctx.send(f"Sorry,  @{jailed_user}, according to {ctx.author.name} it's jail time. oopsie {zany_face}")
    

    # when a message is sent in chat
    async def event_message(self, message):  
        # if message sent by bot user, do nothing
        if message.echo:
            return
        # store name of the author of message
        name = message.author.name
        # lower content of message for easier string cleanup
        content = message.content.lower()
        # sanity check
        print(f"{name}: {content}")
        # if name is in list of users who have already talked during current runtime of bot
        if name in chatters:
            pass
        # if user hasnt sent a chat during this runtime then welcome user
        else:
            await message.channel.send(f'Hey, {name}! Welcome to the stream!')
            # add user to current users messaged in stream
            chatters.append(str(name))

        # method for if someone mentions hue or ravhue in chat for llm reply
        if mention_check(content) == True:
            # if bot is handling another task, notify user to wait to invoke chat command
            if self.is_busy:
                await message.channel.send(f"@{name} The bot is currently busy. Please wait a moment.")
            else:
                # update variable to indicate task is running
                self.is_busy = True
                # notify user task has started
                await message.channel.send(f"@{name} processing request")
                # start time for elapsed time append
                start_time = time.time()
                try:
                    # send user message, and users name to function to generate llm response
                    response = await llm_reply(content, name)
                    # if bot has responded to user before
                    if name in msg_history:
                        # add users name and message content to dict
                        msg_history[name].append(content)
                        pass
                    # if bot has not responded to user before
                    else:
                        # create new list inside dictionary under key of users name
                        msg_history[name] = []
                        # add message content to list in users name key
                        msg_history[name].append(content)
                    
                    # if bot has replied to user before
                    if name in reply_history:
                        pass
                    # if bot hasnt replied to user before, create list under users name as key
                    else:
                        reply_history[name] = []
                    
                    # for counting the chunks of the output (if more than one)
                    counter = 0
                    # add the bot response response to the list under users name key
                    reply_history[name].append(response)
                    # end time for elapsed time
                    end_time = time.time()
                    # subtract difference of start and end time
                    elapsed_time = end_time - start_time
                    # round up to the closest tenth
                    elapsed_time = round(elapsed_time, 2) 

                    # if repomse is a list, indicating reponse is bigger than 400 characters and has been split
                    if type(response) == list:
                        # for item in response list
                        for chunk in response:
                            # increase counter when on new chunk in list
                            counter+=1
                            # send message to chat @-ing the user who prompted the bot including chunk of response, current chunk number, time request completed in
                            await message.channel.send(f"{name}, {str(chunk)}, {counter}/{len(response)} (request completed in {elapsed_time} seconds)")
                            # sleep before next loop to avoid spam detection (mitigated if bot is moderator in channel)
                            await asyncio.sleep(8)

                    # if response is not a list indicating only a single string
                    else:
                        # send message to chat @-ing the user who prompted the bot including chunk of response, number of total chunks, time request completed in
                        await message.channel.send(f"@{name}, {str(response)} 1/1 (request completed in {elapsed_time} seconds)")
                    # notifying chatters bot is ready for llm use
                    await message.channel.send("Whats next?")
                    # change busy status
                    self.is_busy = False
                # if error, send message in chat with error
                except Exception as e:
                    print(f"An error occurred: {e}")
                    await message.channel.send(f"Oops, something went wrong. Error: {e}")
                finally:
                    # regardless of error or not, ensure busy status is updated
                    self.is_busy = False
        
        # if timer has gone off for llm_chat
        elif self.msg_call == True:
            # starting time for elapsed time
            start_time = time.time()
            # reset timer immediatley after method starts to avoid responding to multiple messages while model generates a response
            self.reset()
            # pass in information to llm_chat method to generate a response
            response = llm_chat(content, name)
            # for counting chunks of a response (if any)
            counter = 0
            # end time for elapsed time
            end_time = time.time()
            # saving elapsed time difference to variable
            elapsed_time = end_time - start_time
            # rounding elapsed time to closest tenth
            elapsed_time = round(elapsed_time, 2) 
            # if response is list, indicating chunks
            if type(response) == list:
                for chunk in response:
                    # for each chunk increase the counter by one
                    counter+=1
                    # for each chunk, add the name of user, the chunk, the current chunk count, and the total chunks
                    await message.channel.send(f"@{name}, {str(chunk)}, {counter}/{len(response)}")
                    # sleep to avoid spam moderation in twitch chat
                    await asyncio.sleep(8)

            # if response is a string, indicating a single message
            elif type(response) == str:
                # send whole message
                await message.channel.send(f"@{name}, {response}")
            # reset msg_call variable for next timer
            self.msg_call = False

        # since overridding default systems, have to manually handle commands
        await self.handle_commands(message)

    # command made to essentially check if bot is on
    @commands.command()
    async def hello(self, ctx: commands.Context):
        await ctx.send(f'Hello {ctx.author.name}!')
    
    # sends link to hue commands list
    @commands.command()
    async def help(self, ctx: commands.Context):
        await ctx.send(f'@{ctx.author.name} my commands can be found here: https://rubberduk.ca/2023/10/24/hue-commands/')
    


# run bot
bot = Bot()

# command is callable via !function_name
@bot.command(name='imagine')
# text to image generation
async def imagine(ctx: commands.Context):
    # if bot.is_busy indicator is true, meaning bot is busy
    if bot.is_busy:
        # notify user bot is unavailable
        await ctx.send("Im a bit busy at the moment, relax, jeez.")
        # return indicator that nothing happened
        return 0
    # get event loop
    loop = asyncio.get_event_loop()
    # change is_busy indicator to reflect working task
    bot.is_busy = True
    # define minimum character length requirement for prompt
    length_req = 3
    # save contents of message after command invoke
    message = ctx.message.content.split(' ', 1)[1]
    # if length of message is greater or equal to length requirement
    if len(message) >= length_req:
        # notify user imagine is generating and estimated time
        await ctx.send(f'@{ctx.author.name} imagining {message} (this may take around ~5 minutes)')
        try:
            # async image generation function with prompt
            await imagine_gen(message)
            # notift user in chat when image is generated
            await ctx.send(f'@{ctx.author.name} your image has been generated')
            # empty cache after generation to prevent crashing
            torch.cuda.empty_cache()
        # if error, send message with error
        except Exception as e:
            await ctx.send(f"Oops, brain fart. Error: {e}")
    # if prompt does not meet the minimum length requirement, notify user
    else:
        await ctx.send(f"@{ctx.author.name}, your prompt does not meet the minimum character requirment of {length_req}")
    print("image complete, waiting for next")
    # update busy indicator
    bot.is_busy = False
# run bot
bot.run()
