"""Exercise an actual replacement take, independent SFX, and a science film without a hook."""
import array
import json
import math
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
import wave
from conform import conform, bounds
from cut import FF, render


def tone(path, hz, duration):
    samples=array.array("h",(round(6000*math.sin(i*2*math.pi*hz/16000)) for i in range(round(duration*16000))))
    with wave.open(str(path),"wb") as w:
        w.setparams((1,2,16000,0,"NONE","NONE"));w.writeframes(samples.tobytes())


class Replacement(unittest.TestCase):
    def test_user_take_and_protected_hook(self):
        with TemporaryDirectory() as tmp:
            d=Path(tmp); base=d/"edit"; spec=d/"take.json"; out=d/"release"; plan=d/"plan.json"
            colors=["#ff0000","#00ff00","#0000ff"]
            plan.write_text(json.dumps({"size":[96,64],"fps":25,"shots":[
                {"frames":n,"bg":c,"layers":[],"voice":v} for n,c,v in zip([25,25,50],colors,["","draft one","draft two"])]}))
            render(plan,base)
            self.assertEqual((base/"narration-clean.txt").read_text().split(),["draft","one","draft","two"])
            tone(d/"voice.wav",450,2.75);tone(d/"fx.wav",800,.2)
            data={"opening_shots":1,"opening_audio":"fx.wav","audio":"voice.wav","rate":1.02,
                  "cues":[{"in":0,"out":1,"text":"actual one"},{"in":1.54,"out":2.64,"text":"actual two"}]}
            spec.write_text(json.dumps(data));conform(base,spec,out)
            r=json.loads((out/"release.json").read_text())
            self.assertEqual(r["scene_edges"],[0,25,63,100])
            self.assertEqual(r["captions"][1]["start_ms"],2510)
            self.assertIn("00:00:01,000",(out/"captions.srt").read_text())
            self.assertNotIn("draft",(out/"narration-clean.txt").read_text())
            def decoded(*args):
                return subprocess.check_output([FF,"-v","error","-i",str(out/"final.mp4"),*args,"-"])
            frames=decoded("-map","0:v","-vf","scale=1:1","-pix_fmt","rgb24","-f","rawvideo")
            self.assertEqual(len(frames),100*3)
            for j,channel in [(24,0),(25,1),(62,1),(63,2),(99,2)]:
                self.assertGreater(frames[j*3+channel],220)
            pcm=array.array("h",decoded("-map","0:a","-ar","16000","-ac","1","-f","s16le"))
            peak=lambda a,b:max(map(abs,pcm[round(a*16000):round(b*16000)]))
            self.assertGreater(peak(.05,.15),1000)
            self.assertLess(peak(.35,.92),10)
            self.assertGreater(peak(1.03,1.15),1000)
            with self.assertRaises(FileExistsError):conform(base,spec,out)
            # A short cue list is not evidence that the audio file itself fits.
            tone(d/"voice.wav",450,3.8)
            with self.assertRaises(ValueError):conform(base,spec,d/"too-long")
            self.assertFalse((d/"too-long").exists())

    def test_no_fixed_opening_and_invalid_cues(self):
        t={"fps":10,"frames":30,"cues":[{"start_frame":0,"end_frame":10},{"start_frame":10,"end_frame":30}]}
        cfg={"cues":[{"in":.1,"out":1,"text":"diagram"},{"in":1.5,"out":2.5,"text":"comparison"}]}
        _,edges,rows=bounds(t,cfg)
        self.assertEqual(edges,[0,15,30]);self.assertEqual(rows[0]["start_ms"],100)
        cfg["cues"][1]["in"]=.5
        with self.assertRaises(ValueError):bounds(t,cfg)


if __name__=="__main__":unittest.main()
