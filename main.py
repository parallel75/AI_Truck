from dashscope import SpeechSynthesizer
from dotenv import load_dotenv
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from openai import OpenAI

from alibabacloud_alimt20181012.client import Client as alimt20181012Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_alimt20181012 import models as alimt_20181012_models
from alibabacloud_tea_util import models as util_models
from http import HTTPStatus
from playsound import playsound

import dashscope
import os
import subprocess
import textwrap


load_dotenv()

#命令行执行
def executeCommand(command):
    print(subprocess.call(command,shell=True))

# 调用 Whisper 获取视频英文文案
#https://platform.openai.com/docs/guides/speech-to-text
#https://platform.openai.com/docs/api-reference/audio/createTranscription
def getScript():
    client = OpenAI()
    client.api_key = os.environ["OPENAI_API_KEY"]

    audio_file = open("audio.mp3", "rb")

    if audio_file is not None:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )

        print(transcript.__sizeof__())
        #print(transcript)
        #print(type(transcript))

        results = textwrap.wrap(transcript, 4000)
        #print(results)

        return transcript



# 调用  将英文翻译为中文    群里机器翻译
#https://www.aliyun.com/product/ai/alimt
#https://help.aliyun.com/zh/machine-translation/product-overview
def translate(source,target,message):
    ali_access_key_id=os.environ['ALI_CLOUD_ACCESS_KEY_ID']
    ali_access_key_secret =os.environ['ALI_CLOUD_ACCESS_KEY_SECRET']

    config = open_api_models.Config(
        # 必填，您的 AccessKey ID,
        access_key_id=ali_access_key_id,
        # 必填，您的 AccessKey Secret,
        access_key_secret=ali_access_key_secret
    )
    # Endpoint 请参考 https://api.aliyun.com/product/alimt
    config.endpoint = f'mt.aliyuncs.com'
    client = alimt20181012Client(config)

    translate_general_request = alimt_20181012_models.TranslateGeneralRequest(
        format_type='text',
        source_language=source,
        target_language=target,
        source_text=message,
        scene='general'
    )
    runtime = util_models.RuntimeOptions()

    try:
        # 复制代码运行请自行打印 API 的返回值
        translateGeneralResponse = client.translate_general_with_options(translate_general_request, runtime)

        #print(translateGeneralResponse.body.data.translated)

        translate_result = translateGeneralResponse.body.data.translated
        word_count = translateGeneralResponse.body.data.word_count

        return translate_result
    except Exception as error:
        # 如有需要，请打印 error
        print(error.__str__())


# 优化 中文文案  通益千问
#https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-thousand-questions
#https://dashscope.console.aliyun.com/model
def optimize_with_prompt(message):
    dashscope.api_key = os.environ["ALI_API_KEY"]

    response = dashscope.Generation.call(
        model=dashscope.Generation.Models.qwen_turbo,
        prompt='把以下内容按照中文的习惯修改的更加通顺，可以适当的润色，不要添加任何段落样式 ：' + message
    )
    # The response status_code is HTTPStatus.OK indicate success,
    # otherwise indicate request is failed, you can get error code
    # and message from code and message.
    if response.status_code == HTTPStatus.OK:
        #print(response.output)  # The output text
        print(response.usage)  # The usage information

        return  response.output.text.__str__()
    else:
        print(response.code)  # The error code.
        print(response.message)  # The error message.


#将中文文案生成为音频文件  sambert
#https://help.aliyun.com/zh/dashscope/developer-reference/sambert-speech-synthesis
def generateAudio(message):
    dashscope.api_key = os.environ['ALI_API_KEY']

    result = SpeechSynthesizer.call(model='sambert-zhixiang-v1',
                                    text=message,
                                    sample_rate=48000)
    if result.get_audio_data() is not None:
        with (open('new_audio.mp3', 'wb')) as f:
            f.write(result.get_audio_data())
        #playsound('output.wav')

#合并原有视频文件和新的音频文件
def merge_audio_video(video_filename, audio_filename, output_filename):
    print("合并 音视频文件 ...")
    print("视频文件 :", video_filename)
    print("音频文件 :", audio_filename)

    # 加载视频文件
    video_clip = VideoFileClip(video_filename)

    # 加载音频文件
    audio_clip = AudioFileClip(audio_filename)

    # 合并音视频文件
    final_clip = video_clip.set_audio(audio_clip)

    # 生成最终的结果文件
    final_clip.write_videofile(
        output_filename, codec='libx264', audio_codec='aac')

    # 关闭流
    video_clip.close()
    audio_clip.close()

    return output_filename


def main():
    #print_params()

    yt_url = "https://www.youtube.com/watch?v=_iRUe5GBWR8"

    print("=================================================================")
    download_command = "yt-dlp_macos "+yt_url+" -o 'raw.%(ext)s'"
    print("下载命令： "+download_command)
    print("开始下载............")
    #下载视频
    executeCommand(download_command)
    print("下载完毕")
    print("=================================================================")

    print("=================================================================")
    get_video_command = "ffmpeg -i raw.webm -an video.mp4"
    print("获取纯视频命令： " + get_video_command)
    print("开始获取视频............")
    # 获取纯视频文件
    executeCommand(get_video_command)
    print("获取完毕")
    print("=================================================================")


    print("=================================================================")
    get_audio_command = "ffmpeg -i raw.webm -vn audio.mp3"
    print("获取纯音频命令： " + get_audio_command)
    print("开始获取音频............")
    # 获取纯音频文件
    executeCommand(get_audio_command)
    print("获取完毕")
    print("=================================================================")



    #获取英文文案
    print("=================================================================")
    print("获取英文文案")
    video_script = getScript()
    print(video_script)
    print("获取完毕")
    print("=================================================================")


    #文案翻译为中文
    print("=================================================================")
    print("翻译为中文文案")
    chinese_script = translate('en', 'zh', video_script)
    print(chinese_script)
    print("翻译完毕")
    print("=================================================================")


    #优化中文文案
    print("=================================================================")
    print("优化中文文案")
    optimize_chinese_script =   optimize_with_prompt(chinese_script)
    print(optimize_chinese_script)
    print("优化完毕")
    print("=================================================================")

    #生成语音文件
    print("=================================================================")
    print("生成新的音频文件")
    generateAudio(optimize_chinese_script)
    print("生成完毕")
    print("=================================================================")

    #将视频文件和新的音频文件合并
    print("=================================================================")
    print("合成原有视频文件和新的音频文件")
    merge_audio_video("video.mp4","new_audio.mp3","output.mp4")
    print("合成完毕")
    print("=================================================================")



def print_params():
    print(os.environ["OPENAI_API_KEY"])

    print(os.environ["ALI_API_KEY"])

    print(os.environ["ALI_CLOUD_ACCESS_KEY_ID"])
    print(os.environ["ALI_CLOUD_ACCESS_KEY_SECRET"])

    print("=================================================================")


if __name__ == '__main__':
    main()

