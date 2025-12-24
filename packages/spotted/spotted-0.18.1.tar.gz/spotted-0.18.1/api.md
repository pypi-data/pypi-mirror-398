# Shared Types

```python
from spotted.types import (
    AlbumRestrictionObject,
    ArtistObject,
    AudiobookBase,
    AuthorObject,
    ChapterRestrictionObject,
    CopyrightObject,
    EpisodeObject,
    EpisodeRestrictionObject,
    ExternalIDObject,
    ExternalURLObject,
    FollowersObject,
    ImageObject,
    LinkedTrackObject,
    NarratorObject,
    PagingPlaylistObject,
    PlaylistTrackObject,
    PlaylistTracksRefObject,
    PlaylistUserObject,
    ResumePointObject,
    ShowBase,
    SimplifiedArtistObject,
    SimplifiedEpisodeObject,
    SimplifiedPlaylistObject,
    SimplifiedTrackObject,
    TrackObject,
    TrackRestrictionObject,
)
```

# Albums

Types:

```python
from spotted.types import AlbumRetrieveResponse, AlbumBulkRetrieveResponse
```

Methods:

- <code title="get /albums/{id}">client.albums.<a href="./src/spotted/resources/albums.py">retrieve</a>(id, \*\*<a href="src/spotted/types/album_retrieve_params.py">params</a>) -> <a href="./src/spotted/types/album_retrieve_response.py">AlbumRetrieveResponse</a></code>
- <code title="get /albums">client.albums.<a href="./src/spotted/resources/albums.py">bulk_retrieve</a>(\*\*<a href="src/spotted/types/album_bulk_retrieve_params.py">params</a>) -> <a href="./src/spotted/types/album_bulk_retrieve_response.py">AlbumBulkRetrieveResponse</a></code>
- <code title="get /albums/{id}/tracks">client.albums.<a href="./src/spotted/resources/albums.py">list_tracks</a>(id, \*\*<a href="src/spotted/types/album_list_tracks_params.py">params</a>) -> <a href="./src/spotted/types/shared/simplified_track_object.py">SyncCursorURLPage[SimplifiedTrackObject]</a></code>

# Artists

Types:

```python
from spotted.types import (
    ArtistBulkRetrieveResponse,
    ArtistListAlbumsResponse,
    ArtistListRelatedArtistsResponse,
    ArtistTopTracksResponse,
)
```

Methods:

- <code title="get /artists/{id}">client.artists.<a href="./src/spotted/resources/artists.py">retrieve</a>(id) -> <a href="./src/spotted/types/shared/artist_object.py">ArtistObject</a></code>
- <code title="get /artists">client.artists.<a href="./src/spotted/resources/artists.py">bulk_retrieve</a>(\*\*<a href="src/spotted/types/artist_bulk_retrieve_params.py">params</a>) -> <a href="./src/spotted/types/artist_bulk_retrieve_response.py">ArtistBulkRetrieveResponse</a></code>
- <code title="get /artists/{id}/albums">client.artists.<a href="./src/spotted/resources/artists.py">list_albums</a>(id, \*\*<a href="src/spotted/types/artist_list_albums_params.py">params</a>) -> <a href="./src/spotted/types/artist_list_albums_response.py">SyncCursorURLPage[ArtistListAlbumsResponse]</a></code>
- <code title="get /artists/{id}/related-artists">client.artists.<a href="./src/spotted/resources/artists.py">list_related_artists</a>(id) -> <a href="./src/spotted/types/artist_list_related_artists_response.py">ArtistListRelatedArtistsResponse</a></code>
- <code title="get /artists/{id}/top-tracks">client.artists.<a href="./src/spotted/resources/artists.py">top_tracks</a>(id, \*\*<a href="src/spotted/types/artist_top_tracks_params.py">params</a>) -> <a href="./src/spotted/types/artist_top_tracks_response.py">ArtistTopTracksResponse</a></code>

# Shows

Types:

