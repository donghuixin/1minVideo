# 1minVideo

把一组图片变成一条讲得清楚的**科普片或教程**。图可以是实验照片、原理示意图、数据图表、实物操作图，也可以是软件截图。助手负责看图、选主线和写旁白，Python 与 FFmpeg 负责构图、定时、切镜和导出。

将 [image-to-video](skills/image-to-video/SKILL.md) 目录放入个人 Skills 目录后，可以直接说：**“用 $image-to-video，把这几张实验图做成一条 40 秒的竖屏科普，给没学过物理的人看。”** 也可以说：“用这组操作截图做一个横屏教程，保留真实按钮，暂时不要语音。”用户不需要写分镜 JSON。

**完整工作流**：定观众与主题 → 读图建索引 → [按科普或教程编排](skills/image-to-video/references/story.md) → 先看关键片段 → [导出干净母版和配音稿](skills/image-to-video/references/editing.md) → 有实录则用实际措辞、停顿定切点和外置字幕 → 单独做封面 → 复查编码后的文件。只要其中一项就停在那一项。[实录对齐、封面与发布验收](skills/image-to-video/references/release.md)。

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

**后期才暴露的三个问题：**“不配音”并不等于“没有提示音”；画面内容真实，不代表把案例写成封面大标题就准确；一条录好的旁白，即使总长度相近，也可能改词或在不同地方停顿。现在改版前先记录需保留的段落及各轨状态，纯稿与时间对照稿分别交付，按已核实的实录重定切点。开场秒数、颜色、语速倍率属于单片决定，不是通用模板。

### 借鉴了哪些公开 Skill

| 核对的一手来源 | 我们采用什么 | 不照搬什么 |
|---|---|---|
| [Remotion · remotion-captions](https://github.com/remotion-dev/skills/blob/main/skills/remotion-captions/SKILL.md) | 录音转写、带起止时间的字幕数据、显示样式是三件事；从最终时间数据导出 SRT/VTT。 | 不强加动态字幕或 React 依赖。 |
| [HeyGen · HyperFrames](https://github.com/heygen-com/hyperframes/blob/main/skills/hyperframes/SKILL.md) | 按轨定义内容；局部改动看对应时间范围的成片抽帧。 | 不为简单截图剪辑迁移到浏览器渲染或默认配乐。 |
| [JimLiu · baoyu-cover-image](https://github.com/JimLiu/baoyu-skills/blob/main/skills/baoyu-cover-image/SKILL.md) | 把封面类型、颜色、文字密度分开决定。我们再加一道检查：缩小后最醒目的是否仍是教学主题。 | 它是文章封面 Skill；不沿用文章画幅，也不默认插片头。 |
| [Aaryan Kapoor · video-production](https://github.com/Aaryan-Kapoor/video-production-skill/blob/main/skills/video-production/SKILL.md) | 依据实际音段时长编排视觉，为复剪持久保存素材、脚本和检查帧。 | 不要求每片合成 TTS、使用 Manim 或发布到托管服务。 |

这些是对公开工作流的取舍，不是运行过四套工具的性能比较；仓库不需要安装它们。

在仓库根目录运行 `python3 -m unittest discover -s skills/image-to-video/scripts -p 'test_*.py'` 可复验：示意图科普、界面动画、只有音效的开场、实录替换、独立字幕，以及超时拒绝导出。
