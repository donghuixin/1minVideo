"""Render a screenshot timeline, mute a movie, or mux a locked WAV. Python 3.10+."""
import argparse
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import wave

from PIL import Image, ImageColor

FF = os.environ.get("FFMPEG", "ffmpeg")


def integer(n, low, high=None):
    if type(n) is not int or n < low or (high is not None and n > high):
        raise ValueError(f"invalid integer: {n!r}, expected {low}..{high}")
    return n


def rect(values, size):
    x, y, r, b = values
    for n in values:
        integer(n, 0)
    if not (x < r <= size[0] and y < b <= size[1]):
        raise ValueError(f"bad rectangle {values} for {size}")
    return tuple(values)


def load(plan):
    p = json.loads(plan.read_text(encoding="utf-8"))
    w, h = p["size"]
    integer(w, 2); integer(h, 2); integer(p["fps"], 1, 120)
    if w % 2 or h % 2 or not p["shots"]:
        raise ValueError("yuv420p requires even dimensions and at least one shot")
    images = {}
    for shot in p["shots"]:
        n = integer(shot["frames"], 1)
        ImageColor.getrgb(shot.get("bg", "#ffffff"))
        for layer in shot["layers"]:
            key = layer["file"]
            if key not in images:
                with Image.open(plan.parent / key) as im:
                    images[key] = im.convert("RGBA")
            sz = images[key].size
            rect(layer["crop"], sz)
            rect(layer.get("to", layer["crop"]), sz)
            rect(layer["box"], (w, h))
            at = integer(layer.get("at", 0), 0, n-1)
            end = integer(layer.get("until", n), at+1, n)
            for name in ("pan", "reveal"):
                integer(layer.get(name, 0), 0, end-at)
    return p, images


def eased(frame, count):
    if count <= 1:
        return 1.
    t = min(1., frame/(count-1))
    return t*t*(3-2*t)


def frame_image(size, shot, frame, images):
    out = Image.new("RGB", size, shot.get("bg", "#ffffff"))
    for layer in shot["layers"]:
        at = layer.get("at", 0)
        if not at <= frame < layer.get("until", shot["frames"]):
            continue
        elapsed = frame-at
        start = layer["crop"]
        end = layer.get("to", start)
        t = eased(elapsed, layer.get("pan", 0))
        a = eased(elapsed, layer.get("reveal", 0))
        box = [round(x+(y-x)*t) for x, y in zip(start, end)]
        part = images[layer["file"]].crop(box)
        x, y, r, b = layer["box"]
        scale = min((r-x)/part.width, (b-y)/part.height)
        part = part.resize((max(1,round(part.width*scale)), max(1,round(part.height*scale))),
                           Image.Resampling.LANCZOS)
        dx = (r-x-part.width)//2
        dy = (b-y-part.height)//2 + round(size[1]*.015*(1-a))
        # Clip the rising pixels to their destination, including native PNG alpha.
        part = part.crop((0,0,part.width,min(part.height, b-y-dy))) if dy < b-y else None
        if part:
            mask = part.getchannel("A")
            if a < 1:
                mask = mask.point(lambda v: round(v*a))
            out.paste(part,(x+dx,y+dy),mask)
    return out


def stamp(frame, fps):
    m = round(1000*frame/fps)
    return f"{m//3600000:02}:{m//60000%60:02}:{m//1000%60:02}.{m%1000:03}"


def render(plan, out):
    p, images = load(plan)
    out.mkdir(parents=True,exist_ok=True)
    names = ["picture.mp4","captions.srt","captions.vtt","narration.txt","timing.json"]
    if any((out/name).exists() for name in names):
        raise FileExistsError("use a new output directory")
    w,h = p["size"]; fps=p["fps"]
    with TemporaryDirectory(dir=out) as stage:
        dest = Path(stage)
        args = [FF,"-v","error","-nostdin","-f","rawvideo","-pixel_format","rgb24",
                "-video_size",f"{w}x{h}","-framerate",str(fps),"-i","pipe:0","-an",
                "-c:v","libx264","-crf","17","-pix_fmt","yuv420p","-movflags","+faststart",str(dest/names[0])]
        clock=0; srt=[]; vtt=["WEBVTT\n"]; voice=[]; timeline=[]
        with subprocess.Popen(args,stdin=subprocess.PIPE) as proc:
            for shot in p["shots"]:
                n=shot["frames"]
                for i in range(n):
                    proc.stdin.write(frame_image((w,h),shot,i,images).tobytes())
                span=f"{stamp(clock,fps)} --> {stamp(clock+n,fps)}"
                words=shot.get("voice",""); caption=shot.get("caption",words)
                if caption.strip():
                    srt.append(f"{len(srt)+1}\n{span.replace('.',',')}\n{caption}\n")
                    vtt.append(f"{span}\n{caption}\n")
                voice.append(f"{span}\n{words}\n")
                timeline.append({"start_frame":clock,"end_frame":clock+n,"voice":words,"caption":caption})
                clock+=n
            proc.stdin.close()
            if proc.wait(): raise RuntimeError("FFmpeg render failed")
        for name,rows in zip(names[1:4],(srt,vtt,voice)):
            (dest/name).write_text("\n".join(rows)+"\n",encoding="utf-8")
        (dest/names[-1]).write_text(json.dumps({"fps":fps,"frames":clock,"cues":timeline},ensure_ascii=False,indent=2),encoding="utf-8")
        for name in names:(dest/name).rename(out/name)


def ff(*args):
    subprocess.run([FF,"-v","error","-nostdin","-n",*map(str,args)],check=True)


def mux(folder, wav, target):
    t=json.loads((folder/"timing.json").read_text(encoding="utf-8"))
    with wave.open(str(wav),"rb") as audio:
        diff=abs(audio.getnframes()/audio.getframerate()-t["frames"]/t["fps"])
    if diff>1/t["fps"]+1e-8:
        raise ValueError("align WAV to picture lock first (duration mismatch >1 frame)")
    ff("-i",folder/"picture.mp4","-i",wav,"-map","0:v:0","-map","1:a:0","-c:v","copy",
       "-af","apad","-t",str(t["frames"]/t["fps"]),"-c:a","aac","-movflags","+faststart",target)


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    subs=cli.add_subparsers(dest="action",required=True)
    for action,fields in [("render",("plan","out")),("mute",("source","target")),("mux",("folder","wav","target"))]:
        sub=subs.add_parser(action)
        for field in fields:sub.add_argument(field,type=Path)
    a=cli.parse_args()
    if a.action=="render":render(a.plan,a.out)
    elif a.action=="mux":mux(a.folder,a.wav,a.target)
    else:ff("-i",a.source,"-map","0:v:0","-c:v","copy","-an","-sn","-dn","-movflags","+faststart",a.target)


if __name__=="__main__":main()