```python
from spotted.types import ShowRetrieveResponse, ShowBulkRetrieveResponse
```

Methods:

- <code title="get /shows/{id}">client.shows.<a href="./src/spotted/resources/shows.py">retrieve</a>(id, \*\*<a href="src/spotted/types/show_retrieve_params.py">params</a>) -> <a href="./src/spotted/types/show_retrieve_response.py">ShowRetrieveResponse</a></code>
- <code title="get /shows">client.shows.<a href="./src/spotted/resources/shows.py">bulk_retrieve</a>(\*\*<a href="src/spotted/types/show_bulk_retrieve_params.py">params</a>) -> <a href="./src/spotted/types/show_bulk_retrieve_response.py">ShowBulkRetrieveResponse</a></code>
- <code title="get /shows/{id}/episodes">client.shows.<a href="./src/spotted/resources/shows.py">list_episodes</a>(id, \*\*<a href="src/spotted/types/show_list_episodes_params.py">params</a>) -> <a href="./src/spotted/types/shared/simplified_episode_object.py">SyncCursorURLPage[SimplifiedEpisodeObject]</a></code>

# Episodes

Types:

```python
from spotted.types import EpisodeBulkRetrieveResponse
```

Methods:

- <code title="get /episodes/{id}">client.episodes.<a href="./src/spotted/resources/episodes.py">retrieve</a>(id, \*\*<a href="src/spotted/types/episode_retrieve_params.py">params</a>) -> <a href="./src/spotted/types/shared/episode_object.py">EpisodeObject</a></code>
- <code title="get /episodes">client.episodes.<a href="./src/spotted/resources/episodes.py">bulk_retrieve</a>(\*\*<a href="src/spotted/types/episode_bulk_retrieve_params.py">params</a>) -> <a href="./src/spotted/types/episode_bulk_retrieve_response.py">EpisodeBulkRetrieveResponse</a></code>

# Audiobooks

Types:

```python
from spotted.types import (
    SimplifiedChapterObject,
    AudiobookRetrieveResponse,
    AudiobookBulkRetrieveResponse,
)
```

Methods:

- <code title="get /audiobooks/{id}">client.audiobooks.<a href="./src/spotted/resources/audiobooks.py">retrieve</a>(id, \*\*<a href="src/spotted/types/audiobook_retrieve_params.py">params</a>) -> <a href="./src/spotted/types/audiobook_retrieve_response.py">AudiobookRetrieveResponse</a></code>
- <code title="get /audiobooks">client.audiobooks.<a href="./src/spotted/resources/audiobooks.py">bulk_retrieve</a>(\*\*<a href="src/spotted/types/audiobook_bulk_retrieve_params.py">params</a>) -> <a href="./src/spotted/types/audiobook_bulk_retrieve_response.py">AudiobookBulkRetrieveResponse</a></code>
- <code title="get /audiobooks/{id}/chapters">client.audiobooks.<a href="./src/spotted/resources/audiobooks.py">list_chapters</a>(id, \*\*<a href="src/spotted/types/audiobook_list_chapters_params.py">params</a>) -> <a href="./src/spotted/types/simplified_chapter_object.py">SyncCursorURLPage[SimplifiedChapterObject]</a></code>

# Me

Types:

```python
from spotted.types import MeRetrieveResponse
```

Methods:

- <code title="get /me">client.me.<a href="./src/spotted/resources/me/me.py">retrieve</a>() -> <a href="./src/spotted/types/me_retrieve_response.py">MeRetrieveResponse</a></code>

## Audiobooks

Types:

```python
from spotted.types.me import AudiobookListResponse, AudiobookCheckResponse
```

Methods:

