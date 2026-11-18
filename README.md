# 1minVideo

用真实产品截图制作可复剪的短教程。代码控制取景、气泡入场和切镜，画面、字幕、配音分别导出；无需录浏览器，也不需要云端服务。

仓库内的 [screenshot-to-video Skill](skills/screenshot-to-video/SKILL.md) 可独立使用。将整个 `skills/screenshot-to-video` 目录放入 Codex 的个人 skills 目录后，可用 `$screenshot-to-video` 调用；也可以直接运行脚本。

**两张图试跑**（Python 3.10+、Pillow、带 libx264 的 FFmpeg）：

```sh
python3 -m pip install Pillow
cd skills/screenshot-to-video
python3 scripts/demo.py /tmp/one-minute-demo
python3 scripts/cut.py render /tmp/one-minute-demo/plan.json /tmp/one-minute-demo/export
```

输出无声母版 `picture.mp4` 和外置 `captions.srt`、`captions.vtt`、`narration.txt`；示例使用现场生成的几何测试图，不是产品操作的替身。设置 `FFMPEG` 环境变量可指定编码器。真实项目的截图、语音和成片不包含在仓库中。

### 第一条片子的复盘

| 返工的地方 | 下次怎么做 |
|---|---|
| 想让聊天界面更利落，重画了气泡，还把另一项任务的压缩包当成当前任务的输出。 | 只裁原图。每条指令和对应附件放在分镜表同一行；没有截图的结果不补画。 |
| 用户认可原片的气泡节奏，只要求提高真实性；改版时却连开场顺序也动了。 | 写下“保留什么、只改什么”。先交一段手机上能看的开场：指令出现、真实文件返回，然后才讲下载。 |
| 界面讲解、底部旁白、标题重复说同一件事；先配完整音轨又让改词变得费时。 | 无声看片，只留读懂操作所需的元素。先用一句含产品名的真实台词选声音，锁定画面后才逐镜录制，字幕单独交付。 |
