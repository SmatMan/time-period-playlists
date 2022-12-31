import datetime
import api
import time
import sys

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
    print(f"\nGetting {track}", end='\r')
    rawTrack = api.spGetTrack(auth, track, out[track]["artist"])
    if rawTrack is None:
        print(f"\n\033[1mCouldn't find {track} by {out[track]['artist']}. Consider adding it manually.\033[0m", end='\r')
        time.sleep(0.5)
        continue
    else:
        print(f"Matched {track} to {rawTrack[1]} by {rawTrack[2]}", end='\r')
        playlist.append(rawTrack[0])

print(playlist)

playlistData = []
playlistData.append(input("Playlist Name: "))
if "y" in input("Public? (y/n):").lower():
    playlistData.append("true")
else:
    playlistData.append("false")

playlistID = api.spCreatePlaylist(auth, playlistData)
print(api.spAddToPlaylist(auth, playlistID, playlist))