- <code title="get /me/audiobooks">client.me.audiobooks.<a href="./src/spotted/resources/me/audiobooks.py">list</a>(\*\*<a href="src/spotted/types/me/audiobook_list_params.py">params</a>) -> <a href="./src/spotted/types/me/audiobook_list_response.py">SyncCursorURLPage[AudiobookListResponse]</a></code>
- <code title="get /me/audiobooks/contains">client.me.audiobooks.<a href="./src/spotted/resources/me/audiobooks.py">check</a>(\*\*<a href="src/spotted/types/me/audiobook_check_params.py">params</a>) -> <a href="./src/spotted/types/me/audiobook_check_response.py">AudiobookCheckResponse</a></code>
- <code title="delete /me/audiobooks">client.me.audiobooks.<a href="./src/spotted/resources/me/audiobooks.py">remove</a>(\*\*<a href="src/spotted/types/me/audiobook_remove_params.py">params</a>) -> None</code>
- <code title="put /me/audiobooks">client.me.audiobooks.<a href="./src/spotted/resources/me/audiobooks.py">save</a>(\*\*<a href="src/spotted/types/me/audiobook_save_params.py">params</a>) -> None</code>

## Playlists

Methods:

- <code title="get /me/playlists">client.me.playlists.<a href="./src/spotted/resources/me/playlists.py">list</a>(\*\*<a href="src/spotted/types/me/playlist_list_params.py">params</a>) -> <a href="./src/spotted/types/shared/simplified_playlist_object.py">SyncCursorURLPage[SimplifiedPlaylistObject]</a></code>

## Top

Methods:

- <code title="get /me/top/artists">client.me.top.<a href="./src/spotted/resources/me/top.py">list_top_artists</a>(\*\*<a href="src/spotted/types/me/top_list_top_artists_params.py">params</a>) -> <a href="./src/spotted/types/shared/artist_object.py">SyncCursorURLPage[ArtistObject]</a></code>
- <code title="get /me/top/tracks">client.me.top.<a href="./src/spotted/resources/me/top.py">list_top_tracks</a>(\*\*<a href="src/spotted/types/me/top_list_top_tracks_params.py">params</a>) -> <a href="./src/spotted/types/shared/track_object.py">SyncCursorURLPage[TrackObject]</a></code>

## Albums

Types:

```python
from spotted.types.me import AlbumListResponse, AlbumCheckResponse
```

Methods:

- <code title="get /me/albums">client.me.albums.<a href="./src/spotted/resources/me/albums.py">list</a>(\*\*<a href="src/spotted/types/me/album_list_params.py">params</a>) -> <a href="./src/spotted/types/me/album_list_response.py">SyncCursorURLPage[AlbumListResponse]</a></code>
- <code title="get /me/albums/contains">client.me.albums.<a href="./src/spotted/resources/me/albums.py">check</a>(\*\*<a href="src/spotted/types/me/album_check_params.py">params</a>) -> <a href="./src/spotted/types/me/album_check_response.py">AlbumCheckResponse</a></code>
- <code title="delete /me/albums">client.me.albums.<a href="./src/spotted/resources/me/albums.py">remove</a>(\*\*<a href="src/spotted/types/me/album_remove_params.py">params</a>) -> None</code>
- <code title="put /me/albums">client.me.albums.<a href="./src/spotted/resources/me/albums.py">save</a>(\*\*<a href="src/spotted/types/me/album_save_params.py">params</a>) -> None</code>

## Tracks

Types:

```python
from spotted.types.me import TrackListResponse, TrackCheckResponse
```

Methods:

- <code title="get /me/tracks">client.me.tracks.<a href="./src/spotted/resources/me/tracks.py">list</a>(\*\*<a href="src/spotted/types/me/track_list_params.py">params</a>) -> <a href="./src/spotted/types/me/track_list_response.py">SyncCursorURLPage[TrackListResponse]</a></code>
- <code title="get /me/tracks/contains">client.me.tracks.<a href="./src/spotted/resources/me/tracks.py">check</a>(\*\*<a href="src/spotted/types/me/track_check_params.py">params</a>) -> <a href="./src/spotted/types/me/track_check_response.py">TrackCheckResponse</a></code>
- <code title="delete /me/tracks">client.me.tracks.<a href="./src/spotted/resources/me/tracks.py">remove</a>(\*\*<a href="src/spotted/types/me/track_remove_params.py">params</a>) -> None</code>
- <code title="put /me/tracks">client.me.tracks.<a href="./src/spotted/resources/me/tracks.py">save</a>(\*\*<a href="src/spotted/types/me/track_save_params.py">params</a>) -> None</code>

