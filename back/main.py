import os
import json
import pygame
import asyncio
import socketio
import aiohttp_cors

from aiohttp import web
from typing import TypedDict, Literal


class Track(TypedDict):
    status: Literal["playing", "ended", "looping", "paused"]
    audio: str
    channel: pygame.mixer.Channel


pygame.init()
SOUND_LIST: dict[str, pygame.mixer.Sound] = {}
TRACKS: list[Track] = []

sio = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application()
cors = aiohttp_cors.setup(app)
sio.attach(app)


def find_track_index(sound_name: str):
    for i, t in enumerate(TRACKS):
        if t["audio"] == sound_name:
            return i
    else:
        return None


async def init():

    return app


async def index(request):
    """Serve the client-side application."""
    return web.Response(text="hi fuck you", content_type="text/html")


async def update(request: web.Request):
    sound_directory = os.listdir(os.path.join("assets", "sounds"))
    for file_name in sound_directory:
        if file_name not in SOUND_LIST.keys():
            SOUND_LIST[file_name] = pygame.mixer.Sound(
                os.path.join("assets", "sounds", file_name)
            )
    delete = []
    for fn in SOUND_LIST.keys():
        if fn not in sound_directory:
            delete.append(fn)
    for i in delete:
        SOUND_LIST.pop(i)

    remove_list = []
    for i, t in enumerate(TRACKS):
        if t["status"] != "paused" and not t["channel"].get_busy():
            t["status"] = "ended"
        if t["status"] == "ended":
            remove_list.append(i)
    for i in remove_list:
        TRACKS.pop(i)
    serializable = []
    for i in TRACKS:
        serializable.append({"status": i["status"], "audio": i["audio"]})

    return web.Response(
        body=json.dumps(
            {"available": list(SOUND_LIST.keys()), "playing": serializable}
        ),
        content_type="application/json",
    )


@sio.event
def connect(sid, environ):
    print("connect ", sid)


@sio.event
async def audio_operation(sid, data):
    match data["operation"].lower():
        case "pause":
            if TRACKS[data["affected"]]["status"] == "paused":
                TRACKS[data["affected"]]["channel"].unpause()
                TRACKS[data["affected"]]["status"] = "playing"
            else:
                TRACKS[data["affected"]]["channel"].pause()
                TRACKS[data["affected"]]["status"] = "paused"
        case "stop":
            TRACKS[data["affected"]]["channel"].stop()
            TRACKS[data["affected"]]["status"] = "ended"
        case "fade":
            TRACKS[data["affected"]]["channel"].fadeout(2000)
            TRACKS[data["affected"]]["status"] = "ended"
        case "loop":
            asyncio.get_event_loop().call_later(
                SOUND_LIST[TRACKS[data["affected"]]["audio"]].get_length() - 1,
                lambda: TRACKS[data["affected"]]["channel"].play(
                    SOUND_LIST[TRACKS[data["affected"]]["audio"]], loops=-1
                ),
            )


@sio.event
async def play_audio(sid, data):
    if data.lower() in SOUND_LIST.keys():
        channel = pygame.mixer.find_channel()
        TRACKS.append({"audio": data, "status": "playing", "channel": channel})
        channel.set_volume(1)
        channel.play(SOUND_LIST[data])


@sio.event
def disconnect(sid):
    print("disconnect ", sid)


resource = cors.add(app.router.add_resource("/update"))
route = cors.add(
    resource.add_route("GET", update), {"*": aiohttp_cors.ResourceOptions()}
)


if __name__ == "__main__":
    web.run_app(init(), host="FILL_YOUR_IP_HERE", port=6942)
