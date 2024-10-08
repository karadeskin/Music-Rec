# Kara's Spotify Playlist and Song Recommendation App
This is a Flask web application that integrates with the Spotify API to allow users to view playlist data, get song recommendations, and explore music based on content features such as danceability, energy, and tempo. The app leverages Spotify's OAuth flow for authentication, and users can input a playlist ID and a song name to receive song recommendations using a hybrid recommendation system.

## Features
- Spotify OAuth Login: Users can login with their Spotify accounts to authorize access to their playlists.
- Playlist Data Retrieval: Fetches data from user playlists, including track details and audio features.
- Content-Based Song Recommendations: Recommends songs based on audio features such as danceability, energy, and more.
- Hybrid Recommendations: Combines content-based recommendations with popularity-based ranking to suggest songs.
- Automatic Token Refresh: Automatically refreshes access tokens when they expire.

## Installation
### Prerequisites
- Python 3.x
- Spotify Developer Account (to get the Client ID and Client Secret)
- Flask
- Spotipy (Spotify Web API library)
- Scikit-learn (for scaling and similarity measures)
- Pandas (for data handling)

### Steps to Run
1. Clone the repository. Navigate to where you want the repo, and then execute the following commands:
```bash
git clone https://github.com/karadeskin/Music-Rec.git
cd Music-Rec
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install required Python packages.
You can install the required packages by running:
```bash
pip install pandas Flask requests spotipy scikit-learn urllib3 python-dotenv
```

4. Set up Spotify Developer Credentials.
In config.py, replace 'your_spotify_client_id' & 'your_spotify_client_secret' with your actual Client ID and Client Secret:
```
CLIENT_ID = 'your_spotify_client_id'
CLIENT_SECRET = 'your_spotify_client_secret'
```
You can access these credentials by creating an app as a spotify developer then viewing your Client ID and Client Secret. If you need help doing this, here is a helpful link: https://developer.spotify.com/documentation/web-api/concepts/apps 

5. Once everything is set up, you can run the Flask app using:
```bash
python(3) main.py
```
The app will be available at http://localhost:8888/

## Usage
1. Open your browser and navigate to http://localhost:8888/.
2. Click on "Login with Spotify" to authenticate with your Spotify account.
3. After logging in, you'll be redirected to a page where you can enter:
  - A Spotify playlist ID (from a public or private playlist).
  - A song name from that playlist to receive song recommendations.
4. Click "Get Recommendations" to view a list of recommended songs.

## API Documentation
### Routes
- /: Home page with the option to login using Spotify.
- /login: Initiates the OAuth login flow with Spotify.
- /callback: Handles the callback from Spotify's OAuth process.
- /playlists: Allows users to enter playlist ID and song name, and returns song recommendations.
- /refresh-token: Refreshes the access token if it has expired.

## Future Improvements
- Improve the UI.
- Add additional filters to recommendations (e.g., genre, mood, etc.).
- Query Spotify playlists. 