## Episodes

Types:

```python
from spotted.types.me import EpisodeListResponse, EpisodeCheckResponse
```

Methods:

- <code title="get /me/episodes">client.me.episodes.<a href="./src/spotted/resources/me/episodes.py">list</a>(\*\*<a href="src/spotted/types/me/episode_list_params.py">params</a>) -> <a href="./src/spotted/types/me/episode_list_response.py">SyncCursorURLPage[EpisodeListResponse]</a></code>
- <code title="get /me/episodes/contains">client.me.episodes.<a href="./src/spotted/resources/me/episodes.py">check</a>(\*\*<a href="src/spotted/types/me/episode_check_params.py">params</a>) -> <a href="./src/spotted/types/me/episode_check_response.py">EpisodeCheckResponse</a></code>
- <code title="delete /me/episodes">client.me.episodes.<a href="./src/spotted/resources/me/episodes.py">remove</a>(\*\*<a href="src/spotted/types/me/episode_remove_params.py">params</a>) -> None</code>
- <code title="put /me/episodes">client.me.episodes.<a href="./src/spotted/resources/me/episodes.py">save</a>(\*\*<a href="src/spotted/types/me/episode_save_params.py">params</a>) -> None</code>

## Shows

Types:

```python
from spotted.types.me import ShowListResponse, ShowCheckResponse
```

Methods:

- <code title="get /me/shows">client.me.shows.<a href="./src/spotted/resources/me/shows.py">list</a>(\*\*<a href="src/spotted/types/me/show_list_params.py">params</a>) -> <a href="./src/spotted/types/me/show_list_response.py">SyncCursorURLPage[ShowListResponse]</a></code>
- <code title="get /me/shows/contains">client.me.shows.<a href="./src/spotted/resources/me/shows.py">check</a>(\*\*<a href="src/spotted/types/me/show_check_params.py">params</a>) -> <a href="./src/spotted/types/me/show_check_response.py">ShowCheckResponse</a></code>
- <code title="delete /me/shows">client.me.shows.<a href="./src/spotted/resources/me/shows.py">remove</a>(\*\*<a href="src/spotted/types/me/show_remove_params.py">params</a>) -> None</code>
- <code title="put /me/shows">client.me.shows.<a href="./src/spotted/resources/me/shows.py">save</a>(\*\*<a href="src/spotted/types/me/show_save_params.py">params</a>) -> None</code>

## Following

Types:

```python
from spotted.types.me import FollowingBulkRetrieveResponse, FollowingCheckResponse
```

Methods:

- <code title="get /me/following">client.me.following.<a href="./src/spotted/resources/me/following.py">bulk_retrieve</a>(\*\*<a href="src/spotted/types/me/following_bulk_retrieve_params.py">params</a>) -> <a href="./src/spotted/types/me/following_bulk_retrieve_response.py">FollowingBulkRetrieveResponse</a></code>
- <code title="get /me/following/contains">client.me.following.<a href="./src/spotted/resources/me/following.py">check</a>(\*\*<a href="src/spotted/types/me/following_check_params.py">params</a>) -> <a href="./src/spotted/types/me/following_check_response.py">FollowingCheckResponse</a></code>
- <code title="put /me/following">client.me.following.<a href="./src/spotted/resources/me/following.py">follow</a>(\*\*<a href="src/spotted/types/me/following_follow_params.py">params</a>) -> None</code>
- <code title="delete /me/following">client.me.following.<a href="./src/spotted/resources/me/following.py">unfollow</a>(\*\*<a href="src/spotted/types/me/following_unfollow_params.py">params</a>) -> None</code>

