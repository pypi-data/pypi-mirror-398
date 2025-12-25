from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class GDPRConsent(BaseModel):
    marketing: bool
    privacy: bool
    tos: bool
    origin: str = Field(alias="from")

class User(BaseModel):
    id: str = Field(alias="_id")
    email: str
    fullname: str = ""
    avatar: str = ""
    anonymous: bool
    gdpr_consent: GDPRConsent
    lang: str
    date_registered: datetime = Field(alias="dateRegistered")
    last_modified: datetime = Field(alias="lastModified")

class LibraryState(BaseModel):
    last_watched: Optional[datetime] = Field(None, alias="lastWatched")
    time_watched: int = Field(0, alias="timeWatched")
    time_offset: int = Field(0, alias="timeOffset")
    overall_time_watched: int = Field(0, alias="overallTimeWatched")
    times_watched: int = Field(0, alias="timesWatched")
    flagged_watched: int = Field(0, alias="flaggedWatched")
    duration: int = 0
    video_id: str = ""
    watched: str = ""
    no_notif: bool = Field(False, alias="noNotif")
    season: int = 0
    episode: int = 0

class LibraryItem(BaseModel):
    id: str = Field(alias="_id")
    removed: bool = False
    temp: bool = False
    ctime: Optional[datetime] = Field(None, alias="_ctime")
    mtime: Optional[datetime] = Field(None, alias="_mtime")
    state: LibraryState
    name: str
    type: str
    poster: str = ""
    poster_shape: str = Field("poster", alias="posterShape")
    background: str = ""
    logo: str = ""
    year: str = ""

class AddonManifest(BaseModel):
    id: str
    version: str
    name: str
    description: str = ""
    logo: Optional[str] = None
    background: Optional[str] = None
    types: List[str] = []
    resources: List[Any] = []
    id_prefixes: Optional[List[str]] = Field(None, alias="idPrefixes")
    catalogs: List[Dict[str, Any]] = []

class Addon(BaseModel):
    transport_url: str = Field(alias="transportUrl")
    transport_name: str = Field("", alias="transportName")
    manifest: AddonManifest
    flags: Dict[str, bool] = {}

class Stream(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    title: Optional[str] = None
    info_hash: Optional[str] = Field(None, alias="infoHash")
    file_index: Optional[int] = Field(None, alias="fileIdx")
    url: Optional[str] = None
    external_url: Optional[str] = Field(None, alias="externalUrl")
    yt_id: Optional[str] = Field(None, alias="ytId")
    behavior_hints: Dict[str, Any] = Field({}, alias="behaviorHints")

class Meta(BaseModel):
    id: str
    type: str
    name: str
    poster: Optional[str] = None
    background: Optional[str] = None
    logo: Optional[str] = None
    description: Optional[str] = None
    release_info: Optional[str] = Field(None, alias="releaseInfo")
    runtime: Optional[str] = None
    cast: List[str] = []
    director: List[str] = []
    writer: List[str] = []
    genres: List[str] = []
    country: Optional[str] = None
    imdb_rating: Optional[str] = Field(None, alias="imdbRating")
    awards: Optional[str] = None
    year: Optional[str] = None
    
    # Extra handling for flexibility
    class Config:
        populate_by_name = True
        extra = "ignore"
