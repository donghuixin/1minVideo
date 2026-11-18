"""Runnable science example: shadows of equal-height objects, under ideal parallel light."""
import math
from pathlib import Path
import sys
import json
from PIL import Image, ImageDraw
from prepare import inventory, plan
from cut import render


def make(root):
    raw=root/"originals"; raw.mkdir(parents=True,exist_ok=False)
    for number, (angle,ray) in enumerate([(60,False),(25,False),(25,True)],1):
        im=Image.new("RGB",(600,360),"#fafaf7"); d=ImageDraw.Draw(im)
        x,y,ht=150,255,135
        tip=round(x+ht/math.tan(math.radians(angle)))
        d.line((40,y,559,y),fill="#80868a",width=3)
        d.line((x,y,tip,y),fill="#303b49",width=10)
        d.line((x,y,x,y-ht),fill="#0e7770",width=10)
        if ray:
            d.line((x,y-ht,tip,y),fill="#c16716",width=4)
            d.ellipse((tip-6,y-6,tip+6,y+6),fill="#c16716")
        d.text((35,30),f"ILLUSTRATION  /  {angle} deg",fill="#293540")
        im.save(raw/f"{number}.png")
    proj=root/"project"; inventory(raw,proj)
    story={"mode":"science","size":[360,640],"fps":25,"seconds":12,"shots":[
        {"images":["001","002"],"voice":"同样高的物体，为什么影子不一样长？","evidence":"等高竖杆在两种光线角度下的示意，不是实验照片"},
        {"images":["003"],"voice":"从杆顶沿光线看，落在地面的点就是影子末端。","evidence":"橙线连接杆顶和地面交点"},
        {"images":["001","002"],"voice":"地面水平时，光线越贴近地面，影子越长。","evidence":"保持杆高不变，比较图示中两个影子的长度"}]}
    (proj/"story.json").write_text(json.dumps(story,ensure_ascii=False,indent=2),encoding="utf-8")
    plan(proj)
    return proj


if __name__=="__main__":
    p=make(Path(sys.argv[1])); render(p/"plan.json",p/"export")