## Player

Types:

```python
from spotted.types.me import (
    ContextObject,
    DeviceObject,
    PlayerGetCurrentlyPlayingResponse,
    PlayerGetDevicesResponse,
    PlayerGetStateResponse,
    PlayerListRecentlyPlayedResponse,
)
```

Methods:

- <code title="get /me/player/currently-playing">client.me.player.<a href="./src/spotted/resources/me/player/player.py">get_currently_playing</a>(\*\*<a href="src/spotted/types/me/player_get_currently_playing_params.py">params</a>) -> <a href="./src/spotted/types/me/player_get_currently_playing_response.py">PlayerGetCurrentlyPlayingResponse</a></code>
- <code title="get /me/player/devices">client.me.player.<a href="./src/spotted/resources/me/player/player.py">get_devices</a>() -> <a href="./src/spotted/types/me/player_get_devices_response.py">PlayerGetDevicesResponse</a></code>
- <code title="get /me/player">client.me.player.<a href="./src/spotted/resources/me/player/player.py">get_state</a>(\*\*<a href="src/spotted/types/me/player_get_state_params.py">params</a>) -> <a href="./src/spotted/types/me/player_get_state_response.py">PlayerGetStateResponse</a></code>
- <code title="get /me/player/recently-played">client.me.player.<a href="./src/spotted/resources/me/player/player.py">list_recently_played</a>(\*\*<a href="src/spotted/types/me/player_list_recently_played_params.py">params</a>) -> <a href="./src/spotted/types/me/player_list_recently_played_response.py">SyncCursorURLPage[PlayerListRecentlyPlayedResponse]</a></code>
- <code title="put /me/player/pause">client.me.player.<a href="./src/spotted/resources/me/player/player.py">pause_playback</a>(\*\*<a href="src/spotted/types/me/player_pause_playback_params.py">params</a>) -> None</code>
- <code title="put /me/player/seek">client.me.player.<a href="./src/spotted/resources/me/player/player.py">seek_to_position</a>(\*\*<a href="src/spotted/types/me/player_seek_to_position_params.py">params</a>) -> None</code>
- <code title="put /me/player/repeat">client.me.player.<a href="./src/spotted/resources/me/player/player.py">set_repeat_mode</a>(\*\*<a href="src/spotted/types/me/player_set_repeat_mode_params.py">params</a>) -> None</code>
- <code title="put /me/player/volume">client.me.player.<a href="./src/spotted/resources/me/player/player.py">set_volume</a>(\*\*<a href="src/spotted/types/me/player_set_volume_params.py">params</a>) -> None</code>
- <code title="post /me/player/next">client.me.player.<a href="./src/spotted/resources/me/player/player.py">skip_next</a>(\*\*<a href="src/spotted/types/me/player_skip_next_params.py">params</a>) -> None</code>
- <code title="post /me/player/previous">client.me.player.<a href="./src/spotted/resources/me/player/player.py">skip_previous</a>(\*\*<a href="src/spotted/types/me/player_skip_previous_params.py">params</a>) -> None</code>
- <code title="put /me/player/play">client.me.player.<a href="./src/spotted/resources/me/player/player.py">start_playback</a>(\*\*<a href="src/spotted/types/me/player_start_playback_params.py">params</a>) -> None</code>
- <code title="put /me/player/shuffle">client.me.player.<a href="./src/spotted/resources/me/player/player.py">toggle_shuffle</a>(\*\*<a href="src/spotted/types/me/player_toggle_shuffle_params.py">params</a>) -> None</code>
- <code title="put /me/player">client.me.player.<a href="./src/spotted/resources/me/player/player.py">transfer</a>(\*\*<a href="src/spotted/types/me/player_transfer_params.py">params</a>) -> None</code>

### Queue

Types:

```python
from spotted.types.me.player import QueueGetResponse
```

Methods:

