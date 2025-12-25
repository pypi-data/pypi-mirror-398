#!/usr/bin/env python
# pylint: disable=E0401,W0718

"""
Coding: UTF-8
Author: Bitliker
Date: 2025/12/08 09:15:11
Version: 1.0.0
Description: 音频元数据处理库

基于 mutagen 封装的统一音频标签处理库，支持 MP3、FLAC、M4A、OGG 等格式。
对外隐藏音频格式差异，提供统一的读写接口。

使用示例:
    from audio_tag import load, AudioMetadata

    # 读取音频文件
    audio = load('song.mp3')
    print(audio.title, audio.artist)

    # 修改元数据
    audio.title = '新标题'
    audio.artist = '新艺术家'
    audio.genre = ['Pop', 'Rock']
    audio.save()

    # 设置封面
    audio.set_artwork_from_file('cover.jpg')
    audio.save()
"""
from .audio_file import AudioFile
from .metadata import AudioMetadata

__all__ = [
    "AudioFile",
    "AudioMetadata",
]

__version__ = "1.0.0"
