from enum import Enum, auto

APP_NAME = "youtube_cli"


class Event(Enum):

    NEXT = auto()
    PREV = auto()
    SHUFFLE = auto()
    REPEAT = auto()
    VOLUME = auto()
    PLAY = auto()
    PAUSE = auto()
    STOP = auto()
    SEEK = auto()


class PlayerStates(Enum):
    PLAYING = auto()
    PAUSED = auto()
    STOPPED = auto()


class RepeatStates(Enum):
    DISABLED = auto()
    SONG = auto()
    PLAYLIST = auto()