- <code title="post /me/player/queue">client.me.player.queue.<a href="./src/spotted/resources/me/player/queue.py">add</a>(\*\*<a href="src/spotted/types/me/player/queue_add_params.py">params</a>) -> None</code>
- <code title="get /me/player/queue">client.me.player.queue.<a href="./src/spotted/resources/me/player/queue.py">get</a>() -> <a href="./src/spotted/types/me/player/queue_get_response.py">QueueGetResponse</a></code>

# Chapters

Types:

```python
from spotted.types import ChapterRetrieveResponse, ChapterBulkRetrieveResponse
```

Methods:

- <code title="get /chapters/{id}">client.chapters.<a href="./src/spotted/resources/chapters.py">retrieve</a>(id, \*\*<a href="src/spotted/types/chapter_retrieve_params.py">params</a>) -> <a href="./src/spotted/types/chapter_retrieve_response.py">ChapterRetrieveResponse</a></code>
- <code title="get /chapters">client.chapters.<a href="./src/spotted/resources/chapters.py">bulk_retrieve</a>(\*\*<a href="src/spotted/types/chapter_bulk_retrieve_params.py">params</a>) -> <a href="./src/spotted/types/chapter_bulk_retrieve_response.py">ChapterBulkRetrieveResponse</a></code>

# Tracks

Types:

```python
from spotted.types import TrackBulkRetrieveResponse
```

Methods:

- <code title="get /tracks/{id}">client.tracks.<a href="./src/spotted/resources/tracks.py">retrieve</a>(id, \*\*<a href="src/spotted/types/track_retrieve_params.py">params</a>) -> <a href="./src/spotted/types/shared/track_object.py">TrackObject</a></code>
- <code title="get /tracks">client.tracks.<a href="./src/spotted/resources/tracks.py">bulk_retrieve</a>(\*\*<a href="src/spotted/types/track_bulk_retrieve_params.py">params</a>) -> <a href="./src/spotted/types/track_bulk_retrieve_response.py">TrackBulkRetrieveResponse</a></code>

# Search

Types:

```python
from spotted.types import SearchQueryResponse
```

Methods:

- <code title="get /search">client.search.<a href="./src/spotted/resources/search.py">query</a>(\*\*<a href="src/spotted/types/search_query_params.py">params</a>) -> <a href="./src/spotted/types/search_query_response.py">SearchQueryResponse</a></code>

# Playlists

Types:

```python
from spotted.types import PlaylistRetrieveResponse
```

Methods:

- <code title="get /playlists/{playlist_id}">client.playlists.<a href="./src/spotted/resources/playlists/playlists.py">retrieve</a>(playlist_id, \*\*<a href="src/spotted/types/playlist_retrieve_params.py">params</a>) -> <a href="./src/spotted/types/playlist_retrieve_response.py">PlaylistRetrieveResponse</a></code>
- <code title="put /playlists/{playlist_id}">client.playlists.<a href="./src/spotted/resources/playlists/playlists.py">update</a>(playlist_id, \*\*<a href="src/spotted/types/playlist_update_params.py">params</a>) -> None</code>

## Tracks

Types:

```python
from spotted.types.playlists import TrackUpdateResponse, TrackAddResponse, TrackRemoveResponse
```

Methods:

- <code title="put /playlists/{playlist_id}/tracks">client.playlists.tracks.<a href="./src/spotted/resources/playlists/tracks.py">update</a>(playlist_id, \*\*<a href="src/spotted/types/playlists/track_update_params.py">params</a>) -> <a href="./src/spotted/types/playlists/track_update_response.py">TrackUpdateResponse</a></code>
- <code title="get /playlists/{playlist_id}/tracks">client.playlists.tracks.<a href="./src/spotted/resources/playlists/tracks.py">list</a>(playlist_id, \*\*<a href="src/spotted/types/playlists/track_list_params.py">params</a>) -> <a href="./src/spotted/types/shared/playlist_track_object.py">SyncCursorURLPage[PlaylistTrackObject]</a></code>
- <code title="post /playlists/{playlist_id}/tracks">client.playlists.tracks.<a href="./src/spotted/resources/playlists/tracks.py">add</a>(playlist_id, \*\*<a href="src/spotted/types/playlists/track_add_params.py">params</a>) -> <a href="./src/spotted/types/playlists/track_add_response.py">TrackAddResponse</a></code>
- <code title="delete /playlists/{playlist_id}/tracks">client.playlists.tracks.<a href="./src/spotted/resources/playlists/tracks.py">remove</a>(playlist_id, \*\*<a href="src/spotted/types/playlists/track_remove_params.py">params</a>) -> <a href="./src/spotted/types/playlists/track_remove_response.py">TrackRemoveResponse</a></code>

