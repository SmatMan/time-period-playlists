import datetime
import api
import time

print("Welcome.")
limit = int(input("How many top tracks to get?: "))
start = int(time.mktime(datetime.datetime.strptime(input("Start date (yyyy-mm-dd): "), "%Y-%m-%d").timetuple()))
end = int(time.mktime(datetime.datetime.strptime(input("End date (yyyy-mm-dd): "), "%Y-%m-%d").timetuple()))

print(start, end)

auth = api.spAuth() 

print("Getting top tracks...")
out = api.compileTracks(api.getTopTracks(start, end))

playlist = []

for i, track in enumerate(out):
    if i == limit:
        break
    print(f"Getting {track}...")
    
    rawTrack = api.spGetTrack(auth, track, out[track]["artist"], out[track]["album"])
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