# plottwist
# Ivan Markin 12/2025

import base64
import msgpack
import zlib

import matplotlib.patches as patches

from pathlib import Path
from typing import Union, IO

def encode(data):
    packed_data = zlib.compress(msgpack.packb(data))
    encoded_data = "plottwist:"+base64.b64encode(packed_data).decode("utf-8")
    url = "https://github.com/unkaktus/plottwist#"+encoded_data
    return url

def decode(url):
    b64data = url.split("plottwist:")[1].split()[0]
    packed = base64.b64decode(bytes(b64data, "utf-8"))
    data = msgpack.unpackb(zlib.decompress(packed))
    return data

class PlotTwist:
    def __init__(self, ax):
        self.ax = ax
        self.data = {
            "metadata": {
                "software": "https://github.com/unkaktus/plottwist",
                },
            "artists": [],
            }

    def add_author(self, author):
        if "authors" not in self.data["metadata"]:
            self.data["metadata"]["authors"] = []
        self.data["metadata"]["authors"] += [author]

    def add_reference(self, reference):
        if "references" not in self.data["metadata"]:
            self.data["metadata"]["references"] = []
        self.data["metadata"]["references"] += [reference]

    def plot(self, x, y, **kwargs):
        ret = self.ax.plot(x,y, **kwargs)
        artist = {"func":"plot", "x": list(x), "y": list(y), "kwargs": kwargs}
        self.data["artists"] += [artist]
        return ret

    def scatter(self, x, y, **kwargs):
        ret = self.ax.scatter(x,y, **kwargs)
        artist = {"func":"scatter", "x": list(x), "y": list(y), "kwargs": kwargs}
        self.data["artists"] += [artist]
        return ret

    def axhline(self, y, **kwargs):
        ret = self.ax.axhline(y, **kwargs)
        artist = {"func":"axhline", "y": y, "kwargs": kwargs}
        self.data["artists"] += [artist]
        return ret

    def axvline(self, x, **kwargs):
        ret = self.ax.axvline(x, **kwargs)
        artist = {"func":"axvline", "x": x, "kwargs": kwargs}
        self.data["artists"] += [artist]
        return ret

    def legend(self, **kwargs):
        ret = self.ax.legend(**kwargs)
        artist = {"func":"legend", "kwargs": kwargs}
        self.data["artists"] += [artist]
        return ret

    def plot_badge(self, x,y, **kwargs):
        url = encode(self.data)
        return self.ax.text(x,y, "plottwist", ha='left', va="center",
                    url=url, transform=self.ax.transAxes, **kwargs)

    def hide_at_the_origin(self):
        return self.plot_badge(-0.02,-0.02, color=(0,0,0,0), fontsize=8)

    def reproduce(self, url):
        data = decode(url)
        self.data["metadata"] = data["metadata"]
        for artist in data["artists"]:
            if not "func" in artist:
                continue
            if artist["func"] == "plot":
                self.plot(artist["x"], artist["y"], **artist["kwargs"])
            if artist["func"] == "scatter":
                self.scatter(artist["x"], artist["y"], **artist["kwargs"])
            if artist["func"] == "legend":
                self.legend(**artist["kwargs"])
            if artist["func"] == "axhline":
                self.axhline(artist["y"], **artist["kwargs"])
            if artist["func"] == "axvline":
                self.axvline(artist["x"], **artist["kwargs"])

def read_data(f: Union[str, bytes, Path, IO]):
    if hasattr(f, "read"):
        content = f.read()
        return content.encode() if isinstance(content, str) else content

    if isinstance(f, (str, Path)) and Path(f).exists():
        return Path(f).read_bytes()

    if isinstance(f, bytes):
        return f

    if isinstance(f, str):
        return f.encode("utf-8")

def extract_urls(f: Union[str, bytes, Path, IO]):
    data = read_data(f)
    sp = data.split(bytes("#plottwist:", "utf-8"))[1:]
    sp = [x.split(bytes(")", "utf-8"))[0] for x in sp]
    urls = [f"plottwist:{x.decode('utf-8')}" for x in sp]
    return urls