## Followers

Types:

```python
from spotted.types.playlists import FollowerCheckResponse
```

Methods:

- <code title="get /playlists/{playlist_id}/followers/contains">client.playlists.followers.<a href="./src/spotted/resources/playlists/followers.py">check</a>(playlist_id, \*\*<a href="src/spotted/types/playlists/follower_check_params.py">params</a>) -> <a href="./src/spotted/types/playlists/follower_check_response.py">FollowerCheckResponse</a></code>
- <code title="put /playlists/{playlist_id}/followers">client.playlists.followers.<a href="./src/spotted/resources/playlists/followers.py">follow</a>(playlist_id, \*\*<a href="src/spotted/types/playlists/follower_follow_params.py">params</a>) -> None</code>
- <code title="delete /playlists/{playlist_id}/followers">client.playlists.followers.<a href="./src/spotted/resources/playlists/followers.py">unfollow</a>(playlist_id) -> None</code>

## Images

Types:

```python
from spotted.types.playlists import ImageListResponse
```

Methods:

- <code title="put /playlists/{playlist_id}/images">client.playlists.images.<a href="./src/spotted/resources/playlists/images.py">update</a>(playlist_id, body, \*\*<a href="src/spotted/types/playlists/image_update_params.py">params</a>) -> BinaryAPIResponse</code>
- <code title="get /playlists/{playlist_id}/images">client.playlists.images.<a href="./src/spotted/resources/playlists/images.py">list</a>(playlist_id) -> <a href="./src/spotted/types/playlists/image_list_response.py">ImageListResponse</a></code>

# Users

Types:

```python
from spotted.types import UserRetrieveProfileResponse
```

Methods:

- <code title="get /users/{user_id}">client.users.<a href="./src/spotted/resources/users/users.py">retrieve_profile</a>(user_id) -> <a href="./src/spotted/types/user_retrieve_profile_response.py">UserRetrieveProfileResponse</a></code>

## Playlists

Types:

```python
from spotted.types.users import PlaylistCreateResponse
```

Methods:

- <code title="post /users/{user_id}/playlists">client.users.playlists.<a href="./src/spotted/resources/users/playlists.py">create</a>(user_id, \*\*<a href="src/spotted/types/users/playlist_create_params.py">params</a>) -> <a href="./src/spotted/types/users/playlist_create_response.py">PlaylistCreateResponse</a></code>
- <code title="get /users/{user_id}/playlists">client.users.playlists.<a href="./src/spotted/resources/users/playlists.py">list</a>(user_id, \*\*<a href="src/spotted/types/users/playlist_list_params.py">params</a>) -> <a href="./src/spotted/types/shared/simplified_playlist_object.py">SyncCursorURLPage[SimplifiedPlaylistObject]</a></code>

# Browse

Types:

```python
from spotted.types import BrowseGetFeaturedPlaylistsResponse, BrowseGetNewReleasesResponse
```

Methods:

