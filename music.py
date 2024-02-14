import spotipy
from spotipy.oauth2 import SpotifyOAuth
from passwords import SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URL
from channels_tok import chan_list
#from twitch_hue

scope = "user-read-playback-state playlist-modify-public playlist-modify-private user-library-read user-library-modify user-top-read"

sp = spotipy.Spotify(auth_manager=spotipy.SpotifyOAuth(scope=scope, client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URL, username=chan_list[0]))


def liked():
    results = sp.current_user_top_tracks(limit=5, time_range='short_term')
    scope = 'user-top-read'
    # Extract the song names and artists
    top_5_songs = [(track['name'] + " by " + track['artists'][0]['name']) for track in results['items']]
    
    return top_5_songs

def add_to_queue(song):
    sp.add_to_queue(device_id=None)

def song_current():
    # Set up authentication

    # Get the current playback information
    current_playback = sp.current_playback()

    # Check if there is a currently playing track
    if current_playback is not None and current_playback["is_playing"]:
        # Get the current track
        current_track = current_playback["item"]
        # Get the track name and artist(s)
        track_name = current_track["name"]
        artists = [artist["name"] for artist in current_track["artists"]]
        return f"Currently playing: {track_name} by {', '.join(artists)}"
    else:
        return "No track currently playing"

"""
queue = {} 
def request_song(song, author):
    try:
        
        scope = "user-modify-playback-state user-library-read"
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URL, username='itszraven'))
        results = sp.search(q=song, type="track", limit=1)
        track_uri = results["tracks"]["items"][0]["uri"]

        # Replace with the URI of the track you want to add
        queue.update({song:author})
        print(queue)
        sp.add_to_queue(track_uri)
        return(results["tracks"]["items"][0]["name"])

    except Exception as e:
        return(e)
"""
queue = {}
stack = []
def request_song(song, author, req_stack: list = stack):
    try:
        results = sp.search(q=song, type="track", limit=1)
        track_uri = results["tracks"]["items"][0]["uri"]
        print(track_uri)
        song = track_uri
        req_stack.append(song)
        queue.update({song:author})
        if len(req_stack) < 2:
            print(req_stack)
            return("waiting")
        elif len(req_stack) >= 2:
            # The ID of the playlist
            playlist_id = '3Hlbqq17xTLIGX6Xp0RcVu'
            # Add the song to the playlist
            print(req_stack)
            sp.playlist_add_items(playlist_id, req_stack)
            # Update the queue dictionary
            print(queue)
            track1 = sp.track(req_stack[0])
            track1_name = track1['name']
            track1_art = track1['artists'][0]['name']
            track2 = sp.track(req_stack[1])
            track2_name = track2['name']
            track2_art = track2['artists'][0]['name']
            print(req_stack)
            req_stack.clear()
            return(f"added {track1_name} by {track1_art} and {track2_name} by {track2_art} to queue")
    except Exception as e:
        return(e)



#try:
#print(request('take on me', 'fart'))
#print(request('dancing queen', 'jeeves'))
#except Exception as e:
    #print(f"oops: {e}")

"""
def remove_song(song, author):
    scope = "user-modify-playback-state user-library-read"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URL, username='itszraven'))
    print(queue[song])
    if queue[song] == author:
        queue.pop(song)
        print(queue)
        while True:
            try:
                sp.next_track()
                print("fart")
            except spotipy.exceptions.SpotifyException:
                print("fart")
                break
        print("queue empty")
        for x in queue:
            request_song(x, author)
        return("items requeued")
    else:
        
        return(NameError)
"""

def remove_song(song, author):
    # The ID of the playlist
    playlist_id = '3Hlbqq17xTLIGX6Xp0RcVu'
    
    results = sp.search(q=song, type="track", limit=1)
    track_uri = results["tracks"]["items"][0]["uri"]

    print(queue[track_uri])
    if queue[track_uri] == author:
        queue.pop(track_uri)
        print(queue)
        # Remove the song from the playlist
        ## song is not a uri, fix
        track_ids = [track_uri]
        sp.playlist_remove_all_occurrences_of_items(playlist_id, track_ids)
        
        print("Song removed from playlist")
        return("removed")
    else:
        return(NameError)
    
def remove_song(song, author):
    # The ID of the playlist
    playlist_id = '3Hlbqq17xTLIGX6Xp0RcVu'
    
    results = sp.search(q=song, type="track", limit=1)
    track_uri = results["tracks"]["items"][0]["uri"]

    print(queue[track_uri])
    if queue[track_uri] == author:
        queue.pop(track_uri)
        print(queue)
        # Remove the song from the playlist
        ## song is not a uri, fix
        track_ids = [track_uri]
        sp.playlist_remove_all_occurrences_of_items(playlist_id, track_ids)
        
        print("Song removed from playlist")
        return("removed")
    else:
        return(NameError)
    
def get_tracks():
    playlist_id = '3Hlbqq17xTLIGX6Xp0RcVu'
    tracks = []
    for item in sp.playlist_tracks(playlist_id)["items"]:
        track = item["track"]
        track_uri = track["uri"]
        track_name = track["name"]
        # Get the name of the first artist
        track_artist = track["artists"][0]["name"]
        tracks.append(f"{track_name} - {track_artist}")
    print(tracks)
    return tracks


def clear_queue():
    scope = "user-modify-playback-state user-library-read"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URL, username='itszraven'))
    while True:
        try:
            sp.next_track()
            print("fart")
        except spotipy.exceptions.SpotifyException:
            print("fart")
            break
    print(queue)
    return("queue empty")

##print(remove_song('dancing queen', 'jeeves'))
