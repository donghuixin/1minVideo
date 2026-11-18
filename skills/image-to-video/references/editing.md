# 一份时间线，三个独立轨道

`python3 scripts/demo.py DEMO` 生成可改的 `DEMO/plan.json` 和测试图。将图换成自己的，再运行 `python3 scripts/cut.py render DEMO/plan.json OUT`。使用空的或新的输出目录。需要 Python 3.10+、Pillow 和 FFmpeg（libx264）；无需浏览器、模型或账号。

| 字段 | 单位与用途 |
|---|---|
| size / fps | 输出像素宽高与整数帧率。竖屏常用 [1080,1920]、25。 |
| shots[].frames | 这一镜的帧数。镜头连续拼接。 |
| voice / caption | 分别是送入语音引擎的文本和发布用字幕；caption 缺省时用 voice，空字符串表示不出字幕。以一条字幕为一镜；需要更多提示点时拆镜头。 |
| bg | 此镜的画布底色，例如聊天背景采样色。 |
| layers[] | 后列的图层在前层之上。file 相对 plan 所在目录。 |
| crop / to | 源图像素的 [左,上,右,下)，to 是推镜终点。两个矩形都必须在原图内。 |
| box | 输出坐标 [左,上,右,下)，保持原比例、居中放入，不拉伸。 |
| at / until | 图层入场和离场帧，相对本镜起点；until 不包含在内。 |
| reveal | 入场用多少帧；0 表示直接出现，正值表示渐显及轻微上移。 |
| pan | 到达 to 用多少帧；0 表示直接使用最终裁区。 |

**做对话动画**：底层用真实聊天背景和头尾（如需）；每条消息裁成独立 PNG 或从同一截图取不同 crop，按实际左右方向给 box。用 at 控制登场，reveal 只持续几帧。当前总高度超出屏幕时，下一镜移动整个聊天区或换真实滚动录屏，不挤扁气泡。

**做软件教程**：从可辨认所在页面的 crop 推向目标 to，不同时展示两份重复截图。保留目标足够久让人看清，再切下一镜。更换节奏时改 frames / at，再重新渲染。示例逐帧代码偏向可读和准确；长静帧较多时，可以用 FFmpeg 的 tpad 克隆末帧，或缓存不变的镜头。

**移除现有声音**（画面流复制，不重新压缩）：

```sh
python3 scripts/cut.py mute narrated.mp4 silent.mp4
```

**替换配音**：按 narration.txt 逐镜录音；先裁掉首尾多余的静音，以帧号 ÷ fps 放在时间线上，保留句内停顿。导出与画面等长的 PCM WAV 后，在 Skill 目录运行（OUT 是 render 的输出目录）：

```sh
python3 scripts/cut.py mux OUT new-voice.wav new-review.mp4
```

mux 检查 WAV 与时间线时长差不超过一帧，保留 picture.mp4 且不会添加字幕。没有新 WAV 时，picture.mp4 本身就是可交付文件。SRT/VTT 是**按镜头**定时，不声称逐字对齐。

**验证**：用 ffprobe 检查 picture.mp4 只有视频流、分辨率和总时长符合 plan；含声版多一条音频流。随机暂停和逐帧定位是不同的检查：至少看每个入场前后，以及最后一帧。运行 `python3 scripts/test_cut.py` 可用合成图检查推镜、延迟入场、无音轨、字幕时间和换音轨路径。