- <code title="get /browse/featured-playlists">client.browse.<a href="./src/spotted/resources/browse/browse.py">get_featured_playlists</a>(\*\*<a href="src/spotted/types/browse_get_featured_playlists_params.py">params</a>) -> <a href="./src/spotted/types/browse_get_featured_playlists_response.py">BrowseGetFeaturedPlaylistsResponse</a></code>
- <code title="get /browse/new-releases">client.browse.<a href="./src/spotted/resources/browse/browse.py">get_new_releases</a>(\*\*<a href="src/spotted/types/browse_get_new_releases_params.py">params</a>) -> <a href="./src/spotted/types/browse_get_new_releases_response.py">BrowseGetNewReleasesResponse</a></code>

## Categories

Types:

```python
from spotted.types.browse import (
    CategoryRetrieveResponse,
    CategoryListResponse,
    CategoryGetPlaylistsResponse,
)
```

Methods:

- <code title="get /browse/categories/{category_id}">client.browse.categories.<a href="./src/spotted/resources/browse/categories.py">retrieve</a>(category_id, \*\*<a href="src/spotted/types/browse/category_retrieve_params.py">params</a>) -> <a href="./src/spotted/types/browse/category_retrieve_response.py">CategoryRetrieveResponse</a></code>
- <code title="get /browse/categories">client.browse.categories.<a href="./src/spotted/resources/browse/categories.py">list</a>(\*\*<a href="src/spotted/types/browse/category_list_params.py">params</a>) -> <a href="./src/spotted/types/browse/category_list_response.py">SyncCursorURLPage[CategoryListResponse]</a></code>
- <code title="get /browse/categories/{category_id}/playlists">client.browse.categories.<a href="./src/spotted/resources/browse/categories.py">get_playlists</a>(category_id, \*\*<a href="src/spotted/types/browse/category_get_playlists_params.py">params</a>) -> <a href="./src/spotted/types/browse/category_get_playlists_response.py">CategoryGetPlaylistsResponse</a></code>

# AudioFeatures

Types:

```python
from spotted.types import AudioFeatureRetrieveResponse, AudioFeatureBulkRetrieveResponse
```

Methods:

- <code title="get /audio-features/{id}">client.audio_features.<a href="./src/spotted/resources/audio_features.py">retrieve</a>(id) -> <a href="./src/spotted/types/audio_feature_retrieve_response.py">AudioFeatureRetrieveResponse</a></code>
- <code title="get /audio-features">client.audio_features.<a href="./src/spotted/resources/audio_features.py">bulk_retrieve</a>(\*\*<a href="src/spotted/types/audio_feature_bulk_retrieve_params.py">params</a>) -> <a href="./src/spotted/types/audio_feature_bulk_retrieve_response.py">AudioFeatureBulkRetrieveResponse</a></code>

# AudioAnalysis

Types:

```python
from spotted.types import TimeIntervalObject, AudioAnalysisRetrieveResponse
```

Methods:

- <code title="get /audio-analysis/{id}">client.audio_analysis.<a href="./src/spotted/resources/audio_analysis.py">retrieve</a>(id) -> <a href="./src/spotted/types/audio_analysis_retrieve_response.py">AudioAnalysisRetrieveResponse</a></code>

# Recommendations

Types:

```python
from spotted.types import RecommendationGetResponse, RecommendationListAvailableGenreSeedsResponse
```

Methods:

- <code title="get /recommendations">client.recommendations.<a href="./src/spotted/resources/recommendations.py">get</a>(\*\*<a href="src/spotted/types/recommendation_get_params.py">params</a>) -> <a href="./src/spotted/types/recommendation_get_response.py">RecommendationGetResponse</a></code>
- <code title="get /recommendations/available-genre-seeds">client.recommendations.<a href="./src/spotted/resources/recommendations.py">list_available_genre_seeds</a>() -> <a href="./src/spotted/types/recommendation_list_available_genre_seeds_response.py">RecommendationListAvailableGenreSeedsResponse</a></code>

# Markets

Types:

```python
from spotted.types import MarketListResponse
```

Methods:

- <code title="get /markets">client.markets.<a href="./src/spotted/resources/markets.py">list</a>() -> <a href="./src/spotted/types/market_list_response.py">MarketListResponse</a></code>
