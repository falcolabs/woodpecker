import os
import json
import pygame
import asyncio
import socketio  # type: ignore
import aiohttp_cors  # type: ignore

from aiohttp import web
from typing import Any, TypedDict, Literal


class Track(TypedDict):
    status: Literal["playing", "ended", "looping", "paused"]
    audio: str
    channel: pygame.mixer.Channel


class UpdateRequest(TypedDict):
    operation: str
    value: Any


pygame.init()
SOUND_LIST: dict[str, pygame.mixer.Sound] = {}
TRACKS: list[Track] = []
volume = 1

sio = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application()
cors = aiohttp_cors.setup(app)
sio.attach(app)  # type: ignore


def find_track_index(sound_name: str):
    for i, t in enumerate(TRACKS):
        if t["audio"] == sound_name:
            return i
    else:
        return None


async def init():

    return app


async def index(_):
    """Serve the client-side application."""
    return web.Response(text="hi fuck you", content_type="text/html")


async def update(_):
    sound_directory = os.listdir(os.path.join("assets", "sounds"))
    for file_name in sound_directory:
        if file_name not in SOUND_LIST.keys():
            SOUND_LIST[file_name] = pygame.mixer.Sound(
                os.path.join("assets", "sounds", file_name)
            )
    delete: list[str] = []
    for fn in SOUND_LIST.keys():
        if fn not in sound_directory:
            delete.append(fn)
    for i in delete:
        SOUND_LIST.pop(i)

    remove_list: list[int] = []
    for i, t in enumerate(TRACKS):
        if t["status"] != "paused" and not t["channel"].get_busy():
            t["status"] = "ended"
        if t["status"] == "ended":
            remove_list.append(i)
    for i in remove_list:
        TRACKS.pop(i)

    serializable: list[dict[str, str]] = []
    for i in TRACKS:
        i["channel"].set_volume(volume)
        serializable.append({"status": i["status"], "audio": i["audio"]})

    return web.Response(
        body=json.dumps(
            {"available": list(SOUND_LIST.keys()), "playing": serializable}
        ),
        content_type="application/json",
    )


@sio.event  # type: ignore
def connect(sid: int, _):
    print("connect ", sid)


@sio.event  # type: ignore
async def audio_operation(sid: int, data: UpdateRequest):
    match data["operation"].lower():
        case "pause":
            if TRACKS[data["value"]]["status"] == "paused":
                TRACKS[data["value"]]["channel"].unpause()  # type: ignore
                TRACKS[data["value"]]["status"] = "playing"
            else:
                TRACKS[data["value"]]["channel"].pause()  # type: ignore
                TRACKS[data["value"]]["status"] = "paused"
        case "stop":
            TRACKS[data["value"]]["channel"].stop()  # type: ignore
            TRACKS[data["value"]]["status"] = "ended"
        case "fade":
            TRACKS[data["value"]]["channel"].fadeout(2000)  # type: ignore
            TRACKS[data["value"]]["status"] = "ended"
        case "togloop":
            if TRACKS[data["value"]]["status"] == "looping":
                asyncio.get_event_loop().call_later(
                    SOUND_LIST[TRACKS[data["value"]]["audio"]].get_length() - 1,  # type: ignore
                    lambda: TRACKS[data["value"]]["channel"].play(  # type: ignore
                        SOUND_LIST[TRACKS[data["value"]]["audio"]], loops=1  # type: ignore
                    ),
                )
            else:
                asyncio.get_event_loop().call_later(
                    SOUND_LIST[TRACKS[data["value"]]["audio"]].get_length() - 1,  # type: ignore
                    lambda: TRACKS[data["value"]]["channel"].play(  # type: ignore
                        SOUND_LIST[TRACKS[data["value"]]["audio"]], loops=-1  # type: ignore
                    ),
                )
                TRACKS[data["value"]]["status"] = "looping"
        case "volume":
            global volume
            volume = float(data["value"])
        case _:
            pass


@sio.event  # type: ignore
async def play_audio(sid: int, data: str):
    if data.lower() in SOUND_LIST.keys():
        channel = pygame.mixer.find_channel()
        TRACKS.append({"audio": data, "status": "playing", "channel": channel})
        channel.set_volume(1)
        channel.play(SOUND_LIST[data])


@sio.event  # type: ignore
def disconnect(sid: int):
    print("disconnect ", sid)


resource = cors.add(app.router.add_resource("/update"))  # type: ignore
route = cors.add(  # type: ignore
    resource.add_route("GET", update), {"*": aiohttp_cors.ResourceOptions()}  # type: ignore
)


if __name__ == "__main__":
    web.run_app(init(), host="FILL_YOUR_IP_HERE", port=6942)  # type: ignore
