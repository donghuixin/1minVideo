"""Generate two non-personal geometry fixtures and a runnable shot list."""
from pathlib import Path
import json
import sys
from PIL import Image, ImageDraw

def create(folder):
    folder.mkdir(parents=True,exist_ok=True)
    if any((folder/k).exists() for k in ("source.png","detail.png","plan.json")):
        raise FileExistsError("use a fresh demo folder")
    im=Image.new("RGB",(320,280),"#dfe7ef"); d=ImageDraw.Draw(im)
    d.rectangle((0,0,159,279),fill="#1b4362");d.ellipse((185,56,298,169),fill="#dc7233")
    im.save(folder/"source.png")
    im=Image.new("RGBA",(120,96),(0,0,0,0));ImageDraw.Draw(im).rectangle((8,8,112,88),fill="#33c989")
    im.save(folder/"detail.png")
    src={"file":"source.png","crop":[0,0,320,280],"box":[12,60,348,460]}
    plan={"size":[360,640],"fps":25,"shots":[
        {"frames":50,"voice":"先看全景。","layers":[src]},
        {"frames":75,"voice":"看右边的细节。","layers":[{**src,"to":[160,10,320,210],"pan":15},
         {"file":"detail.png","crop":[0,0,120,96],"box":[55,465,270,620],"at":20,"reveal":8}]}]}
    (folder/"plan.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding="utf-8")

if __name__=="__main__":create(Path(sys.argv[1]))
