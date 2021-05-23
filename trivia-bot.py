# https://discord.com/api/oauth2/authorize?client_id=845940942325678101&permissions=36760896&scope=bot
import asyncio, vigenere
from discord.ext import commands
import discord, os, trivialib, random

key:str = vigenere.random_key()

num_emojis = ['0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']

container={}

def embed1(options:list, guess_type):
    global key
    embed=discord.Embed(title='Song Trivia', color=0x03f8fc)
    correct_guess=options[0]
    random.shuffle(options)
    shuffled_correct_guess_index=options.index(correct_guess)
    embed.add_field(name="Guess the song's {}:".format(guess_type), value='1. {0}\n2. {1}\n3. {2}\n4. {3}'.format(options[0],options[1],options[2],options[3]), inline=False)
    session_id=vigenere.encrypt(str(shuffled_correct_guess_index), key)
    embed.set_footer(text='sessionid:{0}'.format(session_id))
    return embed

def score_embed(server_id):
    global container
    embed=discord.Embed(title='Song Trivia', color=0x03f8fc)
    players_score=container[server_id]['players']
    players_score=dict(reversed(sorted(players_score.items(), key=lambda item: item[1])))
    string=''
    for i in players_score:
        string+='<@{player_id}>  -  {score}\n'.format(player_id=i, score=str(players_score[i]))
    embed.add_field(name='Scoreboard', value=string, inline=False)
    return embed

def song_detail_embed(name, artists, album, image_url, song_url):
    embed=discord.Embed(title='Correct Answer', color=0x03f8fc)
    embed.set_thumbnail(url=image_url)
    embed.add_field(name='Song', value=name, inline=False)
    embed.add_field(name='Album', value=album, inline=False)
    embed.add_field(name='Artists', value=artists, inline=False)
    embed.add_field(name='Listen on', value='[Spotify]({0})'.format(song_url), inline=False)
    return embed

cp='$'
bot=commands.Bot(command_prefix=cp)

@bot.event
async def on_ready():
    print('Status: Online')

@bot.event
async def on_reaction_add(reaction, user):
    global container, key
    message = reaction.message
    server_id=message.guild.id
    if not user.bot:
        user_id=str(user.id)
        if user_id in container[str(server_id)]['has_reacted'] or\
        user_id not in list(container[str(server_id)]['players']):
            await message.remove_reaction(reaction, user)
        
    if not user.bot and message.author == bot.user and\
    user_id in list(container[str(server_id)]['players']) and\
    user_id not in container[str(server_id)]['has_reacted']:
        container[str(server_id)]['has_reacted'].append(user_id)
        channel = message.channel
        msg=await channel.fetch_message(message.id)

        # checking for correct answer
        encrypted_session_id=str(msg.embeds[0].footer.text).split('sessionid:')[1]
        ## decrypting answer
        correct_answer=vigenere.decrypt(encrypted_session_id, key)
        reacted_answer=num_emojis.index(str(reaction))-1
        if str(reacted_answer) == correct_answer:
            current_score=container[str(server_id)]['players'][user_id]
            bonus=container[str(server_id)]['bonus']
            current_score+=3
            if 1<bonus<=10:current_score+=3;bonus-=1
            container[str(server_id)]['players'][user_id]=current_score
            container[str(server_id)]['bonus']=bonus

@bot.command()
async def game(ctx, url):
    global container
    server_id = ctx.message.guild.id
    starter_channel = ctx.message.author.voice.channel

    vc=await starter_channel.connect()
    players=starter_channel.members

    #initiating container
    container[str(server_id)]={
        'players':{},
        'has_reacted':[],
        'bonus': 10,
        'stop': False
    }

    # resetting container
    for player in players:
        container[str(server_id)]['players'][str(player.id)]=0

    trackid=url.split('?')[0].split('playlist/')[1]
    trackinfo=trivialib.spotify_info_privider(trackid)
    random.shuffle(trackinfo)
    for i in range(len(trackinfo)):
        if vc.is_connected() and not vc.is_playing() and not container[str(server_id)]['stop']:
            try:os.remove('{}.mp3'.format(str(server_id)))
            except Exception:pass
            container[str(server_id)]['bonus']=10
            container[str(server_id)]['has_reacted']=[]
            try:
                trivialib.track_downloader(trackinfo[i], server_id)
                random_item_type=['name','artist','album'][random.randint(0,2)]
                correct_guess=trackinfo[i][random_item_type]
                incorrect_guess=lambda item_type: trackinfo[random.randint(0, len(trackinfo)-5)][item_type]
                options=[correct_guess]
                k=0
                while k<3:
                    guess=incorrect_guess(random_item_type)
                    if guess not in options:
                        options.append(guess)
                        k+=1
                vc.play(discord.FFmpegPCMAudio('{sid}.mp3'.format(sid=server_id),  options='-vn -ss 15 -t 30'))
                embed=embed1(options, random_item_type)
                message=await ctx.send(embed=embed)
                for c in range(1,5):
                    await message.add_reaction(num_emojis[c])
                await asyncio.sleep(30)
                vc.resume()
                await message.delete()
                a=trackinfo[i]
                await ctx.send(embed=song_detail_embed(a['name'], a['artist'], a['album'], a['image'], a['track_url']))
                await asyncio.sleep(2)
                await ctx.send(embed=score_embed(str(server_id)))
                e=discord.Embed(title='Song Trivia', color=0x03f8fc)
                e.add_field(name='Get ready!!', value='`Next round is starting in 5 seconds.`', inline=True)
                n=await ctx.send(embed=e)
                await asyncio.sleep(5)
                await n.delete()
            except AttributeError:ctx.send('Please connect to a voice channel before interacting.');continue
            except NotADirectoryError: pass
    vc.stop()
    await ctx.send('**Game Over**')

@bot.command()
async def stop(ctx):
    global container
    server_id = ctx.message.guild.id
    container[str(server_id)]['stop']=True
    await ctx.add_reaction('✅')
token=os.environ.get('EXPERIMENTAL_BOT_TOKEN')
bot.run(token)
