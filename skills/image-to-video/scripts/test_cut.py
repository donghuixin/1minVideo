"""End-to-end smoke test using only synthetic geometry and a silent WAV."""
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
import json
import wave
from cut import FF, render, mux, load, frame_image, ff
from demo import create
from science_demo import make
from prepare import plan

class Smoke(unittest.TestCase):
    def test_modes(self):
        with TemporaryDirectory() as tmp:
            p=make(Path(tmp)); s=json.loads((p/"plan.json").read_text()); a,b=s["shots"][0]["layers"]
            self.assertEqual(sum(r["frames"] for r in s["shots"]),300)
            self.assertLess(a["box"][3],b["box"][1])
            render(p/"plan.json",p/"science")
            self.assertTrue((p/"science"/"picture.mp4").stat().st_size>1000)
            story=json.loads((p/"story.json").read_text());story.update(mode="tutorial",size=[640,360])
            (p/"plan.json").unlink();(p/"story.json").write_text(json.dumps(story))
            plan(p); s=json.loads((p/"plan.json").read_text()); a,b=s["shots"][0]["layers"]
            self.assertLess(a["box"][2],b["box"][0])
            (p/"plan.json").unlink(); story["shots"][0]["images"]=["999"]
            (p/"story.json").write_text(json.dumps(story))
            with self.assertRaises(ValueError):plan(p)

    def test_edit(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);create(root); out=root/"out"
            p,images=load(root/"plan.json");shot=p["shots"][1]
            def frame(n):return frame_image(tuple(p["size"]),shot,n,images)
            self.assertNotEqual(frame(0).tobytes(),frame(15).tobytes())
            self.assertEqual(frame(19).getpixel((160,538)),(255,255,255))
            self.assertEqual(frame(29).getpixel((160,538)),(51,201,137))
            render(root/"plan.json",out)
            self.assertIn("00:00:02,000 --> 00:00:05,000",(out/"captions.srt").read_text())
            with self.assertRaises(FileExistsError):render(root/"plan.json",out)
            def digest(path):return subprocess.check_output([FF,"-v","error","-i",str(path),"-map","0:v","-f","framemd5","-"])
            picture=digest(out/"picture.mp4")
            self.assertEqual(len([x for x in picture.splitlines() if x.startswith(b"0,")]),125)
            wav=root/"voice.wav"
            def make_wav(seconds):
                with wave.open(str(wav),"wb") as w:w.setparams((1,2,24000,0,"NONE","NONE"));w.writeframes(bytes(48000*seconds))
            make_wav(1)
            with self.assertRaises(ValueError):mux(out,wav,root/"review.mp4")
            make_wav(5);mux(out,wav,root/"review.mp4")
            ff("-i",root/"review.mp4","-map","0:a","-f","null","-")
            ff("-i",root/"review.mp4","-map","0:v:0","-c:v","copy","-an",root/"silent.mp4")
            self.assertEqual(picture,digest(root/"silent.mp4"))
            r=subprocess.run([FF,"-v","error","-i",str(root/"silent.mp4"),"-map","0:a","-f","null","-"],capture_output=True)
            self.assertNotEqual(r.returncode,0)

if __name__=="__main__":unittest.main()
