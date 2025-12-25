#!/usr/bin/env python
# pylint: disable=E0401,W0718

"""
Coding: UTF-8
Author: Bitliker
Date: 2025/12/08
Version: 1.0.0
Description: MP4/M4A 文件处理器
"""

from typing import List
from mutagen.mp4 import MP4, MP4Cover
from .base import BaseHandler
from ..metadata import AudioMetadata


class MP4Handler(BaseHandler):
    """MP4/M4A 文件处理器"""

    # MP4 标签映射
    TAG_MAP = {
        'title': '\xa9nam',
        'artist': '\xa9ART',
        'album': '\xa9alb',
        'album_artist': 'aART',
        'year': '\xa9day',
        'genre': '\xa9gen',
        'composer': '\xa9wrt',
        'comment': '\xa9cmt',
        'lyrics': '\xa9lyr',
        'track': 'trkn',
        'disc': 'disk',
        'artwork': 'covr',
    }

    def load(self) -> None:
        self._file = MP4(self.filepath)

    def read(self) -> AudioMetadata:
        tags = self._file.tags
        if tags is None:
            return AudioMetadata()

        # 音轨号
        track_info = tags.get(self.TAG_MAP['track'])
        track_num = None
        total_tracks = None
        if track_info:
            track_num = track_info[0][0] if track_info[0][0] else None
            total_tracks = track_info[0][1] if track_info[0][1] else None

        # 碟片号
        disc_info = tags.get(self.TAG_MAP['disc'])
        disc_num = None
        total_discs = None
        if disc_info:
            disc_num = disc_info[0][0] if disc_info[0][0] else None
            total_discs = disc_info[0][1] if disc_info[0][1] else None

        # 封面
        artwork = None
        cover_data = tags.get(self.TAG_MAP['artwork'])
        if cover_data:
            artwork = bytes(cover_data[0])

        # 流派
        genre = self._parse_genre(tags.get(self.TAG_MAP['genre']))

        return AudioMetadata(
            title=self._get_first_value(tags.get(self.TAG_MAP['title'])),
            artist=self._get_first_value(tags.get(self.TAG_MAP['artist'])),
            album=self._get_first_value(tags.get(self.TAG_MAP['album'])),
            album_artist=self._get_first_value(tags.get(self.TAG_MAP['album_artist'])),
            year=self._get_first_value(tags.get(self.TAG_MAP['year'])),
            genre=genre,
            track_number=track_num,
            total_tracks=total_tracks,
            disc_number=disc_num,
            total_discs=total_discs,
            lyrics=self._get_first_value(tags.get(self.TAG_MAP['lyrics'])),
            composer=self._get_first_value(tags.get(self.TAG_MAP['composer'])),
            comment=self._get_first_value(tags.get(self.TAG_MAP['comment'])),
            artwork=artwork,
        )

    def _parse_genre(self, genres) -> List[str]:
        """解析流派标签"""
        if genres is None:
            return []
        return [str(g) for g in genres]

    def write(self, metadata: AudioMetadata) -> None:
        tags = self._file.tags
        if tags is None:
            self._file.add_tags()
            tags = self._file.tags

        if metadata.title is not None:
            tags[self.TAG_MAP['title']] = [metadata.title]
        if metadata.artist is not None:
            tags[self.TAG_MAP['artist']] = [metadata.artist]
        if metadata.album is not None:
            tags[self.TAG_MAP['album']] = [metadata.album]
        if metadata.album_artist is not None:
            tags[self.TAG_MAP['album_artist']] = [metadata.album_artist]
        if metadata.year is not None:
            tags[self.TAG_MAP['year']] = [metadata.year]
        if metadata.genre:
            tags[self.TAG_MAP['genre']] = list(metadata.genre)
        if metadata.composer is not None:
            tags[self.TAG_MAP['composer']] = [metadata.composer]
        if metadata.comment is not None:
            tags[self.TAG_MAP['comment']] = [metadata.comment]
        if metadata.lyrics is not None:
            tags[self.TAG_MAP['lyrics']] = [metadata.lyrics]

        # 音轨号
        track_num = metadata.track_number or 0
        total_tracks = metadata.total_tracks or 0
        if track_num or total_tracks:
            tags[self.TAG_MAP['track']] = [(track_num, total_tracks)]

        # 碟片号
        disc_num = metadata.disc_number or 0
        total_discs = metadata.total_discs or 0
        if disc_num or total_discs:
            tags[self.TAG_MAP['disc']] = [(disc_num, total_discs)]

        # 封面
        if metadata.artwork is not None:
            tags[self.TAG_MAP['artwork']] = [
                MP4Cover(metadata.artwork, imageformat=MP4Cover.FORMAT_JPEG)
            ]

    def save(self) -> None:
        self._file.save()
