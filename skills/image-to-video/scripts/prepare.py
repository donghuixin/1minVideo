"""Inventory real images and compile an evidence-linked storyboard to a cut.py plan."""
import argparse
import json
import math
from pathlib import Path
import re
from PIL import Image, ImageDraw, ImageOps


def write(path, data):
    with path.open("x", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def inventory(source, project):
    paths = sorted(p for p in source.iterdir() if p.is_file() and p.suffix.lower() in
                   {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"})
    if not paths:
        raise ValueError("no supported images in source folder")
    if project.exists() and any(project.iterdir()):
        raise ValueError("inventory needs a new or empty project folder")
    assets = project / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (192 * min(4, len(paths)), 155 * math.ceil(len(paths)/4)), "white")
    d = ImageDraw.Draw(sheet)
    index = {}
    for i, p in enumerate(paths):
        key = f"{i+1:03}"
        with Image.open(p) as src:
            im = ImageOps.exif_transpose(src).convert("RGBA")
        rel = f"assets/{key}.png"
        im.save(project/rel)
        index[key] = {"file":rel, "source_name":p.name, "size":im.size}
        im.thumbnail((182,123), Image.Resampling.LANCZOS)
        x = i % 4 * 192; y = i // 4 * 155
        sheet.paste(im, (x+(192-im.width)//2, y), im)
        d.text((x+8,y+129),key,fill="black")
    sheet.save(project/"contact.jpg", quality=90)
    write(project/"images.json",index)
    write(project/"story.json",{"mode":None,"size":[1080,1920],"fps":25,"shots":[]})


def plan(project):
    read = lambda name: json.loads((project/name).read_text(encoding="utf-8"))
    catalog=read("images.json"); story=read("story.json")
    if story.get("mode") not in {"science","tutorial"} or not story.get("shots"):
        raise ValueError("inspect contact.jpg, then author story.json with mode and shots")
    w,h=story["size"]; fps=story["fps"]; shots=story["shots"]
    if not all(type(n) is int and n>=16 and not n%2 for n in (w,h)):
        raise ValueError("canvas dimensions must be even integers >=16")
    if type(fps) is not int or not 1<=fps<=120:raise ValueError("invalid fps")
    weights=[]; output=[]
    for row in shots:
        ids=row["images"]; voice=row.get("voice","").strip()
        if len(ids) not in (1,2) or not all(i in catalog for i in ids):
            raise ValueError(f"each shot needs one or two known image IDs: {ids}")
        if not row.get("evidence","").strip():
            raise ValueError("state what is visible, or identify the source of the explanation")
        latin=len(re.findall(r"[A-Za-z0-9]+",voice))
        cjk=len(re.findall(r"[\u3400-\u9fff]",voice))
        weights.append(max(2.0,cjk/4.4+latin/2.6+0.55+(0.5 if len(ids)==2 else 0)))
        pad=max(1,round(min(w,h)*.035))
        boxes=[[pad,pad,w-pad,h-pad]]
        if len(ids)==2 and h>w:boxes=[[pad,pad,w-pad,h//2-pad],[pad,h//2+pad,w-pad,h-pad]]
        elif len(ids)==2:boxes=[[pad,pad,w//2-pad,h-pad],[w//2+pad,pad,w-pad,h-pad]]
        layers=[]
        for key,box in zip(ids,boxes):
            img=catalog[key]; layers.append({"file":img["file"],"crop":[0,0,*img["size"]],"box":box})
        output.append({"voice":voice,"caption":row.get("caption",voice),"layers":layers,
                       "evidence":row["evidence"],"images":ids})
    seconds=story.get("seconds",sum(weights))
    if not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or seconds<=0:
        raise ValueError("invalid target duration")
    total=round(seconds*fps)
    if total<len(shots)*fps:raise ValueError("budget less than one second per shot; cut shots or extend")
    # Reserve one second per shot; distribute the remaining frames without rounding drift.
    extra=total-len(shots)*fps; denom=sum(x-1 for x in weights); cumulative=0.; prev=0
    for n,(shot,weight) in enumerate(zip(output,weights),1):
        cumulative+=weight-1; end=round(extra*cumulative/denom)
        shot["frames"]=fps+end-prev; prev=end
        if shot["frames"]/fps < weight*.82:print(f"Shot {n}: shorten narration or allow more reading time.")
    write(project/"plan.json",{"mode":story["mode"],"size":[w,h],"fps":fps,"shots":output})


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    sub=cli.add_subparsers(dest="action",required=True)
    a=sub.add_parser("inventory"); a.add_argument("source",type=Path); a.add_argument("project",type=Path)
    sub.add_parser("plan").add_argument("project",type=Path)
    args=cli.parse_args()
    if args.action=="inventory":inventory(args.source,args.project)
    else:plan(args.project)
