import requests
import config as cfg
import datetime
from collections import OrderedDict
import json

def save(inp): # debug save
    with open("test.json", "w") as f:
        f.write(inp)

def getDefaultTopTracks(user=cfg.lastFmUser, timePeriod="1month"): # get top tracks of a user based on last.fm's charts
    url = f"http://ws.audioscrobbler.com/2.0/?method=user.gettoptracks&user={user}&api_key={cfg.lfmkey}&period={timePeriod}&format=json"
    r = requests.get(url)
    save(r.text)

def getTopTracks(start, end, user=cfg.lastFmUser):
    # convert start and end to unix timestamps
    start = int(start.timestamp())
    end = int(end.timestamp())
    print(start, end)
    url = f"http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={user}&from={start}&to={end}&api_key={cfg.lfmkey}&format=json"
    r = requests.get(url).json()
    if r["recenttracks"]["@attr"]["total"] == "0": # if no tracks were played
        return None

    # if first track being played
    try:
        if r["recenttracks"]["track"][0]["@attr"] is not None and r["recenttracks"]["track"][0]["@attr"]["nowplaying"] == "true":
            r["recenttracks"]["track"].pop(0) # remove it
    except KeyError:
        pass

    if int(r["recenttracks"]["@attr"]["totalPages"]) <= 1: # if only one page of tracks
        return r["recenttracks"]["track"]
    else: # if more than one page of tracks
        tracks = []
        for page in range(1, int(r["recenttracks"]["@attr"]["totalPages"])+1):
            url = f"http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={user}&from={start}&to={end}&api_key={cfg.lfmkey}&format=json&page={page}"
            r = requests.get(url).json()

            try:
                if r["recenttracks"]["track"][0]["@attr"] is not None and r["recenttracks"]["track"][0]["@attr"]["nowplaying"] == "true":
                    r["recenttracks"]["track"].pop(0) # remove it
            except KeyError:
                pass

            tracks += r["recenttracks"]["track"]
        print(r["recenttracks"]["@attr"])
        return tracks

def compileTracks(tracks):
    compiledTracks = {}
    sortedTracks = {}
    for track in tracks:
        if track["name"] not in compiledTracks: # if track is not in list
            compiledTracks[track["name"]] = {"artist": track["artist"]["#text"], "album": track["album"]["#text"], "streams": 1} # add it
        else: # otherwise
            compiledTracks[track["name"]]["streams"] += 1 # up the streamcount by 1
    
    # sort the tracks by streamcount
    sortedTracks = OrderedDict(sorted(compiledTracks.items(), key=lambda x: x[1]["streams"], reverse=True))
    return sortedTracks 

def spAuth():
    with open("spotifyCreds.json", "r+") as f:
        creds = json.load(f)

    if int(creds["expiry"]) < int(datetime.datetime.now().timestamp()): # if creds have expired
        url = "https://accounts.spotify.com/authorize"
        params = {
            "client_id": cfg.spId,
            "response_type": "code",
            "redirect_uri": "http://localhost:8888/callback",
            "scope": "user-read-private user-read-email playlist-modify-public playlist-modify-private"
        }
        r = requests.get(url, params=params)
        print(f"Please go to this URL: \n{r.url}.")
        code = input("Sign in, and paste the code here: ")
        code = code.split("?code=")[1]
        print(code)
        url = "https://accounts.spotify.com/api/token"
        params = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "http://localhost:8888/callback",
            "client_id": cfg.spId,
            "client_secret": cfg.spSecret
        }
        r = requests.post(url, data=params)
        print(r.text)
        creds = r.json()

        url = f"https://api.spotify.com/v1/me"
        userid = requests.get(url, headers={"Authorization": f"Bearer {creds['access_token']}"}).json()["id"]

        with open("spotifyCreds.json", "w") as f:
            creds["expiry"] = str(int((datetime.datetime.now().timestamp() + creds["expires_in"])))
            creds["userid"] = userid
            json.dump(creds, f)
        return {"token": creds["access_token"], "userid": userid}
    else:
        print("Creds are still valid.")
        return {"token": creds["access_token"], "userid": creds["userid"]}



def spGetTrack(auth, track, artist, album):
    url = f"https://api.spotify.com/v1/search?q=track:{track}%20artist:{artist}&type=track&limit=1"
    r = requests.get(url, headers={"Authorization": f"Bearer {auth['token']}"}).json()
    try:
        return r["tracks"]["items"][0]["uri"]
    except IndexError:
        return r

def spCreatePlaylist(auth, data): 
    url = f"https://api.spotify.com/v1/users/{auth['userid']}/playlists"
    params = {
        "name": data[0],
        "public": data[1],
    }
    r = requests.post(url, headers={"Authorization": f"Bearer {auth['token']}"}, data=json.dumps(params)).json()
    print(r)
    return r["id"]

def spAddToPlaylist(auth, playlistID, tracks):
    url = f"https://api.spotify.com/v1/playlists/{playlistID}/tracks"
    params = {
        "uris": tracks,
    }
    r = requests.post(url, headers={"Authorization": f"Bearer {auth['token']}"}, data=json.dumps(params)).json()
    return r
#save(str(getTopTracks(start=datetime.datetime(2021, 2, 1), end=datetime.datetime(2021, 2, 28))))

out = compileTracks(getTopTracks(start=datetime.datetime(2022, 2, 1), end=datetime.datetime(2022, 2, 28)))

auth = spAuth()

playlist = []

# get top 10 tracks
for i, track in enumerate(out):
    if i == 10:
        break
    print(f"Getting {track}...")
    
    rawTrack = spGetTrack(auth, track, out[track]["artist"], out[track]["album"])
    print(rawTrack)
    playlist.append(rawTrack)

print(playlist)

playlistData = []
playlistData.append(input("Playlist Name: "))
if "y" in input("Public?").lower():
    playlistData.append("true")
else:
    playlistData.append("false")

playlistID = spCreatePlaylist(auth, playlistData)
print(spAddToPlaylist(auth, playlistID, playlist))