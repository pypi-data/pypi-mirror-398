"""
This has been built by manually checking the information
that the 'yt-dlp' 'extract_info' method gives you. The
values that are set as null are transformed into None 
when parsed in Python, but there are also 'none' values
that are actually strings no indicate, with that string,
something specific that is, by itself, just a string.

I'm transforming the keys to have a more clear and
understandable data structure in my system, but this
increases the difficulty when parsing the data that
comes from the 'yt-dlp' library. You can blame on me,
of course, but I want the information more clear on
my system so anyone can understand it from the data.
The way it is parsed and transformed in the code doesn't
matter. This will not change in the next years because
the information is saved with that format in the 
Youtube databases :).

We have a specific way of handling all the files 
related to a Youtube video. Each of the files have a
specific filename to be persisted in our system, so
we download them with that specific name and then, if
needed, we copy them to the requested 'output_filename'.
This is to be more eficient, at least in the first
stage of the app, so we only download those files once
and work faster.

Thanks to:
- https://gist.github.com/khalid32/129cdd43d7347601a6515eeb6e1bc2da
"""
from yta_youtube.dataclasses import YoutubeVideoScene, YoutubeVideoAudioFormat, YoutubeVideoVideoFormat, YoutubeVideoChapter, YoutubeVideoReturn
from yta_youtube.enums import AudioFormatExtension, VideoFormatExtension, VideoFormatQuality, AudioFormatQuality, YoutubeVideoLanguage, YoutubeSubtitleFormat
from yta_youtube.regex import RegularExpression
from yta_validation.parameter import ParameterValidator
from yta_temp import Temp
from yta_programming.output import Output
from yta_file.handler import FileHandler
from yta_subtitles_parser.dataclasses import Subtitles
from yta_subtitles_parser.parser import SubtitlesParser
from yta_file_downloader import Downloader
from yt_dlp import YoutubeDL
from collections import defaultdict
from typing import Union

import requests


YDL_CONFIG = {
    #'listformats': True,
    'format': 'bestaudio/best',
    #'outtmpl': '%(title)s.%(ext)s', # You can change the PATH as you want
    #'download_archive': 'downloaded.txt',
    'noplaylist': True,   
    'quiet': True,
    'no_warnings': True,
    # 'postprocessors': [{
    #     'key': 'FFmpegExtractAudio',
    #     'preferredcodec': 'mp3',
    #     'preferredquality': '192',
    # }],
    #'progress_hooks': [hook]
}

