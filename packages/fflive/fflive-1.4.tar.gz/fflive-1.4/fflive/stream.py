#!/usr/bin/python2.7
# coding=utf-8

import os

import json

import subprocess


class Stream(object):
    def __init__(self):
        self.cmd = ""
        self.out_file = ""
        self.vcode_type = ""
        self.input_file = ""
        self.word_list_str = ""
        self.subbtitle_file = ""

        self.cmd = []
        self.img_file = []
        self.word_list = []
        self.img_dynamic_list = []

        self.image_list = {}
        self.dynamic_list = {}

        # RTMP streaming parameters
        self.rtmp_url = ""
        self.rtmp_key = ""
        self.rtmp_token = ""
        self.user_agent = ""
        self.referer = ""
        self.headers = {}

    # 输入文件
    def input(self, file):
        self.input_file = file

    # 添加图片
    def img(self, img, x="0", y="0", str_time="0", end_time="0", enable_expr=None):
        if img == "":
            return False

        # Only try to get video info if input is a local file
        input_info = {}
        if self.input_file and os.path.isfile(self.input_file):
            input_info = self.video_info()
        else:
            # For URL inputs, we can't get duration, so use default behavior
            pass

        if end_time == "0":
            # If we can't get duration from URL, use a large default value
            if input_info and "format" in input_info and "duration" in input_info["format"]:
                end_time = float(input_info["format"]["duration"]) + 10.0
            else:
                end_time = "999999"  # Large number for indefinite duration

        img_data = {
            "img": img,
            "x": str(x),
            "y": str(y),
            "str_time": str(str_time),
            "end_time": str(end_time),
            "enable_expr": enable_expr  # Allow custom enable expression
        }

        self.img_file.append(img_data)

        img_input = []
        img_overlay = []

        for val in self.img_file:
            img_input.append(" -i %s" % val["img"])
            if val["enable_expr"]:
                # Use custom enable expression if provided
                img_overlay.append(" overlay=x=%s:y=%s:enable='%s'" % (
                        val["x"],
                        val["y"],
                        val["enable_expr"]
                    )
                )
            else:
                # Use time-based enable expression
                img_overlay.append(" overlay=x=%s:y=%s:enable='if(gt(t,%s),lt(t,%s))'" % (
                        val["x"],
                        val["y"],
                        val["str_time"],
                        val["end_time"]
                    )
                )

        img_input_str = " ".join(img_input)
        img_overlay_str = ",".join(img_overlay)

        self.image_list = {
            "input": img_input_str,
            "overlay": img_overlay_str
        }

    # 添加动态图片 gif apng 等
    def img_dynamic(self, file, x="0", y="0", str_time="0", end_time="0"):
        input_info = self.video_info()
        if file == "":
            return False
        if end_time == "":
            end_time = float(input_info["format"]["duration"]) + 10.0

        apng = {
            "input": " -ignore_loop 0 -i %s" % file,
            "x": str(x),
            "y": str(y),
            "str_time": str(str_time),
            "end_time": str(end_time)
        }
        self.img_dynamic_list.append(apng)

        img_dy_input = []
        img_dy_overlay = []
        for val in self.img_dynamic_list:
            img_dy_input.append(val["input"])
            img_dy_overlay.append(" overlay=x=%s:y=%s:shortest=1:enable='if(gt(t,%s), lt(t,%s))'" % (
                    val["x"],
                    val["y"],
                    val["str_time"],
                    val["end_time"]
                )
            )
        img_dy_input_str = " ".join(img_dy_input)
        img_dy_overlay_str = ",".join(img_dy_overlay)

        self.dynamic_list = {
            "input": img_dy_input_str,
            "overlay": img_dy_overlay_str
        }

    # 添加文字水印
    def word_water_mark(self, c, x="0", y="0", str_time="0", end_time="0", font="", color="white"):
        if font == "":
            return False
        input_info = self.video_info()
        if c == "":
            return False
        if end_time == "0":
            end_time = float(input_info["format"]["duration"]) + 10.0

        text = " drawtext=text='%s':x=%s:y=%s:enable='if(gt(t,%s),lt(t,%s))':fontfile=%s:" \
               "fontcolor=%s" % (c, str(x), str(y), str(str_time), str(end_time), str(font), str(color))
        self.word_list.append(text)

        self.word_list_str = ",".join(self.word_list)

    # 添加字幕文件 subtitles=txt.srt
    def subbtitle(self, file):
        self.subbtitle_file = " subtitles=%s" % file

    # 编码方式 -vcodec
    def vcode(self, code):
        if code == "":
            return False
        self.vcode_type = " -vcodec %s" % code

    # 输出文件
    def out(self, file):
        if file == "":
            return False
        self.out_file = "%s" % file

    # 设置 RTMP URL
    def rtmp_output(self, url, key="", token=""):
        if url == "":
            return False
        # 如果提供了 key，将其附加到 URL
        if key != "":
            if '?' in url:
                self.rtmp_url = "%s&%s" % (url, key)
            else:
                self.rtmp_url = "%s?%s" % (url, key)
        else:
            self.rtmp_url = url
        if key != "":
            self.rtmp_key = key
        if token != "":
            self.rtmp_token = token
        return True

    # 设置 User Agent
    def set_user_agent(self, user_agent):
        self.user_agent = user_agent

    # 设置 Referer
    def set_referer(self, referer):
        self.referer = referer

    # 设置自定义 HTTP 头
    def set_header(self, name, value):
        self.headers[name] = value

    # 设置多个 HTTP 头
    def set_headers(self, headers_dict):
        self.headers.update(headers_dict)

    # 设置认证信息（用于 DRM 或其他认证场景）
    def set_auth_info(self, auth_url="", auth_key="", auth_token="", cookie=""):
        if auth_url != "":
            self.set_header("Authorization", "Bearer %s" % auth_token if auth_token != "" else "")
        if cookie != "":
            self.set_header("Cookie", cookie)

    # 设置视频预设
    def set_video_preset(self, preset):
        self.video_preset = preset

    # 设置视频比特率
    def set_video_bitrate(self, bitrate):
        self.video_bitrate = bitrate

    # 设置音频编码器
    def set_acode(self, acode):
        self.acode_type = acode

    # 设置音频比特率
    def set_audio_bitrate(self, bitrate):
        self.audio_bitrate = bitrate

    # 设置输出格式
    def set_format(self, format_type):
        self.output_format = format_type

    # 执行脚本
    def run(self):
        if self.input_file == "":
            return False
        im = "ffmpeg -i %s" % self.input_file

        # 添加认证参数
        if self.user_agent != "":
            im = "%s -user_agent \"%s\"" % (im, self.user_agent)
        if self.referer != "":
            im = "%s -referer \"%s\"" % (im, self.referer)

        # 添加自定义 HTTP 头
        for header_name, header_value in self.headers.items():
            im = "%s -headers \"%s: %s\"" % (im, header_name, header_value)

        ov = ""

        if len(self.dynamic_list) > 0 and self.dynamic_list["input"] != "":
            im = "%s %s" % (im, self.dynamic_list["input"])

            if ov != "":
                ov = "%s,%s" % (ov, self.dynamic_list["overlay"])
            else:
                ov = self.dynamic_list["overlay"]
        if len(self.image_list) > 0:
            im = "%s %s" % (im, self.image_list["input"])

            if ov != "":
                ov = "%s,%s" % (ov, self.dynamic_list["overlay"])
            else:
                ov = self.dynamic_list["overlay"]

        # 文字水印
        if self.word_list_str != "":
            if ov != "":
                ov = "%s,%s" % (ov, self.word_list_str)
            else:
                ov = self.word_list_str

        # 字幕
        if self.subbtitle_file != "":
            if ov != "":
                ov = "%s,%s" % (ov, self.subbtitle_file)
            else:
                ov = self.subbtitle_file

        # Additional encoding parameters
        additional_params = ""

        # Add video preset if specified
        if hasattr(self, 'video_preset') and self.video_preset:
            additional_params += " -preset %s" % self.video_preset

        # Add video bitrate if specified
        if hasattr(self, 'video_bitrate') and self.video_bitrate:
            additional_params += " -b:v %s" % self.video_bitrate

        # Add audio codec if specified
        if hasattr(self, 'acode_type') and self.acode_type:
            additional_params += " %s" % self.acode_type

        # Add audio bitrate if specified
        if hasattr(self, 'audio_bitrate') and self.audio_bitrate:
            additional_params += " -b:a %s" % self.audio_bitrate

        # Add format if specified (for RTMP streaming)
        if hasattr(self, 'output_format') and self.output_format:
            additional_params += " -f %s" % self.output_format

        # 判断是否为 RTMP 输出
        if self.rtmp_url != "":
            # RTMP 输出
            if self.vcode_type != "":
                self.cmd = "%s -filter_complex \"%s\"%s -y %s %s" % (im, ov, additional_params, self.vcode_type, self.rtmp_url)
            else:
                self.cmd = "%s -filter_complex \"%s\"%s -y %s" % (im, ov, additional_params, self.rtmp_url)
        else:
            # 普通文件输出
            if self.vcode_type != "":
                self.cmd = "%s -filter_complex \"%s\"%s -y %s %s" % (im, ov, additional_params, self.vcode_type, self.out_file)
            else:
                self.cmd = "%s -filter_complex \"%s\"%s -y %s" % (im, ov, additional_params, self.out_file)

        self.do()

    # 获取视频的相关时长信息
    def video_info(self):
        result = {}
        if os.path.isfile(self.input_file) is False:
            return result

        cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', self.input_file]
        returned_data = subprocess.check_output(cmd)
        return json.loads(returned_data.decode('utf-8'))

    # 执行命令
    def do(self):
        if self.cmd == "":
            return False
        res = subprocess.call(self.cmd, shell=True)
        if res != 0:
            return False
        return True


