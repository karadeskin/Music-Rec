import requests
from datetime import datetime, timedelta
from flask import Flask, redirect, request, jsonify, session, render_template_string
import urllib.parse
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import config
from spotify import get_trending_playlist_data, hybrid_recommendations
import secrets
#import libraries

#create a flask web app instance
app = Flask(__name__)
#set random secret key for security
app.secret_key = secrets.token_hex(16)
#spotify API credentials and redirect URI
CLIENT_ID = config.CLIENT_ID
CLIENT_SECRET = config.CLIENT_SECRET
REDIRECT_URI = 'http://localhost:8888/callback'
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

#route to the home page
@app.route('/')
def index():
    return "Kara's Spotify App <a href='/login'>Login with Spotify</a>"

#route to initiate spotify oauth login and authorization
@app.route('/login')
def login():
    #define scope and params for oauth request
    scope = 'user-read-private user-read-email'
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri' : REDIRECT_URI,
        'show_dialog': True
    }
    #auth url and redirect user to spotify login page
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

#route to handle callback after spotify authorization
@app.route('/callback')
def callback():
    #if error in auth process
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})
    #if auth successful, exchange auth code for access token
    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }
        #send POST request to spotify to get access token
        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()
        #store in vars
        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']
        #redirect user to playlist page after successful login
        return redirect('/playlists')

#route to display and handle playlist data and song rec
@app.route('/playlists', methods=['GET', 'POST'])
def get_playlists():
    #ensure user logged in by checking access token
    if 'access_token' not in session:
        return redirect('/login')
    #check if access token has expired and redirect to refresh
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    #get token from session
    access_token = session['access_token']
    #handle POST requests to fetch and display playlist data and recs
    if request.method == 'POST':
        #get playlist ID entered by user
        playlist_id = request.form.get('playlist_id')
        if playlist_id:
            #fetch playlist data using spotify API
            music_df, status = get_trending_playlist_data(playlist_id, access_token)
            if status:
                #normalize music features for rec
                scaler = MinMaxScaler()
                music_features = music_df[['Danceability', 'Energy', 'Key', 'Loudness', 'Mode', 'Speechiness', 'Acousticness', 'Instrumentalness', 'Liveness', 'Valence', 'Tempo']].values
                music_features_scaled = scaler.fit_transform(music_features)
                #get song name entered by user for rec
                input_song_name = request.form.get('song_name')
                if input_song_name:
                    #generate recs based on input song and music features
                    recommendations, suggestion = hybrid_recommendations(input_song_name, music_df, music_features_scaled, num_recommendations=5)
                    #if successfully generated, render results
                    if suggestion:
                        return render_template_string("""
                        <h2>Song names in your playlist:</h2>
                        <ul>
                        {% for track in music_df %}
                            <li>{{ track['Track Name'] }}</li>
                        {% endfor %}
                        </ul>
                        
                        <h2>Recommended song names:</h2>
                        <ul>
                        {% for rec in recommendations %}
                            <li>{{ rec['Track Name'] }}</li>
                        {% endfor %}
                        </ul>
                        """, music_df=music_df.to_dict(orient='records'), recommendations=recommendations.to_dict(orient='records'))
                    else:
                        #display error message if rec could not be generated
                        return "Sorry, failed to generate recommemdations."
            else:
                #display error message if playlist data could not be retrieved
                return "Failed to retrieve playlist data."
    #display HTML form for entering playlist ID and song name
    return '''
        <form method="POST">
            Enter your Playlist ID: <input type="text" name="playlist_id"><br>
            Enter a Song Name for Recommendation: <input type="text" name="song_name"><br>
            <input type="submit" value="Get Recommendations">
        </form>
    '''

#route to handle token refresh when token expires
@app.route('/refresh-token')
def refresh_token():
    #ensure refresh token exists in session
    if 'refresh_token' not in session:
        return redirect('/login')
    #refresh access token if expired
    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }
        #send POST request to refresh access token
        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()
        #store new access token and update the expiration time
        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']
        #redirect back to page
        return redirect('/playlists')

#run the flask app on port 8888 and enable debug mode for dev
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
    
        
        