class YoutubeVideo:
    """
    Class to represent a Youtube video and all its
    information, simplified to make easier working
    with it. This is a base class that will include
    the basic information that can be extracted from
    the public videos and using the awesome yt-dlp
    library.
    """

    @property
    def url(
        self
    ) -> str:
        """
        A shortcut to 'long_url'.
        """
        return self.long_url
    
    @property
    def long_url(
        self
    ) -> str:
        """
        The public youtube video url in long format.

        The long url is like this:
        - `https://www.youtube.com/watch?v={ID}`

        A valid example is this one:
        - `https://www.youtube.com/watch?v=0BjlBnfHcHM`
        """
        return f'https://www.youtube.com/watch?v={self.id}'

    @property
    def short_url(
        self
    ) -> str:
        """
        The public youtube video url in short format.
        Short youtube video urls are transformed into
        long youtube urls when you navigate into them.

        The short url is like this:
        - `youtu.be/{ID}`

        A valid example is this one:
        - `youtu.be/0BjlBnfHcHM`
        """
        return f'youtu.be/{self.id}'
    
    @property
    def data(
        self
    ) -> dict:
        """
        The raw data extracted with yt-dlp library. Please,
        use any other property instead of this directly or
        the behaviour could be unexpected.

        We've dedicated a lot of effort on simplifying the
        way to interact with all the youtube videos 
        available information :).
        """
        # TODO: This information expires due to an expiration
        # token so, should we refresh it?
        if (
            not hasattr(self, '_data') or
            self._data is None
        ):
            self._data = self._youtubedl.extract_info(
                url = self.url,
                download = False
            )

        return self._data
    
    @property
    def thumbnail_url(
        self
    ) -> str:
        """
        The url of the best quality thumbnail.
        """
        return self.data['thumbnail']
    
    @property
    def thumbnail(
        self
    ) -> str:
        """
        The best quality thumbnail is downloaded and
        the filename is returned to be parsed with
        'pillow' or the desired library.

        (!) This method will download the image, so 
        use it carefully.

        TODO: Is this the best way to proceed? I mean,
        making that simple the ability to download 
        resources? If so, what about storing its name
        """
        filename = self._get_filename(f'thumbnail.png')

        return (
            Downloader.download_file(self.thumbnail_url, filename).filename
            if not FileHandler.file_exists(filename) else
            filename
        )
    
    @property
    def title(
        self
    ) -> str:
        """
        The original video title which is in its original
        language.
        """
        return self.data['title']
    
    @property
    def description(
        self
    ) -> str:
        """
        The original video description which is in its
        original language.
        """
        return self.data['description']
    
    @property
    def channel_id(
        self
    ) -> str:
        """
        The id of the channel that owns this video.

        TODO: What is the format, including @ or 
        something (?)
        """
        return self.data['channel_id']
    
    @property
    def channel_url(
        self
    ) -> str:
        """
        The url of the channel that owns this video.

        TODO: Does it include the 'http'? Include
        an example please...
        """
        return self.data['channel_url']
    
    @property
    def duration(
        self
    ) -> int:
        """
        The duration of the video in milliseconds.

        TODO: Maybe better in seconds (?)
        """
        return self.data['duration']
    
    @property
    def number_of_views(
        self
    ) -> int:
        """
        The amount of views.
        """
        return self.data['view_count']
    
    @property
    def is_age_limited(
        self
    ) -> bool:
        """
        A flag that indicates if the video has an age
        limitation or not.

        TODO: I'm not sure about this
        """
        # "age_limit": 0,
        return self.data['age_limit'] == 0
    
    @property
    def categories(
        self
    ) -> list[str]:
        """
        The list of categories includes for this video.

        TODO: Maybe map these categories to Enum (?)
        """
        # "categories": [
        #     "Entertainment"
        # ],
        return self.data['categories']
    
    @property
    def tags(
        self
    ) -> list[str]:
        """
        The list of taggs included on this video.
        """
        return self.data['tags']
    
    @property
    def is_embeddable(
        self
    ) -> bool:
        """
        A flag that indicates if the video can be 
        embedded or not.
        """
        # "playable_in_embed": true,
        return self.data['playable_in_embed']
    
    @property
    def number_of_comments(
        self
    ) -> int:
        """
        The amount of comments.
        """
        return self.data['comment_count']
    
    @property
    def number_of_likes(
        self
    ) -> int:
        """
        The amount of likes.
        """
        return self.data['like_count']
    
    @property
    def channel_name(
        self
    ) -> str:
        """
        The name of the channel in which this video has
        been uploaded.

        TODO: What is the format, including @ or 
        something (?)
        """
        return self.data['channel']
    
    @property
    def channel_number_of_followers(
        self
    ) -> int:
        """
        The amount of followers of the channel in which
        this video has been uploaded.
        """
        return self.data['channel_follower_count']
    
    @property
    def is_channel_verified(
        self
    ) -> bool:
        """
        A flag that indicates if the channel in which 
        this video has been uploaded is verified or not.
        """
        # "channel_is_verified": true,
        return self.data['channel_is_verified']
    
    @property
    def uploader_channel_name(
        self
    ) -> str:
        """
        The name of the channel who uploaded the video.

        TODO: How does this actually work (?)
        """
        return self.data['uploader']
    
    @property
    def uploader_channel_id(
        self
    ) -> str:
        """
        The id of the channel who uploaded the video, that
        is a name starting with @.
        """
        return self.data['uploader_id']
    
    @property
    def uploader_channel_url(
        self
    ) -> str:
        """
        The url to the channel who uploaded the video.

        TODO: Does it include the 'http' (?)
        """
        return self.data['uploader_url']
    
    @property
    def upload_date(
        self
    ) -> str:
        """
        The date in which the video has been uploaded, in
        a YYYYMMDD string format.
        """
        return self.data['upload_date']
    
    @property
    def upload_timestamp(
        self
    ) -> int:
        """
        The timestamp in which the video has been uploaded,
        in milliseconds.
        """
        return self.data['timestamp']
    
    @property
    def visibility(
        self
    ) -> str:
        """
        The visibility (also known as availability) of the
        video, that can be 'public', 'hidden' or 'private'.

        TODO: Does it actually work like that? Can I have a
        'private' value? (maybe if I'm logged in).
        TODO: Turn these values into Enum values.
        """
        return self.data['availability']
    
    @property
    def original_url(
        self
    ) -> str:
        """
        The original url.

        TODO: What is this actually (?)
        """
        return self.data['original_url']
    
    @property
    def full_title(
        self
    ) -> str:
        """
        The full title.

        TODO: I don't know the difference between this
        title and the normal one.
        """
        return self.data['fulltitle']
    
    @property
    def duration_string(
        self
    ) -> str:
        """
        The duration string that is shown in the video
        thumbnail and player.
        """
        return self.data['duration_string']
    
    @property
    def file_size(
        self
    ) -> int:
        """
        The video file size in bytes.

        TODO: Is it actually in bytes (?)
        """
        # "filesize": 21250979,
        return self.data['filesize']
    
    @property
    def file_size_approx(
        self
    ) -> int:
        """
        The video file size in bytes but approximated.

        TODO: What is this and what is it for (?)
        """
        return self.data['filesize_approx']
    
    @property
    def number_of_audio_channels(
        self
    ) -> int:
        """
        The number of audio channels.
        """
        return self.data['audio_channels']
    
    @property
    def quality(
        self
    ) -> float:
        """
        The quality of the video. This is expressed in
        float terms and is defined by Youtube. We have
        mapped those qualities and transformed into
        human-like values.

        TODO: Maybe parse as VideoFormatQuality (?)
        """
        # "quality": 3.0,
        return self.data['quality']
    
    @property
    def height(
        self
    ) -> any:
        """
        The height of the video.

        TODO: I don't know how this is expressed
        """
        # "height": null,
        return self.data['height']
    
    @property
    def width(
        self
    ) -> any:
        """
        The width of the video.

        TODO: I don't know how this is expressed
        """
        # "width": null,
        return self.data['width']
    
    @property
    def language(
        self
    ) -> YoutubeVideoLanguage:
        """
        The original video language in the international
        Google naming. If the original language was 'none'
        it will return a YoutubeVideoLanguage.NO_LANGUAGE
        instance.
        """
        # "language": "en",
        return (
            YoutubeVideoLanguage.to_enum(self.data['language'])
            if self.data['language'] is not None else
            YoutubeVideoLanguage.NO_LANGUAGE
        )
    
    @property
    def language_preference(
        self
    ) -> int:
        """
        The language preference expressed in a number.

        TODO: I need to map these values to obtain the 
        real ones and use enum values instead.
        """
        return self.data['language_preference']

    @property
    def extension(
        self
    ) -> str:
        """
        The extension of the video.

        TODO: Parse and use enum values.
        """
        # TODO: Is this the video or the audio extension (?)
        # "ext": "webm",
        return self.data['ext']
    
    @property
    def video_codec(
        self
    ) -> str:
        """
        The video codec.

        TODO: Parse as enum values
        TODO: This can be none, so we need an enum
        representing that there is no video codec
        TODO: Do we actually need this (?)
        """
        # "vcodec": "none",
        return self.data['vcodec']
    
    @property
    def video_extension(
        self
    ) -> str:
        """
        The video extension.

        TODO: Parse as enum values
        TODO: This can be none, so we need an enum
        represnting that there is no video extension
        TODO: Do we actually need this (?)
        """
        # "video_ext": "none",
        
        return self.data['video_ext']
    
    @property
    def audio_codec(
        self
    ) -> Union[str, None]:
        """
        The audio codec.

        TODO: Parse as enum values.
        TODO: This can be none, so we need an enum
        represnting that there is no audio codec
        TODO: Do we actually need this (?)
        """
        # "acodec": "opus",
        # 'acodec' is inside a format
        return self.data.get('acodec', None)
        return self.data['acodec']
    
    @property
    def audio_extension(
        self
    ) -> str:
        """
        The audio extension.

        TODO: Parse as enum values.
        TODO: This can be none, so we need an enum
        represnting that there is no audio extension
        TODO: Do we actually need this (?)
        """
        # "audio_ext": "webm",
        return self.data['audio_ext']

    @property
    def container(
        self
    ) -> str:
        """
        TODO: I have no idea about what this is
        """
        return self.data['container']
    
    @property
    def protocol(
        self
    ) -> str:
        """
        The protocol used in this video.

        TODO: Do we actually need this (?)
        """
        return self.data['protocol']
    
    @property
    def video_bit_rate(
        self
    ) -> float:
        """
        The video bit rate.

        TODO: Do we actually need this (?)
        """
        return float(self.data['vbr'])
    
    @property
    def audio_bit_rate(
        self
    ) -> float:
        """
        The audio bit rate

        TODO: Do we actually need this (?)
        """
        return float(self.data['abr'])
    
    @property
    def aspect_ratio(
        self
        # TODO: What is the type (?)
    ) -> any:
        """
        The aspect ratio of the video.

        TODO: How does it work? It can be 'none'
        """
        return self.data['aspect_ratio']

    @property
    def format(
        self
    ) -> str:
        """
        The format of the video.

        TODO: I don't know what this is for
        """
        return self.data['format']

    @property
    def most_viewed_scenes(
        self
    ) -> Union[None, list[YoutubeVideoScene]]:
        """
        A list with the most viewed scenes and the time
        in which each of them happen.

        This is based on the user views and it is not
        available in all the videos. If it is not 
        availabile, its value is None.

        This array, if available, is ordered from the 
        most viewed to the less viewed scenes.

        "heatmap": [
            {
                "start_time": 0.0,
                "end_time": 13.65,
                "value": 1.0
            },
            {...}
        ]
        """
        # Apparently, Youtube chooses 100 scenes of a
        # video for this purpose (or at least with long
        # videos), so each scene lasts duration / 100
        if self.data['heatmap'] is None:
            return None
        
        self._most_viewed_scenes = (
            [
                YoutubeVideoScene(scene['start_time'], scene['end_time'], scene['value'])
                for scene in sorted(
                    self.data['heatmap'],
                    key = lambda scene: scene['value'],
                    reverse = True
                )
            ]
            if self._most_viewed_scenes is None else
            self._most_viewed_scenes
        )

        return self.most_viewed_scenes
    
    @property
    def has_most_viewed_scenes(
        self
    ) -> bool:
        """
        A flag that indicates if the video has most viewed
        scenes or not.
        """
        return self.most_viewed_scenes is not None
    
    @property
    def chapters(
        self
    ) -> list[YoutubeVideoChapter, None]:
        """
        A list with the different chapters available for
        the video, that are titles and time segments the
        author defined to help the viewer understand what
        the video is about in the different moments.

        The list of chapters can be None if the author
        didn't define them, so they are not available for
        all the videos in the platform.

        "chapters": [
            {
                "start_time": 0.0,
                "title": "Hola Mundo",
                "end_time": 52.0
            },
            {...}
        ]

        This is the id of a video with chapters available:
        _6N18g3ewnw
        
        """
        return (
            None
            if self.data['chapters'] is None else
            [
                YoutubeVideoChapter(chapter['start_time'], chapter['end_time'], chapter['title'])
                for chapter in self.data['chapters']
            ]
        )
    
    @property
    def has_chapters(
        self
    ) -> bool:
        """
        A flag that indicates if the video has chapters or
        not.
        """
        return self.data['chapters'] is not None

    @property
    def _automatic_subtitles(
        self
    ) -> Union[dict, None]:
        """
        The automatic subtitles of this video, but parsed
        and reorganized to simplify the way we work with
        them. These elements come categorized by the
        languages, as the first key, and with the extension
        (format) when inside an specific language.

        This is an example:
        self._automatic_subtitles = {
            'ar': {
                'json3': {
                    'ext': 'json3',
                    'url': 'https://www.youtube.com/api/timedtext?v=0BjlBnfHcHM&ei=q7WiZ-_hF-6s9fwPtMKTgAQ&caps=asr&opi=112496729&xoaf=5&hl=en&ip=0.0.0.0&ipbits=0&expire=1738741787&sparams=ip%2Cipbits%2Cexpire%2Cv%2Cei%2Ccaps%2Copi%2Cxoaf&signature=05E516DEAE75175E5A6DD593C9E66840BF02236F.DD85AD4467DD56D8EA83C25C610E412C37B8C7AB&key=yt8&lang=ar&fmt=json3',
                    'name': 'Arabic'
                },
                {...}
            },
            {...}
        }
        """
        if (
            not hasattr(self, '__automatic_subtitles') or
            self.__automatic_subtitles is None
        ):
            subtitles = self.data.get('automatic_captions', None)
            self.__automatic_subtitles = defaultdict(dict)
    
            for language, subtitle_elements in subtitles.items():
                for subtitle_element in subtitle_elements:
                    # The element with 'protocol' field is a config file
                    # and not an automatic subtitles file
                    if not 'protocol' in subtitle_element:
                        self.__automatic_subtitles[language][subtitle_element['ext']] = subtitle_element

        return self.__automatic_subtitles
    
    @property
    def has_automatic_subtitles(
        self
    ) -> bool:
        """
        A flag that indicates if this video has automatic
        subtitles or not.
        """
        return self._automatic_subtitles is not None

    @property
    def automatic_subtitles_languages(
        self
    ) -> list[YoutubeVideoLanguage]:
        """
        A list containing all the available automatic 
        subtitles languages. Perfect to choose the desired
        language and download the corresponding automatic
        subtitles.
        """
        # TODO: What if no automatic subtitles? Is it None (?)
        return list([
            YoutubeVideoLanguage.to_enum(language)
            for language in self._automatic_subtitles.keys()
        ])
    
    @property
    def _subtitles(
        self
    ) -> Union[dict, None]:
        """
        The subtitles of this video, but parsed and 
        reorganized to simplify the way we work with them.
        These elements come categorized by the languages,
        as the first key, and with the extension (format)
        when inside an specific language.

        This is an example:
        self._subtitles = {
            'ar': {
                'json3': {
                    'ext': 'json3',
                    'url': 'https://www.youtube.com/api/timedtext?v=0BjlBnfHcHM&ei=q7WiZ-_hF-6s9fwPtMKTgAQ&caps=asr&opi=112496729&xoaf=5&hl=en&ip=0.0.0.0&ipbits=0&expire=1738741787&sparams=ip%2Cipbits%2Cexpire%2Cv%2Cei%2Ccaps%2Copi%2Cxoaf&signature=05E516DEAE75175E5A6DD593C9E66840BF02236F.DD85AD4467DD56D8EA83C25C610E412C37B8C7AB&key=yt8&lang=ar&fmt=json3',
                    'name': 'Arabic'
                },
                {...}
            },
            {...}
        }
        """
        if (
            not hasattr(self, '__subtitles') or
            self.__subtitles is None
        ):
            subtitles = self.data.get('subtitles', None)
            self.__subtitles = defaultdict(dict)
    
            for language, subtitle_elements in subtitles.items():
                for subtitle_element in subtitle_elements:
                    self.__subtitles[language][subtitle_element['ext']] = subtitle_element

        return self.__subtitles
    
    @property
    def has_subtitles(
        self
    ) -> bool:
        """
        A flag that indicates if this video has subtitles
        or not.
        """
        return self._subtitles is not None
    
    @property
    def subtitles_languages(
        self
    ) -> list[YoutubeVideoLanguage]:
        """
        A list containing all the available subtitles
        languages. Perfect to choose the desired language
        and download the corresponding subtitles.
        """
        return list([
            YoutubeVideoLanguage.to_enum(language)
            for language in self._subtitles.keys()
        ])

    @property
    def _formats(
        self
        # TODO: What about the type (?)
    ) -> any:
        """
        *For internal use only*
        
        All the existing formats for this video.
        """
        return self.data['formats']

    @property
    def audio_formats(
        self
    ) -> dict:
        """
        All the audio formats available in the different
        languages. This is a dict, if available, of the
        audio formats for the different languages and in
        different formats.

        There are 3 levels: language, format and quality.

        For example, we can have an audio format with the
        index 'ar' to represent the arabic audio format,
        the 'webm' format and the 'low' audio quality.

        Example of our audio_formats:

        self.audio_formats = {
            'ar': {
                'webm': {
                    'dubbed': YoutubeVideoAudioFormat(...),
                    'low': YoutubeVideoAudioFormat(...),
                    'medium': YoutubeVideoAudioFormat(...)
                }
            },
            {...}
        }
        """
        if (
            not hasattr(self, '_audio_formats') or
            self._audio_formats is None
        ):
            self._audio_formats = {}

            for format in self._formats:
                if (
                    #not format.get('width') and
                    #not format.get('height') and
                    format['resolution'] == 'audio only' and
                    'filesize' in format
                ):
                    # Ensure the language key exists in audio_formats
                    language_key = (
                        format['language']
                        if format['language'] is not None else
                        YoutubeVideoLanguage.NO_LANGUAGE.value
                    )
                    # audio_format.ar = {}
                    self._audio_formats.setdefault(language_key, {})

                    # Ensure the format key, for that language, exist
                    extension_key = format['audio_ext']
                    # audio_format.ar.m4a = {}
                    self._audio_formats[language_key].setdefault(extension_key, {})

                    audio_format = YoutubeVideoAudioFormat(
                        id = format['format_id'],
                        url = format['url'],
                        quality = format['quality'],
                        file_size = format['filesize'],
                        language = language_key,
                        extension = format['ext'],
                        audio_extension = format['audio_ext'],
                        abr = format['abr']
                    )

                    quality_key = AudioFormatQuality.to_enum(format['quality']).as_key
                    # audio_format.ar.m4a.low = YoutubeVideoAudioFormat
                    self._audio_formats[language_key][extension_key][quality_key] = audio_format

        return self._audio_formats
    
    @property
    def video_formats(
        self
    ) -> dict:
        """
        All the video formats available in the different
        languages. This is a dict, if available, of the
        video formats where the different keys are the
        qualities (heights) available as simple strings.

        For example, we can have a video format with the
        index '720' to represent the HD video format, and
        we can obtain it by doing 'video_formats['720']'.

        This method returns a dict in which the keys are
        the video qualities available as simple strings.

        Example of our video_formats:
        
        self.video_formats = {
            '1080': {
                'mp4': YoutubeVideoVideoFormat(...)
            },
            '720': {
                'mp4': YoutubeVideoVideoFormat(...)
            },
            {...}
        }
        """
        if (
            not hasattr(self, '_video_formats') or
            self._video_formats is None
        ):
            self._video_formats = {}

            """
            A video format is a format that contains the
            'aspect_ratio' value and also is not a 'storyboard'
            or 'Premium' content.
            """

            for format in self._formats:
                if (
                    format.get('aspect_ratio') and
                    format.get('format_note') not in ['storyboard', 'Premium'] and
                    format.get('resolution') != 'audio only' and
                    'filesize' in format
                ):
                    # Here we transform the youtube quality value to
                    # our own stringified quality key
                    quality_key = VideoFormatQuality.to_enum(format['quality']).as_key
                    # video_format.1080 = {}
                    self.video_formats.setdefault(quality_key, {})
                    
                    video_format = YoutubeVideoVideoFormat(
                        id = format['format_id'],
                        url = format['url'],
                        quality = format['quality'],
                        file_size = format['filesize'],
                        width = format['width'],
                        height = format['height'],
                        extension = format['ext'],
                        video_extension = format['video_ext'],
                        fps = format['fps'],
                        aspect_ratio = format['aspect_ratio'],
                        vbr = format['vbr']
                    )

                    format_key = format['ext']
                    # video_format.1080.mp4 = instance
                    self._video_formats[quality_key][format_key] = video_format

        return self._video_formats

    @property
    def video_qualities(
        self
    ) -> list[VideoFormatQuality]:
        """
        Get a list with the video qualities that are
        available.
        """
        self._video_qualities = (
            # We store the video formats with the quality.as_key
            # method, so we have to turn back from tthe 'as_key'
            # to the enum
            [
                VideoFormatQuality.from_key(quality_str_key)
                for quality_str_key in self.video_formats.keys()
            ]
            if not hasattr(self, '_video_qualities') else
            self._video_qualities
        )

        return self._video_qualities

    @property
    def audio_languages(
        self
    ) -> list[YoutubeVideoLanguage]:
        """
        Get a list with the audio languages that are
        available.
        """
        self._audio_languages = (
            [
                YoutubeVideoLanguage.to_enum(language_str)
                for language_str in self.audio_formats.keys()
            ]
            if not hasattr(self, '_audio_languages') else
            self._audio_languages
        )

        return self._audio_languages
    
    # TODO: Create properties that pre-calculate the values
    # for the special options such as 'best', 'worst', etc.
    
    def __init__(
        self,
        id_or_url: str,
    ):
        """
        Initialize a YoutubeVideo instance with the given
        'id_or_url', that must be a valid youtube video id
        or url and the video must be available.

        Parameters:
            id_or_url (str): The youtube video ID or URL.
        """
        ParameterValidator.validate_mandatory_string('id_or_url', id_or_url, do_accept_empty = False)

        id_or_url = (
            _get_youtube_video_id_from_url(id_or_url)
            if RegularExpression.YOUTUBE_VIDEO_URL.parse(id_or_url) else
            id_or_url
        )

        if not RegularExpression.YOUTUBE_VIDEO_ID.parse(id_or_url):
            raise Exception('The provided "id_or_url" is not a valid youtube video url or video id.')

        if not is_youtube_video_available(id_or_url):
            raise Exception('The youtube video with the given "id_or_url" is not available.')
        
        self.id: str = id_or_url
        """
        The public youtube video id (which comes in its
        url).

        This is a valid id:
        - `0BjlBnfHcHM`
        """
        # We need to initialize the yt-dlp instance to be able
        # to extract the informationn
        self._youtubedl: YoutubeDL = YoutubeDL(YDL_CONFIG)
        """
        *For internal use only*

        Instance of yt-dlp class to be able to extract
        the information we need.
        """
        self._data: dict = None
        """
        *For internal use only*

        The raw data extracted with yt-dlp library.
        """

        # Initialize properties
        self.data

    def get_automatic_subtitles(
        self,
        language: YoutubeVideoLanguage = YoutubeVideoLanguage.DEFAULT,
        format: YoutubeSubtitleFormat = YoutubeSubtitleFormat.BEST
    ) -> Union[Subtitles, None]:
        """
        Obtain, if available, the automatic subtitles for
        the given 'language' and in the 'format' provided.

        The automatic subtitles are the subtitles generated
        by the platform based on a transcription of the
        audio.

        The automatic subtitles are stored always with the
        same format, so if they have been downloaded
        previously they will be returned instantly.
        """
        if not self.has_automatic_subtitles:
            # No automatic subtitles for any language available
            return None
        
        language = YoutubeVideoLanguage.to_enum(language)
        format = YoutubeSubtitleFormat.to_enum(format)
        
        automatic_subtitles = self._get_subtitles(self._automatic_subtitles, language, format)

        if automatic_subtitles is None:
            # No automatic subtitles available for that
            # language in that format
            return None
        
        # This name will allow us persist the file and return
        # it the next time we need it
        filename = self._get_filename(f'automatic_subtitles_{language.value}.{automatic_subtitles["ext"]}')

        filename = (
            Downloader.download_file(automatic_subtitles['url'], filename).filename
            if not FileHandler.file_exists(filename) else
            filename
        )

        return SubtitlesParser.parse_from_filename(filename)
    
    def get_subtitles(
        self,
        language: YoutubeVideoLanguage = YoutubeVideoLanguage.DEFAULT,
        format: YoutubeSubtitleFormat = YoutubeSubtitleFormat.BEST
    ) -> Union[Subtitles, None]:
        """
        Obtain, if available, the subtitles for the given
        'language' and in the 'format' provided.

        The subtitles are stored always with the same 
        format, so if they have been downloaded previously
        they will be returned instantly.
        """
        if not self.has_subtitles:
            # No subtitles for any language available
            return None
        
        language = YoutubeVideoLanguage.to_enum(language)
        format = YoutubeSubtitleFormat.to_enum(format)

        subtitles = self._get_subtitles(self._subtitles, language, format)

        if subtitles is None:
            # No subtitles available for that language
            # in that format
            return None
        
        # This name will allow us persist the file and return
        # it the next time we need it
        filename = self._get_filename(f'subtitles_{language.value}.{subtitles["ext"]}')

        filename = (
            Downloader.download_file(subtitles['url'], filename).filename
            if not FileHandler.file_exists(filename) else
            filename
        )

        return SubtitlesParser.parse_from_filename(filename)

    def is_video_quality_available(
        self,
        video_quality: VideoFormatQuality
    ) -> bool:
        """
        Check if the provided 'video_quality' is available
        for this video.
        """
        return VideoFormatQuality.to_enum(video_quality) in self.video_qualities

    def is_audio_language_available(
        self,
        audio_language: YoutubeVideoLanguage
    ) -> bool:
        """
        Check if the provided 'audio_language' is available
        for this video.
        """
        return YoutubeVideoLanguage.to_enum(audio_language) in self.audio_languages

    def download(
        self,
        language: YoutubeVideoLanguage = YoutubeVideoLanguage.DEFAULT,
        audio_extension: AudioFormatExtension = AudioFormatExtension.BEST,
        audio_quality: AudioFormatQuality = AudioFormatQuality.BEST,
        video_extension: VideoFormatExtension = VideoFormatExtension.BEST,
        video_quality: VideoFormatQuality = VideoFormatQuality.BEST,
        output_filename: Union[str, None] = None
    ) -> Union[YoutubeVideoReturn, None]:
        """
        Download the video with the given 'video_extension'
        and 'video_quality' with the audio that fits the
        'language', 'audio_extension' and 'audio_quality'
        parameters.

        This method will raise an Exception if no audio or
        video format is found with the parameters provided.
        """
        language = YoutubeVideoLanguage.to_enum(language)
        audio_extension = AudioFormatExtension.to_enum(audio_extension)
        audio_quality = AudioFormatQuality.to_enum(audio_quality)
        video_extension = VideoFormatExtension.to_enum(video_extension)
        video_quality = VideoFormatQuality.to_enum(video_quality)

        audio_format = self._get_audio_format(language, audio_extension, audio_quality)
        # TODO: Maybe, if no available, I have to try
        # with the 'no_language' language
        if audio_format is None:
            raise Exception('Sorry, no audio format available with the given parameters.')
        
        video_format = self._get_video_format(video_quality, video_extension)
        if video_format is None:
            raise Exception('Sorry, no video format available with the given parameters.')

        return YoutubeVideoReturn(
            self,
            self._download_formats(
                [video_format, audio_format],
                # TODO: I think ffmpeg should choose the extension
                # Let ffmpeg choose the extension for me, so we need
                # the 'output_filename' without extension
                Output.get_filename(output_filename, VideoFormatExtension.MP4.value)
            )
        )

    def download_with_best_quality(
        self,
        language: YoutubeVideoLanguage = YoutubeVideoLanguage.DEFAULT,
        audio_quality: AudioFormatQuality = AudioFormatQuality.MEDIUM,
        video_quality: VideoFormatQuality = VideoFormatQuality.FULL_HD,
        output_filename: Union[str, None] = None
    ) -> YoutubeVideoReturn:
        """
        Download the video with the 'video_quality' if
        available, or with the next best quality available,
        and with the audio that fits the 'language' and the
        requested 'audio_quality', or the next best audio
        quality available.

        This method will raise an Exception if no audio or
        video format is found with the parameters provided.
        """
        language = YoutubeVideoLanguage.to_enum(language)
        audio_quality = AudioFormatQuality.to_enum(audio_quality)
        video_quality = VideoFormatQuality.to_enum(video_quality)

        audio_format = self._get_best_available_audio_format(language, audio_quality)
        if audio_format is None:
            # TODO: Maybe, if no available, I have to try
            # with the 'no_language' language
            raise Exception('Sorry, no audio format available with the given parameters.')
        
        video_format = self._get_best_available_video_format(video_quality)
        if video_format is None:
            raise Exception('Sorry, no video format available with the given parameters.')
        
        return YoutubeVideoReturn(
            self,
            self._download_formats(
                [video_format, audio_format],
                # Let ffmpeg choose the extension for me, so we need
                # the 'output_filename' without extension
                Output.get_filename(output_filename, VideoFormatExtension.MP4.value)
            )
        )

    def download_video_with_best_quality(
        self,
        quality: VideoFormatQuality = VideoFormatQuality.FULL_HD,
        output_filename: Union[str, None] = None
    ) -> YoutubeVideoReturn:
        """
        Download the video with the 'quality' if available,
        or with the next best quality available. This method
        guarantees that a video format is downloaded.

        This method will raise an Exception if no audio or
        video format is found with the parameters provided.
        """
        quality = VideoFormatQuality.to_enum(quality)

        video_format = self._get_best_available_video_format(quality)
        if video_format is None:
            raise Exception('No "video" available for the given quality and extension.')

        return YoutubeVideoReturn(
            self,
            self._download_format(
                video_format,
                # First is persistance filename, then output
                filename = self._get_filename(f'video_{quality.as_key}.{video_format.extension.value}'),
                output_filename = Output.get_filename(output_filename, video_format.extension.value)
            )
        )

        # TODO: Remove this below when confirmed that the code
        # above is working correctly
        # if not FileValidator.file_exists(filename):
        #     # I think if 1 it is ok and 0 it is not
        #     YoutubeDL({
        #         'outtmpl': filename,
        #         'format': video_format.id,
        #     }).download(self.url)

        # # TODO: Maybe use a FileReturn (?)
        # # TODO: Handle 'copy_file' when returning None
        # return FileHandler.copy_file(filename, output_filename)
        
    def download_video(
        self,
        extension: VideoFormatExtension = VideoFormatExtension.BEST,
        quality: VideoFormatQuality = VideoFormatQuality.BEST,
        output_filename: Union[str, None] = None
    ) -> YoutubeVideoReturn:
        """
        Download only the video with no audio.

        This method will raise an Exception if no video
        format is found with the parameters provided.
        """
        extension = VideoFormatExtension.to_enum(extension)
        quality = VideoFormatQuality.to_enum(quality)

        video_format = self._get_video_format(quality, extension)
        if video_format is None:
            raise Exception('No "video" available for the given quality and extension.')

        return YoutubeVideoReturn(
            self,
            self._download_format(
                video_format,
                # First is persistance filename, then output
                filename = self._get_filename(f'video_{quality.as_key}.{video_format.extension.value}'),
                output_filename = Output.get_filename(output_filename, video_format.extension.value)
            )
        )

        # TODO: Remove this below when confirmed that the code
        # above is working correctly
        # if not FileValidator.file_exists(filename):
        #     # I think if 1 it is ok and 0 it is not
        #     YoutubeDL({
        #         'outtmpl': filename,
        #         'format': video_format.id,
        #     }).download(self.url)

        # # TODO: Maybe use a FileReturn (?)
        # # TODO: Handle 'copy_file' when returning None
        # return FileHandler.copy_file(filename, output_filename)
    
    def download_audio_with_best_quality(
        self,
        language: YoutubeVideoLanguage = YoutubeVideoLanguage.DEFAULT,
        quality: AudioFormatQuality = AudioFormatQuality.MEDIUM,
        output_filename: Union[str, None] = None 
    ) -> YoutubeVideoReturn:
        """
        Download the audio that fits the 'language' and the
        requested 'quality', or the next best audio quality
        available. This method guarantees that an audio
        format is downloaded.

        This method will raise an Exception if no audio or
        video format is found with the parameters provided.
        """
        language = YoutubeVideoLanguage.to_enum(language)
        quality = AudioFormatQuality.to_enum(quality)

        audio_format = self._get_best_available_audio_format(language, quality)
        # TODO: Maybe, if no available, I have to try
        # with the 'no_language' language
        if audio_format is None:
            raise Exception('No "audio" available for the given language, extension and quality.')

        return YoutubeVideoReturn(
            self,
            self._download_format(
                format = audio_format,
                # First is persistance filename, then output
                filename = self._get_filename(f'audio_{language.value}.{audio_format.extension.value}'),
                output_filename = Output.get_filename(output_filename, audio_format.extension.value)
            )
        )
        
    def download_audio(
        self,
        language: YoutubeVideoLanguage = YoutubeVideoLanguage.DEFAULT,
        extension: AudioFormatExtension = AudioFormatExtension.BEST,
        quality: AudioFormatQuality = AudioFormatQuality.BEST,
        output_filename: Union[str, None] = None
    ) -> YoutubeVideoReturn:
        """
        Download only the audio, with no video, and store
        as the `output_filename` provided.

        This method will raise an Exception if no audio
        format is found with the parameters provided.
        """
        language = YoutubeVideoLanguage.to_enum(language)
        extension = AudioFormatExtension.to_enum(extension)
        quality = AudioFormatQuality.to_enum(quality)

        audio_format = self._get_audio_format(language, extension, quality)
        # TODO: Maybe, if no available, I have to try
        # with the 'no_language' language
        if audio_format is None:
            raise Exception('No "audio" available for the given language, extension and quality.')
        
        return YoutubeVideoReturn(
            self,
            self._download_format(
                audio_format,
                # First is persistance filename, then output
                filename = self._get_filename(f'audio_{language.value}.{audio_format.extension.value}'),
                output_filename = Output.get_filename(output_filename, audio_format.extension.value)
            )
        )
    
    def _get_audio_format(
        self,
        language: YoutubeVideoLanguage = YoutubeVideoLanguage.DEFAULT,
        extension: AudioFormatExtension = AudioFormatExtension.BEST,
        quality: AudioFormatQuality = AudioFormatQuality.BEST
    ) -> Union[YoutubeVideoAudioFormat, None]:
        """
        *For internal use only*

        Get the audio format with the given `language`, `extension`
        and `quality`, if available.
        """
        # TODO: Is it possible to have 0 'audio_formats' (?)
        # A video with no language has a 'no_language' audio
        # format key. Do silenced videos exist? Videos without
        # audio format? I think they don't...
        if not bool(self.audio_formats):
            return None
        
        # Check that variables are valid
        language = YoutubeVideoLanguage.to_enum(language)
        extension = AudioFormatExtension.to_enum(extension)
        quality = AudioFormatQuality.to_enum(quality)

        def _get_audio_format_from_language(
            audio_formats: dict,
            language: YoutubeVideoLanguage
        ):
            """
            Obtain the audio format for the given 'language'.
            The 'audio_formats' provided must be our custom
            and processed audio formats at the top level 
            (level 0).
            """
            language_key = (
                self.language.value
                if language == YoutubeVideoLanguage.DEFAULT
                else language.value
            )

            return audio_formats.get(language_key, None)

        with_language = _get_audio_format_from_language(self.audio_formats, language)

        if with_language is None:
            # No audio available for that language
            return None
        
        def _get_audio_format_from_extension(
            audio_formats: dict,
            extension = AudioFormatExtension
        ):
            """
            Obtain the audio format for the given 'extension'.
            The 'audio_formats' provided must be our custom
            and processed audio formats at level 1, where a
            specific language has been previously chosen.
            """
            if extension in AudioFormatExtension.special_values():
                # We obtain the first available key based on
                # quality
                formats_ordered_by_quality = (
                    AudioFormatExtension.formats_ordered_by_quality()
                    if extension == AudioFormatExtension.BEST
                    else AudioFormatExtension.formats_ordered_by_quality()[::-1]
                )

                extension_key = next(
                    (
                        key.value
                        for key in formats_ordered_by_quality
                        if key.value in audio_formats
                    ),
                    None
                )
            else:
                extension_key = extension.value

            return audio_formats.get(extension_key, None)
        
        with_extension = _get_audio_format_from_extension(with_language, extension)

        if with_extension is None:
            # No audio available with that extension for that language
            return None
        
        def _get_audio_format_from_quality(
            audio_formats: dict,
            quality: AudioFormatQuality
        ):
            """
            Obtain the audio format for the given 'quality'.
            The 'audio_formats' provided must be our custom
            and processed audio formats at level 2, where a
            specific language and a extension have been
            previously chosen.
            """
            if quality in AudioFormatQuality.special_values():
                # We obtain the first available key based on
                # quality
                formats_ordered_by_quality = (
                    AudioFormatQuality.formats_ordered_by_quality()
                    if quality == AudioFormatQuality.BEST
                    else AudioFormatQuality.formats_ordered_by_quality()[::-1]
                )

                quality_key = next(
                    (
                        key.as_key
                        for key in formats_ordered_by_quality
                        if key.as_key in audio_formats
                    ),
                    None
                )
            else:
                quality_key = quality.as_key

            return audio_formats.get(quality_key, None)

        with_quality = _get_audio_format_from_quality(with_extension, quality)

        return with_quality

    def _get_video_format(
        self,
        quality: VideoFormatQuality = VideoFormatQuality.BEST,
        extension: VideoFormatExtension = VideoFormatExtension.BEST,
    ) -> Union[YoutubeVideoVideoFormat, None]:
        """
        Get the video format with the provided 'quality',
        if available.
        """
        # TODO: Is it possible to have 0 'video_formats' (?)
        if not bool(self.video_formats):
            # No formats available
            return None
        
        # Check that variables are valid
        quality = VideoFormatQuality.to_enum(quality)
        extension = VideoFormatExtension.to_enum(extension)

        def _get_video_format_from_quality(
            video_formats: dict,
            quality: VideoFormatQuality
        ):
            """
            Obtain the video format for the given 'quality'.
            The 'video_formats' provided must be our custom
            and processed video formats at the top level 
            (level 0).
            """
            if quality in VideoFormatQuality.special_values():
                # We obtain the first available key based on
                # quality
                formats_ordered_by_quality = (
                    VideoFormatQuality.formats_ordered_by_quality()
                    if quality == VideoFormatQuality.BEST
                    else VideoFormatQuality.formats_ordered_by_quality()[::-1]
                )

                quality_key = next(
                    (
                        key.as_key
                        for key in formats_ordered_by_quality
                        if key.as_key in video_formats
                    ),
                    None
                )
            else:
                quality_key = quality.as_key

            return video_formats.get(quality_key, None)

        with_quality = _get_video_format_from_quality(self.video_formats, quality)

        def _get_video_format_from_extension(
            video_formats: dict,
            extension = VideoFormatExtension
        ):
            """
            Obtain the video format for the given 'extension'.
            The 'video_formats' provided must be our custom
            and processed video formats at level 1, where a
            specific quality has been previously chosen.
            """
            if extension in VideoFormatExtension.special_values():
                # We obtain the first available key based on
                # quality
                formats_ordered_by_quality = (
                    VideoFormatExtension.formats_ordered_by_quality()
                    if extension == VideoFormatExtension.BEST
                    else VideoFormatExtension.formats_ordered_by_quality()[::-1]
                )

                extension_key = next(
                    (
                        key.value
                        for key in formats_ordered_by_quality
                        if key.value in video_formats
                    ),
                    None
                )
            else:
                extension_key = extension.value

            return video_formats.get(extension_key, None)
        
        with_extension = _get_video_format_from_extension(with_quality, extension)

        return with_extension

    def _get_subtitles(
        self,
        subtitles: dict,
        language: YoutubeVideoLanguage,
        format: YoutubeSubtitleFormat
    ) -> Union[dict, None]:
        """
        *For internal use only*

        Method to extract the subtitles of the given
        `language` and `format` from the `subtitles`
        given as parameter. Those ` subtitles` are
        the subtitles once they've been parsed by our
        system.

        This method has been created to avoid code
        duplicity, and is only for internal use. The
        'get_subtitles' and 'get_automatic_subtitles'
        method will call this one.

        This method returns None if there are no
        subtitles for the given `language` and `format`,
        or the final dict of those subtitles if found
        in the given `subtitles` whole parsed dict.
        """
        language = YoutubeVideoLanguage.to_enum(language)

        # There cannot be subtitles without a language set
        language = (
            self.language.value
            if language == YoutubeVideoLanguage.DEFAULT
            else language.value
        )

        with_language = subtitles[language]

        if with_language is None:
            # No subtitles available for that language
            return None
        
        format = YoutubeSubtitleFormat.to_enum(format)
        if format in YoutubeSubtitleFormat.special_values():
            # TODO: This logic below is a bit strange, explain it please
            formats = YoutubeSubtitleFormat.formats_ordered_by_quality()
            if format != YoutubeSubtitleFormat.BEST:
                formats = formats[::-1]

            format = next(
                (
                    key
                    for key in formats
                    if key.value in with_language.keys()
                ),
                None
            )

        return with_language[format.value]

    def _get_best_available_video_format(
        self,
        quality: VideoFormatQuality = VideoFormatQuality.FULL_HD
    ) -> Union[YoutubeVideoVideoFormat, None]:
        """
        *For internal use only*

        Get the video format with the given `quality` if possible,
        or with the next available (below).

        If you ask for the FULL_HD quality but only the HD quality
        is available, the HD quality will be returned.
        """
        quality = VideoFormatQuality.to_enum(quality)

        # We obtain a list with the qualities from the one they
        # are asking for to the last one
        qualities = VideoFormatQuality.formats_ordered_by_quality()
        qualities = qualities[qualities.index(quality):]

        video_format = None
        for quality in qualities:
            video_format = self._get_video_format(quality, VideoFormatExtension.BEST)
            if video_format is not None:
                return video_format

        raise None
    
    def _get_best_available_audio_format(
        self,
        language: YoutubeVideoLanguage = YoutubeVideoLanguage.DEFAULT,
        quality: AudioFormatQuality = AudioFormatQuality.MEDIUM
    ) -> Union[YoutubeVideoAudioFormat, None]:
        """
        *For internal use only*

        Get the audio format with the given 'quality' if possible,
        or with the next available (below).

        If you ask for the MEDIUM quality but only the LOW quality
        is available, the LOW quality will be returned.
        """
        quality = AudioFormatQuality.to_enum(quality)

        # We obtain a list with the qualities from the one they
        # are asking for to the last one
        qualities = AudioFormatQuality.formats_ordered_by_quality()
        qualities = qualities[qualities.index(quality):]

        audio_format = None
        for quality in qualities:
            audio_format = self._get_audio_format(language, AudioFormatExtension.BEST, quality)
            if audio_format is not None:
                return audio_format

        return None

    def _download_format(
        self,
        format: Union[YoutubeVideoVideoFormat, YoutubeVideoAudioFormat],
        filename: str,
        output_filename: Union[str, None]
    ) -> str:
        """
        *For internal use only*

        Download the given audio or video `format`, associated
        with the also provided `filename`, and stores using the
        given `output_filename`.

        This method returns the final name with which the format
        has been downloaded.
        """
        if not FileHandler.file_exists(filename):
            # I think if 1 it is ok and 0 it is not
            YoutubeDL({
                'outtmpl': filename,
                'format': format.id,
            }).download(self.url)

        output_filename = Output.get_filename(output_filename, format.extension.value)
        
        # TODO: Maybe use a FileReturn (?)
        # TODO: Handle 'copy_file' when returning None
        return FileHandler.copy_file(filename, output_filename)
    
    def _download_formats(
        self,
        formats: list[Union[YoutubeVideoAudioFormat, YoutubeVideoVideoFormat]],
        output_filename: Union[str, None] = None
    ) -> str:
        """
        *For internal use only*

        Download the given `formats` and stores them using
        the provided `output_filename`.

        This method returns the final name with which 
        the formats have been downloaded.
        """
        formats_str = '+'.join([
            format.id
            for format in formats
        ])
        
        # I think if 1 it is ok and 0 it is not
        YoutubeDL({
            'outtmpl': output_filename,
            'format': formats_str,
            # We force mp4, but maybe we should not do this...
            'merge_output_format': VideoFormatExtension.MP4.value
            #'merge_output_format': video_format.extension.value
        }).download(self.url)

        # TODO: Maybe use a FileReturn (?)
        return output_filename

    def _get_filename(self, filename: str) -> str:
        """
        *For internal use only*

        Get the full filename for this youtube video 
        based on the given `filename`. This method
        will use the video id to concatenate and build
        a whole filename that is ok for persistance.
        """
        return _get_youtube_video_filename(self.id, filename)