if __name__ == '__main__':
    # 原有示例
    stream = Stream()
    stream.input("face.mp4")
    stream.img("t1.png")
    stream.img("t2.png", "10", y=10, str_time=5, end_time=10)
    stream.img_dynamic("t1.apng", x=10, y=10, str_time=5, end_time=10)
    stream.img_dynamic("t2.apng", x=10, y=10, str_time=5, end_time=9)
    stream.word_water_mark("测试文字水印1", x="10", y="10", str_time="0", end_time="20", font="ttf.ttf", color="white")
    stream.word_water_mark("测试文字水印2", x="10", y="10", str_time="0", end_time="20", font="ttf.ttf", color="white")
    stream.subbtitle("srt.srt")
    stream.out("out.mp4")
    stream.run()

    # 新增 RTMP 流媒体示例
    print("RTMP 流媒体示例:")
    rtmp_stream = Stream()
    rtmp_stream.input("input_video.mp4")  # 输入视频文件

    # 设置 RTMP 输出地址
    rtmp_stream.rtmp_output("rtmp://live.example.com/live", "stream_key=your_stream_key")

    # 设置认证参数
    rtmp_stream.set_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    rtmp_stream.set_referer("https://example.com")
    rtmp_stream.set_header("Authorization", "Bearer your_auth_token")
    rtmp_stream.set_header("Cookie", "session_id=abc13")

    # 运行流媒体
    # rtmp_stream.run()  # 注释掉以避免实际执行

