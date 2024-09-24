import requests
import base64
import pandas as pd
import spotipy
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
#import libraries for making API requests, algorithms, etc.

def get_access_token(CLIENT_ID, CLIENT_SECRET):
    """
    func to obtain an access token from spotify using client credentials 
    args:
        CLIENT_ID (str): spotify app's client ID
        CLIENT_SECRET (str): spotify app's client secret
    returns:
        str: access token to authenticate API requests
    """
    #encode client credentials in base64
    client_credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    client_credentials_base64 = base64.b64encode(client_credentials.encode())
    #define token endpoint and headers
    token_url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Authorization': f'Basic {client_credentials_base64.decode()}'
    }
    #request access token
    data = {
        'grant_type': 'client_credentials'
    }
    response = requests.post(token_url, data=data, headers=headers)
    #check if request is successful and return access token
    if response.status_code == 200:
        access_token = response.json()['access_token']
        return access_token
    else:
        print("Error obtaining access token.")
        exit()

def get_trending_playlist_data(playlist_id, access_token):
    """
    function to retrieve the tracks and audio features from spotify playlist
    args:
        playlist_id (str): spotify playlist ID
        access_token (str): access token for Spotify API
    returns:
        pd.DataFrame: dataFrame containing track details and audio features
        bool: status indicating success (True) or fail (False)
    """
    #initialize spotify API client using the access token
    sp = spotipy.Spotify(auth=access_token)
    #get playlist tracks including track names, artists, albums
    playlist_tracks = sp.playlist_tracks(playlist_id, fields='items(track(id, name, artists, album(id, name)))')
    #initialize list to store music data
    music_data = []
    #loop through each track in playlist and get info
    for track_info in playlist_tracks['items']:
        track = track_info['track']
        track_name = track['name']
        artists = ', '.join([artist['name'] for artist in track['artists']])
        album_name = track['album']['name']
        album_id = track['album']['id']
        track_id = track['id']
        #fetch audio features for track
        audio_features = sp.audio_features(track_id)[0] if track_id != 'Not available' else None
        #try fetching other track details, like release date and popularity
        try:
            album_info = sp.album(album_id) if album_id != 'Not available' else None
            release_date = album_info['release_date'] if album_info else None
        except:
            release_date = None
        try:
            track_info = sp.track(track_id) if track_id != 'Not available' else None
            popularity = track_info['popularity'] if track_info else None
        except:
            popularity = None
        #store data in dictionary
        track_data = {
            'Track Name': track_name,
            'Artists': artists,
            'Album Name': album_name,
            'Album ID': album_id,
            'Track ID': track_id,
            'Popularity': popularity,
            'Release Date': release_date,
            'Duration (ms)': audio_features['duration_ms'] if audio_features else None,
            'Explicit': track_info.get('explicit', None),
            'External URLs': track_info.get('external_urls', {}).get('spotify', None),
            'Danceability': audio_features['danceability'] if audio_features else None,
            'Energy': audio_features['energy'] if audio_features else None,
            'Key': audio_features['key'] if audio_features else None,
            'Loudness': audio_features['loudness'] if audio_features else None,
            'Mode': audio_features['mode'] if audio_features else None,
            'Speechiness': audio_features['speechiness'] if audio_features else None,
            'Acousticness': audio_features['acousticness'] if audio_features else None,
            'Instrumentalness': audio_features['instrumentalness'] if audio_features else None,
            'Liveness': audio_features['liveness'] if audio_features else None,
            'Valence': audio_features['valence'] if audio_features else None,
            'Tempo': audio_features['tempo'] if audio_features else None,
        }
        #append data to list
        music_data.append(track_data)
    #convert list to a pandas dataframe
    df = pd.DataFrame(music_data)
    return df, True

def content_based_recommendations(input_song_name, music_df, music_features_scaled, num_recommendations=5):
    """
    function to generate content-based recommendations based on song features
    args:
        input_song_name (str): name of the input song to base recommendations on
        music_df (pd.DataFrame): dataframe containing playlist data
        music_features_scaled (np.ndarray): scaled music features for comparison
        num_recommendations (int): number of recommendations to generate
    returns:
        pd.DataFrame: dataframe containing recommended tracks
    """
    #check if input song exits in playlist data
    if input_song_name not in music_df['Track Name'].values:
        print(f"'{input_song_name}' not found in the dataset. Please enter a valid song name.")
        return
    #get index of song
    input_song_index = music_df[music_df['Track Name'] == input_song_name].index[0]
    #compute cosine similarity between input song features and all songs in the dataset
    similarity_scores = cosine_similarity([music_features_scaled[input_song_index]], music_features_scaled)
    #get the indices of the most similar ones
    similar_song_indices = similarity_scores.argsort()[0][::-1][1:num_recommendations + 1]
    #return top recommended songs as a df
    content_based_recommendations = music_df.iloc[similar_song_indices][['Track Name', 'Artists', 'Album Name', 'Release Date', 'Popularity']]
    return content_based_recommendations

def calculate_weighted_popularity(release_date):
    """
    function to calculate weighted popularity based on release date
    args:
        release_date (str): release date of the track
    returns:
        float: weight for popularity score based on how recent the release is
    """
    #parse release date and calculate time span since release
    release_date = datetime.strptime(release_date, '%Y-%m-%d')
    time_span = datetime.now() - release_date
    #weight is inversely proportional to time since release
    weight = 1 / (time_span.days + 1)
    return weight

def hybrid_recommendations(input_song_name, music_df, music_features_scaled, num_recommendations=5, alpha=0.5):
    """
    function to generate hybrid recommendations based on content and popularity
    args:
        input_song_name (str): name of the input song to base recommendations on
        music_df (pd.DataFrame): dataframe containing playlist data
        music_features_scaled (np.ndarray): scaled music features for comparison
        num_recommendations (int): number of recommendations to generate
        alpha (float): weight for balancing content-based and popularity-based recommendations
    returns:
        pd.DataFrame: dataframe containing hybrid recommended tracks
        bool: status indicating if recommendations were successfully generated
    """
    #make sure input song exists
    if input_song_name not in music_df['Track Name'].values:
        print(f"'{input_song_name}' not found in the dataset. Please enter a valid song name.")
        return
    #generate content based recs
    content_based_rec = content_based_recommendations(input_song_name, music_df, music_features_scaled, num_recommendations)
    #calculate weighted pop
    popularity_score = music_df.loc[music_df['Track Name'] == input_song_name, 'Popularity'].values[0]
    weighted_popularity_score = popularity_score * calculate_weighted_popularity(music_df.loc[music_df['Track Name'] == input_song_name, 'Release Date'].values[0])
    #create a hybrid rec dataframe
    hybrid_recommendations = content_based_rec
    #add the input song to the recs, weighted by pop score
    new_row = pd.DataFrame({
        'Track Name': [input_song_name],
        'Artists': [music_df.loc[music_df['Track Name'] == input_song_name, 'Artists'].values[0]],
        'Album Name': [music_df.loc[music_df['Track Name'] == input_song_name, 'Album Name'].values[0]],
        'Release Date': [music_df.loc[music_df['Track Name'] == input_song_name, 'Release Date'].values[0]],
        'Popularity': [weighted_popularity_score]
    })
    #concat new row to rec df and sort by pop
    hybrid_recommendations = pd.concat([hybrid_recommendations, new_row], ignore_index=True)
    hybrid_recommendations = hybrid_recommendations.sort_values(by='Popularity', ascending=False)
    hybrid_recommendations = hybrid_recommendations[hybrid_recommendations['Track Name'] != input_song_name]
    return hybrid_recommendations, True
