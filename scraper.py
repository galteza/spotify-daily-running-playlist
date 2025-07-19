from flask import Flask, request, url_for, session, redirect
from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
from requests import post, get
import base64
import json
import pprint
from scrapeBPM import scrapeBPM
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import csv
import pandas as pd

# STEP 1: LOADING ENVIRONMENT

load_dotenv()
client_ID = os.getenv("CLIENT_ID")
client_SECRET = os.getenv("CLIENT_SECRET")
client_token_url = 'https://accounts.spotify.com/api/token'

# STEP 2: REQUESTING A CLIENT-ACCESS TOKEN

#### Encoding ID & SECRET TO BASE64

client_creds = f'{client_ID}:{client_SECRET}'
client_creds_bytes = client_creds.encode("utf-8")
client_creds_b64 = str(base64.b64encode(client_creds_bytes), "utf-8")

initialize_client_token_headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': f'Basic {client_creds_b64}'
}
initialize_client_token_data = {"grant_type": "client_credentials"}

client_token_request_response = post(client_token_url, headers=initialize_client_token_headers, data=initialize_client_token_data)
CLIENT_TOKEN_INFO = json.loads(client_token_request_response.content)

pprint.pprint(client_token_request_response)
pprint.pprint(CLIENT_TOKEN_INFO)

# STEP 3: REQUESTING A USER-ACCESS TOKEN THROUGH OAUTH PROCESS

app = Flask(__name__)
app.config['SESSION_COOKIE_NAME'] = 'Cookie'
app.secret_key = 'sdkfjhksjadsf890123'

USER_TOKEN_INFO = 'user_token_info'

####    STEP 3.1: OAUTH Process (c/o Routing through Flask)

@app.route('/')
@app.route('/index')
def login():
    auth_url = createSpotifyOAuth().get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect_page')
def redirectPage():
    session.clear()
    code = request.args.get('code')
    user_token_info = createSpotifyOAuth().get_access_token(code)
    session[USER_TOKEN_INFO] = user_token_info
    return redirect(url_for('dailyRunningPlaylist', _external=True))


####    STEP 3.2: PLAYLIST REFRESH
@app.route('/daily_running_playlist')
def dailyRunningPlaylist():
    # STEP 3.2.1: Access User Playlists
    try:
        user_token_info = getUserToken()
    except:
        print('Not logged in.')
        return redirect('/')
    
    sp = spotipy.Spotify(auth=user_token_info['access_token'], requests_timeout=600)
    user_playlists = sp.current_user_playlists()['items']
    running_playlist_id = None

    for playlist in user_playlists:
        if(playlist['name'] == 'Daily Running Playlist'):
            running_playlist_id = playlist['id']

    if not running_playlist_id:
        return "ERROR: Could not find running playlist."

    liked_songs = []
    
    # STEP 3.2.2: Retrieving the user's Liked Songs in batches of 50 tracks then adding to liked_songs
    retrieving_liked_songs = sp.current_user_saved_tracks()
    while retrieving_liked_songs:
        # Extend the liked_songs array then retrieving the next ones in line if there exists any
        liked_songs.extend(retrieving_liked_songs['items'])
        retrieving_liked_songs = sp.next(retrieving_liked_songs) if retrieving_liked_songs['next'] else None
    
    # liked_songs_trackids = [song['track']['id'] for song in liked_songs if song['track']['id']]
    liked_songs_uri = [song['track']['uri'] for song in liked_songs if song['track']['uri']]
    liked_songs_name = [song['track']['name'] for song in liked_songs if song['track']['name']]
    liked_songs_artist = [song['track']['artists'][0]['name'] for song in liked_songs if song['track']['artists']]

    # STEP 3.2.3: Cross-checking TEMPO data of songs from CSV file containing BPMs and updating the CSV with the BPM (via SongBPM.com) of the newly introduced songs 
    
    # Take the name and the artist to put them together and make it a query
    liked_songs_query = [f'{name} {artist}' for name, artist in zip(liked_songs_name, liked_songs_artist)]
    

    df = pd.read_csv('BPMs.csv') 
    possible_running_songs_uri = []

    for query in liked_songs_query:
        new_data = {'Query': [query]}
        pd.DataFrame(new_data).to_csv('BPMs.csv', mode='a', index=False, header=False)

    '''
    # STEP 3.2.3: Cross-checking TEMPO data of songs from Spotify API & adding valid to possible running tracks
    audiofeatures_request_url = 'https://api.spotify.com/v1/audio-features/'
    
    possible_running_songs_uri = []

    for id in liked_songs_trackids:
        client_token_info = getClientToken()
        pprint.pprint(client_token_info)
        client_token_code = client_token_info['access_token']
        audiofeatures_request_headers = {
            'Authorization': f"Bearer {client_token_code}"
        }
        pprint.pprint(audiofeatures_request_headers)
        audiofeatures_request_response = get(f'{audiofeatures_request_url}{id}', headers=audiofeatures_request_headers)
        pprint.pprint(audiofeatures_request_response)
        audiofeatures_request_response_json = json.loads(audiofeatures_request_response.content)
        pprint.pprint(audiofeatures_request_response_json)
        song_tempo = audiofeatures_request_response_json['track']['tempo']

        if 150 <= song_tempo <= 170:
            possible_running_songs_uri.append(f'spotify:track:{id}')
    '''
    
    # STEP 3.2.4: Choosing final 50 tracks & replacing daily playlist
    if len(possible_running_songs_uri) < 50:
        final_running_songs_uri = possible_running_songs_uri
    elif len(possible_running_songs_uri) >= 50:
        final_running_songs_uri = random.sample(possible_running_songs_uri, 50)

    sp.playlist_replace_items(running_playlist_id, [])
    sp.playlist_add_items(running_playlist_id, final_running_songs_uri)
    
    return ("New Running Playlist for Today!")

# STEP 0: GENERAL FUNCTIONS

def createSpotifyOAuth():
    return SpotifyOAuth(
        client_id = client_ID,
        client_secret = client_SECRET,
        redirect_uri = url_for('redirectPage', _external = True),
        scope = 'user-library-read playlist-modify-public playlist-modify-private playlist-read-private'
    )

def getUserToken():
    user_token_info = session.get(USER_TOKEN_INFO)
    if not user_token_info:
        return redirect(url_for('dailyRunningPlaylist', _external = True))
    
    yes_expired = user_token_info['expires_in'] < 60

    if(yes_expired):
        user_token_info = createSpotifyOAuth().refresh_access_token(user_token_info['refresh_token'])

    return user_token_info

def getClientToken():
    client_token_info = CLIENT_TOKEN_INFO

    yes_expired = client_token_info['expires_in'] < 60

    if(yes_expired):
        renew_client_token_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {client_creds_b64}'
        }
        renew_client_token_data = {
            'grant_type': 'refresh_token'
        }

        client_token_refresh_response = post(client_token_url, headers=renew_client_token_headers, data=renew_client_token_data)
        
        if client_token_refresh_response.status_code != 200:
            print("Failed to refresh client token.")
            return None

        try:
            client_token_info = json.loads(client_token_refresh_response.content)
            print("New Client Token Response:", CLIENT_TOKEN_INFO)  # Debugging print
            
            if 'access_token' not in CLIENT_TOKEN_INFO:
                raise Exception("Error: No access_token found in the response.")
            
            return client_token_info
        except json.JSONDecodeError:
            print(f"Error decoding client token response. Response: {client_token_refresh_response.content}")
            return None

    return client_token_info

if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 7000)