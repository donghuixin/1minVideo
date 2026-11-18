# 1minVideo

把一组图片变成一条讲得清楚的**科普片或教程**。图可以是实验照片、原理示意图、数据图表、实物操作图，也可以是软件截图。助手负责看图、选主线和写旁白，Python 与 FFmpeg 负责构图、定时、切镜和导出。

将 [image-to-video](skills/image-to-video/SKILL.md) 目录放入个人 Skills 目录后，可以直接说：**“用 $image-to-video，把这几张实验图做成一条 40 秒的竖屏科普，给没学过物理的人看。”** 也可以说：“用这组操作截图做一个横屏教程，保留真实按钮，暂时不要语音。”用户不需要写分镜 JSON。

**完整工作流**：读图建索引 → 判断科普或教程 → 围绕一个问题编排镜头、标记证据 → 编译画面与时长 → 渲染无声母版、外置字幕、旁白稿 → 按需加独立配音 → 复查编码后的成片。见[双模式分镜示例](skills/image-to-video/references/story.md)及[代码剪辑手册](skills/image-to-video/references/editing.md)。

**两张图试跑**（Python 3.10+、Pillow、带 libx264 的 FFmpeg）：

```sh
python3 -m pip install Pillow
cd skills/image-to-video
python3 scripts/demo.py /tmp/one-minute-demo
python3 scripts/cut.py render /tmp/one-minute-demo/plan.json /tmp/one-minute-demo/export
```

输出无声母版 `picture.mp4` 和外置 `captions.srt`、`captions.vtt`、`narration.txt`；示例使用现场生成的几何测试图，不是产品操作的替身。设置 `FFMPEG` 环境变量可指定编码器。真实项目的截图、语音和成片不包含在仓库中。

**跑一个不含任何聊天界面的科普片**：在同一目录运行 `python3 scripts/science_demo.py /tmp/shadow-demo`。脚本生成三张基于几何关系的投影示意图，剪成 12 秒对比短片，结果在 `/tmp/shadow-demo/project/export`。这是示意图，不是实测数据。

### 第一条片子的复盘

| 返工的地方 | 下次怎么做 |
|---|---|
| 想让聊天界面更利落，重画了气泡，还把另一项任务的压缩包当成当前任务的输出。 | 只裁原图。每条指令和对应附件放在分镜表同一行；没有截图的结果不补画。 |
| 用户认可原片的气泡节奏，只要求提高真实性；改版时却连开场顺序也动了。 | 写下“保留什么、只改什么”。先交一段手机上能看的开场：指令出现、真实文件返回，然后才讲下载。 |
| 界面讲解、底部旁白、标题重复说同一件事；先配完整音轨又让改词变得费时。 | 无声看片，只留读懂操作所需的元素。先用一句含产品名的真实台词选声音，锁定画面后才逐镜录制，字幕单独交付。 |
