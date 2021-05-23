import spotipy, youtube_dl
from spotipy.oauth2 import SpotifyClientCredentials
def spotify_info_privider(track_id=None):
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())
    l=sp.playlist_items(playlist_id=track_id)
    songs=[]
    for i in l['items']:
        if i['track']['duration_ms']<900000:
            song_name=i['track']['name']
            album_name=i['track']['album']['name']
            artists_name=''
            for j in i['track']['artists']:
                if not len(artists_name)>=30:
                    artists_name+=j['name']+', '
            image=i['track']['album']['images'][2]['url']
            track_url=i['track']['external_urls']['spotify']
            songs.append({
                'name':song_name,
                'artist': artists_name,
                'album': album_name,
                'image': image,
                'track_url': track_url
                })
    return songs

def track_downloader(song:list, channel_id:int):
    ydl_opts = {
                'format': 'bestaudio/best',
                'download_archive': None,
                'outtmpl': '{song_name}.mp3'.format(song_name=str(channel_id)),
                'default_search': 'ytsearch',
                'noplaylist': True,
                'postprocessor_args': [
                    '-metadata', 'title=' + song.get('name'),
                    '-metadata', 'artist=' + song.get('artist'),
                    '-metadata', 'album=' + song.get('album'),
                    {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                    }
                ]
            }
    query = f"{song.get('artist')} - {song.get('name')} Lyrics".replace(":", "").replace("\"", "")    
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([str(query)])

