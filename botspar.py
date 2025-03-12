import os
import discord
import yt_dlp as youtube_dl
import asyncio
import requests

# Caminho do FFmpeg (verifique se está correto)
ffmpeg_path = "C:\\ffmpeg\\ffmpeg\\bin"  
os.environ['PATH'] += os.pathsep + ffmpeg_path

# Use uma variável de ambiente para o token
intents = discord.Intents.default()
intents.messages = True
intents.guild_messages = True
intents.guilds = True
intents.voice_states = True
intents.message_content = True


client = discord.Client(intents=intents)

# Opções do yt-dlp para evitar HLS
ytdl_format_options = {
    'format': 'bestaudio[ext=webm]/bestaudio[ext=mp4]/bestaudio',
    'noplaylist': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320',
    }],
    
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -b:a 192k'
}

headers = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json"
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

@client.event
async def on_ready():
    print(f"Bot está pronto como {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.startswith('!play'):
        if message.author.voice:
            voice_channel = message.author.voice.channel
            if not client.voice_clients or not any(vc.channel == voice_channel for vc in client.voice_clients):
                voice = await voice_channel.connect()
            else:
                voice = discord.utils.get(client.voice_clients, channel=voice_channel)

            song_url = message.content[6:].strip()
            
            try:
                info = ytdl.extract_info(song_url, download=False)
                
                # Pegar URL de áudio compatível (evitando .m3u8)
                audio_url = None
                for fmt in info['formats']:
                    if fmt.get('acodec') != 'none' and 'm3u8' not in fmt['url']:
                        audio_url = fmt['url']
                        break
                
                if not audio_url:
                    await message.channel.send("Não foi possível extrair áudio compatível desse link.")
                    return

                source = await discord.FFmpegOpusAudio.from_probe(audio_url, **ffmpeg_options)
                voice.play(source)
                
                await message.channel.send(f"Tocando: {info['title']}")

                while voice.is_playing():
                    await asyncio.sleep(1)
                await voice.disconnect()

            except Exception as e:
                await message.channel.send(f"Erro ao tocar a música: {str(e)}")
                print(e)
    
    if message.content.startswith('!stop'):
        if client.voice_clients:
            await client.voice_clients[0].disconnect()
            await message.channel.send("Parando a música.")

    if message.content.startswith("!user"):
        user_id = int(message.content[-1])
        numbers = [int(word) for word in message.content.split() if word.isdigit()]
        response = requests.get(f"https://discord.com/api/v10/users/{numbers[0]}", headers=headers)
        print(response.text)
        if response.status_code == 200:
            user_data = response.json()
            avatar_hash = user_data.get('avatar')
            if avatar_hash:
                avatar_url = f"https://cdn.discordapp.com/avatars/{user_data['id']}/{avatar_hash}.png"
            else:
                avatar_url = f"https://cdn.discordapp.com/embed/avatars/{int(user_data['discriminator']) % 5}.png"
            embed = discord.Embed(title=f"Informações do usuário - {user_data['username']}", color=0x00ff00)
            embed.add_field(name=":closed_lock_with_key:  ID", value=user_data['id'], inline=False)
            embed.add_field(name=":bust_in_silhouette:   Nome de usuário", value=user_data['username'], inline=False)
            embed.add_field(name="Discriminador", value=user_data['discriminator'], inline=False)
            embed.set_thumbnail(url=avatar_url)
            print(numbers[0])
            await message.channel.send(embed=embed)
        else:
            await message.channel.send("Usuário não encontrado.")
            print(response.text)
            print(numbers[0])




client.run('')
