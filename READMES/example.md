# Example Usage
What you will find in this example
* Creating an album named "test" if it doesn't exists already
* uploading media to google's servers
* using the upload token to "attach" uploaded media to  user's account and in this case also the specific album from earlier
```python
from gpsdk import GooglePhotos, Album, MediaItem, NewMediaItem, SimpleMediaItem
CLIENT_SECRETS="path to your client_secrets.json file"

gp = GooglePhotos(CLIENT_SECRETS)
album = Album.exists(gp, name="test")
if not album:
    album = Album.create(gp, "test")
token = MediaItem.upload_media(gp, "path_to_media_file.png")
items = MediaItem.batchCreate(
    gp,
    [
        NewMediaItem("description", SimpleMediaItem(token, "filename"))
    ],
    albumId=album.id
)
for item in items:
    print(item)

```