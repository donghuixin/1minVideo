"""Retime a picture export around a reviewed recording. No ASR service or TTS required."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import shutil
from tempfile import TemporaryDirectory
import wave
from cut import FF, ff

SR = 48000


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def clock(ms):
    return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02}.{ms%1000:03}"


def check_frames(movie, expected):
    progress=subprocess.check_output([FF,"-v","error","-nostdin","-nostats","-i",str(movie),
        "-map","0:v:0","-fps_mode","passthrough","-progress","pipe:1","-f","null","-"],text=True)
    counts=[int(line.split("=")[1]) for line in progress.splitlines() if line.startswith("frame=")]
    if not counts or counts[-1]!=expected:raise ValueError(f"decoded frame count mismatch: {movie.name}")
    return counts[-1]


def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda:f.read(1024*1024),b""):h.update(part)
    return h.hexdigest()


def bounds(t, cfg):
    fps, total, shots = t["fps"], t["frames"], t["cues"]
    old = [s["start_frame"] for s in shots] + [total]
    if not shots or fps <= 0 or old[0] != 0 or any(
        a >= b or s["end_frame"] != b for a,b,s in zip(old,old[1:],shots)
    ):
        raise ValueError("invalid source timeline")
    p = cfg.get("opening_shots", 0)
    if type(p) is not int or not 0 <= p < len(shots):
        raise ValueError("opening_shots must leave at least one voiced shot")
    cues = cfg["cues"]
    if len(cues) != len(shots)-p:
        raise ValueError("map one reviewed cue to each subsequent shot; split/merge the plan first")
    rate = cfg.get("rate",1)
    if not .5 <= rate <= 2:
        raise ValueError("unsupported tempo")
    prev=0; rows=[]; begin=old[p]
    for c in cues:
        a,b=c["in"],c["out"]
        if not (math.isfinite(b) and prev <= a < b and c["text"].strip()):
            raise ValueError("review cue text and positive non-overlapping source times")
        prev=b
        if begin/fps+b/rate > total/fps+1e-8:
            raise ValueError("take does not fit: extend the picture or choose a reviewed tempo")
        ms=[round((begin/fps+x/rate)*1000) for x in (a,b)]
        if ms[1]<=ms[0]:raise ValueError("cue shorter than caption precision")
        rows.append({"start_ms":ms[0],"end_ms":ms[1],"text":c["text"]})
    new=old[:p+1]+[begin+round(x["in"]*fps/rate) for x in cues[1:]]+[total]
    if any(a>=b for a,b in zip(new,new[1:])):raise ValueError("shots collapse at this frame rate")
    return old,new,rows


def conform(folder, spec, out):
    if out.exists():raise FileExistsError("use a new release directory")
    t,cfg=read(folder/"timing.json"),read(spec)
    old,new,rows=bounds(t,cfg)
    fps,rate,p=t["fps"],cfg.get("rate",1),cfg.get("opening_shots",0)
    prefix=round(old[p]*SR/fps); length=round(old[-1]*SR/fps)
    if not prefix and cfg.get("opening_audio"):raise ValueError("no opening for opening_audio")
    check_frames(folder/"picture.mp4",old[-1])
    out.parent.mkdir(parents=True,exist_ok=True)
    with TemporaryDirectory(dir=out.parent) as tmp:
        work=Path(tmp); release=work/"release"; release.mkdir()
        wav=work/"voice.wav"
        src=spec.parent/cfg["audio"]
        ff("-i",src,"-map","0:a:0","-af",f"aresample={SR},atempo={rate}","-ac","1","-c:a","pcm_s16le",wav)
        with wave.open(str(wav)) as f:
            size=f.getnframes()
        if size > length-prefix:
            raise ValueError("decoded audio exceeds available space; do not truncate the recording")
        if round(cfg["cues"][-1]["out"]*SR/rate)>size+round(SR*.04):
            raise ValueError("last reviewed cue extends beyond the recording")
        hook=work/"hook.wav"
        if cfg.get("opening_audio"):
            ff("-i",spec.parent/cfg["opening_audio"],"-map","0:a:0","-af",
               f"aresample={SR},apad,atrim=end_sample={prefix}","-ac","1","-c:a","pcm_s16le",hook)
        with wave.open(str(work/"mix.wav"),"wb") as mix:
            mix.setparams((1,2,SR,0,"NONE","NONE"))
            if hook.exists():
                with wave.open(str(hook)) as f:mix.writeframes(f.readframes(prefix))
            else:mix.writeframes(bytes(prefix*2))
            with wave.open(str(wav)) as f:mix.writeframes(f.readframes(size))
            mix.writeframes(bytes((length-prefix-size)*2))
        # Stretch a shorter slot only when needed, so a late action is never simply cut off.
        for i,(a,b,c,d) in enumerate(zip(old,old[1:],new,new[1:])):
            n,m=b-a,d-c
            vf=f"trim=end_frame={n},setpts=PTS-STARTPTS"
            if m<n:vf+=f",setpts=PTS*{m}/{n},fps={fps}"
            vf+=f",tpad=stop_mode=clone:stop_duration={m/fps+1},trim=end_frame={m},setpts=N/({fps}*TB)"
            ff("-ss",f"{a/fps:.9f}","-i",folder/"picture.mp4","-map","0:v:0","-an","-vf",vf,
               "-c:v","libx264","-preset","veryfast","-crf","17","-pix_fmt","yuv420p",work/f"{i}.mp4")
        manifest=work/"clips.txt"
        manifest.write_text("".join(f"file '{i}.mp4'\n" for i in range(len(old)-1)),encoding="ascii")
        ff("-f","concat","-i",manifest,"-i",work/"mix.wav","-map","0:v:0","-map","1:a:0","-c:v","copy",
           "-c:a","aac","-b:a","160k","-movflags","+faststart",release/"final.mp4")
        srt=[];vtt=["WEBVTT\n"]; sheet=[]
        for i,(a,b) in enumerate(zip(new,new[1:])):
            label=t["cues"][i].get("visual") or f"Shot {i+1}"
            line=""
            if i>=p:
                r=rows[i-p]; line=r["text"]
                span=f"{clock(r['start_ms'])} --> {clock(r['end_ms'])}"
                srt.append(f"{i-p+1}\n{span.replace('.',',')}\n{line}\n");vtt.append(f"{span}\n{line}\n")
            sheet.append(f"{clock(round(a*1000/fps))} --> {clock(round(b*1000/fps))}  {label}\n{line or '[no narration]'}\n")
        for name,strings in [("captions.srt",srt),("captions.vtt",vtt),("picture-and-voice.txt",sheet),
                             ("narration-clean.txt",[r["text"]+"\n" for r in rows])]:
            (release/name).write_text("\n".join(strings)+"\n",encoding="utf-8")
        receipt={"fps":fps,"frames":old[-1],"decoded_frames":check_frames(release/"final.mp4",old[-1]),
                 "source_picture_sha256":digest(folder/"picture.mp4"),"source_take_sha256":digest(src),
                 "opening_frames":old[p],"rate":rate,
                 "take_samples_after_tempo":size,"sample_rate":SR,"scene_edges":new,"captions":rows}
        (release/"release.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding="utf-8")
        shutil.copyfile(work/"mix.wav",release/"aligned-mix.wav")
        release.rename(out)


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ("folder","spec","out"):cli.add_argument(key,type=Path)
    args=cli.parse_args();conform(args.folder,args.spec,args.out)
