import spotipy
from spotipy.oauth2 import SpotifyOAuth
from passwords import SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URL
from channels_tok import chan_list

# declare scope for authorization token
scope = "user-read-playback-state playlist-modify-public playlist-modify-private user-library-read user-library-modify user-top-read"

# authenticating spotify with tokens from accounts, scope, and username of intended account to read/modify
sp = spotipy.Spotify(auth_manager=spotipy.SpotifyOAuth(scope=scope, client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URL, username=chan_list[0]))

# returns top played songs from user in specified period
def liked():
    # specifying time range and amount of songs to grab from users top played songs
    results = sp.current_user_top_tracks(limit=5, time_range='short_term')
    # pulling song names and artists
    top_5_songs = [(track['name'] + " by " + track['artists'][0]['name']) for track in results['items']]
    
    return top_5_songs

# legacy function
def add_to_queue(song):
    sp.add_to_queue(device_id=None)

# return currently playing song on specified account
def song_current():
    # grabbing information from current playing song on account
    current_playback = sp.current_playback()

    # if there is a currently playing song
    if current_playback is not None and current_playback["is_playing"]:
        # grab current song
        current_track = current_playback["item"]
        # save song name and artist
        track_name = current_track["name"]
        artists = [artist["name"] for artist in current_track["artists"]]
        # return string of currently playing song with artist name
        return f"Currently playing: {track_name} by {', '.join(artists)}"
    else:
        # if no song planning, return to notify user
        return "No track currently playing"

# dictionary of songs as keys, and the requesting user as values
queue = {}
# temporary holding for songs to be queued
stack = []
# function for adding requested music to queue
def request_song(song, author, req_stack: list = stack):
    try:
        # search for song based on request text
        results = sp.search(q=song, type="track", limit=1)
        # save best match track_uri to variable based on song request text
        track_uri = results["tracks"]["items"][0]["uri"]
        print(track_uri)
        # rename track_uri variable for legibility
        song = track_uri
        # add song to request stack
        req_stack.append(song)
        # updating queue dict with track_uri as key and the requesting user as value
        queue.update({song:author})
        # if request stack is less than 2, return message to wait for another request
        if len(req_stack) < 2:
            print(req_stack)
            return("waiting")
        # if request stack is greater or equal to 2
        elif len(req_stack) >= 2:
            # save queue playlist id
            playlist_id = '3Hlbqq17xTLIGX6Xp0RcVu'
            # add songs from stack to queue playlist
            print(req_stack)
            sp.playlist_add_items(playlist_id, req_stack)
            # Update the queue dictionary
            print(queue)
            # search and save track information based on first position request stack track_uri
            track1 = sp.track(req_stack[0])
            # save name of first track
            track1_name = track1['name']
            # save artist of first track
            track1_art = track1['artists'][0]['name']
            # search and save track information based on second position request stack track_uri
            track2 = sp.track(req_stack[1])
            # save name of second track name
            track2_name = track2['name']
            # save second track artist
            track2_art = track2['artists'][0]['name']
            print(req_stack)
            # clear request stack for next song requests
            req_stack.clear()
            # return added song information
            return(f"added {track1_name} by {track1_art} and {track2_name} by {track2_art} to queue")
    # if error, return error message
    except Exception as e:
        return(e)
    
# function for removing song from playlist 
def remove_song(song, author):
    # queue playlist id
    playlist_id = '3Hlbqq17xTLIGX6Xp0RcVu'
    # search for song based on request text
    results = sp.search(q=song, type="track", limit=1)
    # save best match track_uri to variable based on song request text
    track_uri = results["tracks"]["items"][0]["uri"]

    print(queue[track_uri])
    # if requested song removal is from the same person that added the song
    if queue[track_uri] == author:
        # pop song from queue
        queue.pop(track_uri)
        print(queue)
        # save to be removed tracks as list
        track_ids = [track_uri]
        # remove all instances of song in playlist
        sp.playlist_remove_all_occurrences_of_items(playlist_id, track_ids)
        print("Song removed from playlist")
        # succuesful status code
        return("removed")
    else:
        # if not correct user
        return(NameError)
    

def get_tracks():
    # queue playlist id
    playlist_id = '3Hlbqq17xTLIGX6Xp0RcVu'
    # temporary list for storing song information
    tracks = []
    # for song in queue playlist
    for item in sp.playlist_tracks(playlist_id)["items"]:
        # save current song
        track = item["track"]
        # save current track uri
        track_uri = track["uri"]
        # save current song name
        track_name = track["name"]
        # save name of artist
        track_artist = track["artists"][0]["name"]
        # add track name and artist to tracks list
        tracks.append(f"{track_name} - {track_artist}")
    print(tracks)
    # return list of all songs currently in queue
    return tracks