def _get_youtube_video_filename(
    id: str,
    filename: str
) -> str:
    """
    *For internal use only*

    Get the real filename according to the given
    youtube video `id` and the desired `filename`.
    This includes the full path to this file.

    This method is not checking if the provided
    `filename` has an extension or not so please,
    provide a valid `filename`.
    """
    return Temp.get_custom_wip_filename(f'{id}_{filename}')

def _get_youtube_video_id_from_url(
    url: str
) -> Union[str, None]:
    """
    *For internal use only*

    Extracts the video id from the given video `url`.

    This is one example of a valid youtube url:
    - `https://www.youtube.com/watch?v=0BjlBnfHcHM`
    """
    if (
        not RegularExpression.YOUTUBE_VIDEO_SHORT_URL.parse(url) and
        not RegularExpression.YOUTUBE_VIDEO_LONG_URL.parse(url)
    ):
        return None

    match = RegularExpression.YOUTUBE_VIDEO_ID_PART_IN_URL.get_matching_group(url, 0)

    return (
        match.replace('v=', '')
        if match is not None else
        match
    )

def is_youtube_video_available(
    id_or_url: str
) -> bool:
    """
    Check if the provided `id_or_url` is a url or id
    of a youtube video that is available (or not) by
    trying to obtain its thumbnail from a specific url.
    """
    id_or_url = (
        _get_youtube_video_id_from_url(id_or_url)
        if RegularExpression.YOUTUBE_VIDEO_URL.parse(id_or_url) else
        id_or_url
    )

    if not RegularExpression.YOUTUBE_VIDEO_ID.parse(id_or_url):
        raise Exception('The provided "id_or_url" is not a valid youtube video url or video id.')
    
    # This is, apparently, another alternative, and the
    # one that yt-dlp uses for its default 'thumbnail'
    # attribute:
    # https://i.ytimg.com/vi/{id}/mqdefault.jpg
    return requests.get(f'http://img.youtube.com/vi/{id_or_url}/mqdefault.jpg').status_code != 404