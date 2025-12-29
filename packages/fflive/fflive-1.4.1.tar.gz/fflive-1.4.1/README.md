# fflive python

## 系统依赖
ffmpeg 3.0 及以上
python 3.0 及以上

mac，linux，windows 相应的 gpu 显卡驱动 （使用硬编码时需支持）

### Install
```shell
pip install fflive
```

### Command Line Interface (CLI)
After installation, you can use fflive directly from the command line:

```bash
fflive -i "input_url_or_file" -c:v libx264 -preset veryfast -b:v 1000k -c:a aac -b:a 128k -f flv "rtmp_output_url"
```

Example with authentication:
```bash
fflive \
  -i "https://stream-url.com/live/index.m3u8" \
  -c:v libx264 -preset veryfast -b:v 1000k \
  -c:a aac -b:a 128k \
  -f flv "rtmp://live.restream.io/live/stream_key" \
  -user-agent "Mozilla/5.0 (compatible; FFLive/1.0)" \
  -referer "https://example.com" \
  -key "your_stream_key"
```

### Use Demo 向视频（指定位置和时间，默认坐标为 0 ）添加 n 张图片
```shell
from fflive import video

# 输入视频
input_file = "demo.mp4"

# 输出视频
out_file = "demo_out.mp4"

# 图片列表
img_data = [
        {
            "img": "demo1.png",
            "x": "",
            "y": "",
            "str_time": "5",
            "end_time": "15",
        },
        {
            "img": "demo2.png",
            "x": "",
            "y": "",
            "str_time": "20",
            "end_time": "25.5"
        }
    ]

video.ins_img(input_file, img_data, out_file)
```

### Demo 视频添加动图 gif apng 等

```shell
from fflive import video

input_file = "demo.mp4"

out_file = "demo_out.mp4"

img_data = {
    "img": "img.apng",
    "x": "20",
    "y": "20",
    "str_time": "2",
    "end_time": "10"
}


video.ins_dynamic_img(input_file, img_data, out_file)
```

### 图片处理   图片转 mp4  5: 时长为 5 秒的 mp4
```shell
from fflive import image

image.img_trans_video("png/text_%02d.jpg", "5", "out.mp4")
```

### 符合模式
```python
from fflive import stream
stream = Stream()
# 输入文件
stream.input(input_file)
# 图片
stream.img("t1.png")
stream.img("t2.png", "10", y=10, str_time=5, end_time=10)
# 动图
stream.img_dynamic("t1.apng", x=10, y=10, str_time=5, end_time=10)
stream.img_dynamic("t2.gif", x=10, y=10, str_time=5, end_time=9)
# 文字水印
stream.word_water_mark("test1", x="10", y="10", str_time="0", end_time="20", font="ttf.ttf", color="blue")
stream.word_water_mark("test2", x="10", y="10", str_time="0", end_time="20", font="ttf.ttf", color="blue")
# 字幕
stream.subbtitle("tt.srt")
# 输出文件
stream.out(out_file)
stream.run()
```

### RTMP 流媒体 (新增功能)
```python
from fflive import stream

# 创建流实例
stream_instance = stream.Stream()

# 输入视频文件或流媒体URL
stream_instance.input("input_video.mp4")
# 或者输入在线流媒体
# stream_instance.input("https://example.com/live/index.m3u8")

# 设置 RTMP 输出
stream_instance.rtmp_output("rtmp://your-server/live", key="your_stream_key")

# 设置认证参数
stream_instance.set_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
stream_instance.set_referer("https://example.com")
stream_instance.set_header("Authorization", "Bearer your_auth_token")
stream_instance.set_header("Cookie", "session_id=abc123")

# 也可以设置多个头部信息
headers = {
    "Authorization": "Bearer your_auth_token",
    "User-Agent": "Custom User Agent",
    "Referer": "https://example.com"
}
stream_instance.set_headers(headers)

# 设置编码参数 (用于直播流)
stream_instance.vcode("libx264")  # 视频编码器
stream_instance.set_video_preset("veryfast")  # 编码预设
stream_instance.set_video_bitrate("1000k")  # 视频比特率
stream_instance.set_acode("-c:a aac")  # 音频编码器
stream_instance.set_audio_bitrate("128k")  # 音频比特率
stream_instance.set_format("flv")  # 输出格式

# 运行流媒体
stream_instance.run()
```

### 从URL流媒体到RTMP (高级功能)
```python
from fflive import stream

# 创建流实例
st = stream.Stream()

# 输入在线流媒体URL
st.input("https://example-stream.com/live/index.m3u8")

# 添加水印/Logo (支持复杂定位)
st.img("/path/to/logo.png", x="main_w-overlay_w-50", y="20", enable_expr="gt(t,0)")

# 设置RTMP输出
st.rtmp_output("rtmp://live.restream.io/live/your_stream_key")

# 设置编码参数
st.vcode("libx264")
st.set_video_preset("veryfast")
st.set_video_bitrate("1000k")
st.set_acode("-c:a aac")
st.set_audio_bitrate("128k")
st.set_format("flv")

# 设置认证参数
st.set_user_agent("Mozilla/5.0 (compatible; FFLive/1.0)")
st.set_header("Referer", "https://example.com")

# 运行流媒体
# st.run()  # 取消注释以实际运行
```

