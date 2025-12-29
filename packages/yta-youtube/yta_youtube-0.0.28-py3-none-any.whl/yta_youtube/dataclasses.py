from yta_youtube.enums import AudioFormatQuality, VideoFormatQuality, AudioFormatExtension, VideoFormatExtension, YoutubeVideoLanguage
from yta_validation.parameter import ParameterValidator
from dataclasses import dataclass


@dataclass
class YoutubeVideoScene:
    """
    Class to represent a youtube video scene, perfect
    to contain the data of the most viewed moments.
    """

    @property
    def mid_time(
        self
    ) -> float:
        """
        The time moment in the middle of the scene, after
        the 'start_time' and before the 'end_time'. This
        value is useful if we need to extract a part of
        this scene but not the whole scene.
        """
        return (self.start_time + self.end_time) / 2

    def __init__(
        self,
        start_time: float,
        end_time: float,
        rating: float
    ):
        ParameterValidator.validate_mandatory_positive_number('start_time', start_time, do_include_zero = True)
        ParameterValidator.validate_mandatory_positive_number('end_time', end_time, do_include_zero = False)
        ParameterValidator.validate_mandatory_number_between('rating', rating, 0.0, 1.0)

        if start_time > end_time:
            raise Exception('The "start_time" cannot be after the "end_time".')
        
        self.start_time: float = start_time
        """
        The time moment in which the video scene starts.
        """
        self.end_time: float = end_time
        """
        The time moment in which the video scene ends.
        """
        self.rating: float = rating
        """
        The rating, from 0 to 1, of how popular is the scene
        in the video.
        """

@dataclass
class YoutubeVideoChapter:
    """
    Class to represent a chapter in a youtube video.
    A chapter is an introduction to the video content
    in different time moments.

    The different video chapters are defined by the
    author of the video and are not always available
    in a youtube video.
    """

    @property
    def mid_time(
        self
    ) -> float:
        """
        The time moment in the middle of the scene, after
        the 'start_time' and before the 'end_time'. This
        value is useful if we need to extract a part of
        this scene but not the whole scene.
        """
        return (self.start_time + self.end_time) / 2

    def __init__(
        self,
        start_time: float,
        end_time: float,
        title: str
    ):
        ParameterValidator.validate_mandatory_positive_number('start_time', start_time, do_include_zero = True)
        ParameterValidator.validate_mandatory_positive_number('start_time', start_time, do_include_zero = False)
        ParameterValidator.validate_mandatory_string('title', title, do_accept_empty = True)

        if start_time > end_time:
            raise Exception('The "start_time" cannot be after the "end_time".')
        
        self.start_time = start_time
        """
        The time moment in which the video chapter starts.
        """
        self.end_time = end_time
        """
        The time moment in which the video chapter ends.
        """
        self.title = title
        """
        The title of the video chapter.
        """

@dataclass
class YoutubeVideoAudioFormat:
    """
    Class to represent an audio format of a youtube
    video.
    """

    def __init__(
        self,
        id: str,
        url: str,
        quality: AudioFormatQuality,
        file_size: int,
        language: YoutubeVideoLanguage,
        extension: AudioFormatExtension,
        audio_extension: AudioFormatExtension,
        abr: str
    ):
        language = YoutubeVideoLanguage.to_enum(language)
        quality = AudioFormatQuality.to_enum(quality)
        extension = AudioFormatExtension.to_enum(extension)
        audio_extension = AudioFormatExtension.to_enum(audio_extension)

        self.id: str = id
        """
        The identifier of the audio format. This is the
        value we must use to download the corresponding
        format using the yt-dlp library.
        """
        self.url: str = url
        """
        The url to download the associated audio file.
        """
        self.quality: AudioFormatQuality = quality
        """
        The quality of the associated audio file.
        """
        self.file_size: int = file_size
        """
        The size of the associated audio file.
        """
        self.language: YoutubeVideoLanguage = language
        """
        The language in which the audio file is built.
        """
        self.extension: AudioFormatExtension = extension
        """
        The extension of the associated audio file.

        TODO: Is this the same value as 'audio_extension' (?)
        """
        self.audio_extension: str = audio_extension
        """
        The extension of the associated audio file.

        TODO: Is this the same value as 'extension' (?)
        TODO: Please, use AudioExtension enum
        """
        self.abr: str = abr
        """
        The audio bit rate value.

        TODO: I don't know if string or what
        TODO: This can be 'none'
        """

    def __str__(
        self
    ) -> str:
        def _format_size(
            size: int
        ) -> str:
            for unit in ("B", "KB", "MB", "GB"):
                if size < 1024:
                    return f"{size:.2f} {unit}"
                size /= 1024
            return f"{size:.2f} TB"

        return (
            "AudioFormat(\n"
            f"  id='{self.id}',\n"
            f"  quality='{self.quality.value}',\n"
            f"  language='{self.language.value}',\n"
            f"  extension='{self.extension.value}',\n"
            f"  audio_extension='{self.audio_extension}',\n"
            f"  abr='{self.abr}',\n"
            f"  file_size={_format_size(self.file_size)},\n"
            f"  url='{self.url}'\n"
            ")"
        )


@dataclass
class YoutubeVideoVideoFormat:
    """
    Class to represent a video format of a youtube
    video. A video format is the video but with a
    specific configuration (fps, quality, etc.).
    """

    def __init__(
        self,
        id: str,
        url: str,
        quality: VideoFormatQuality,
        file_size: int,
        width: int,
        height: int,
        extension: VideoFormatExtension,
        video_extension: VideoFormatExtension,
        fps: float,
        aspect_ratio: float,
        vbr: float
    ):
        quality = VideoFormatQuality.to_enum(quality)
        extension = VideoFormatExtension.to_enum(extension)
        video_extension = VideoFormatExtension.to_enum(video_extension)

        self.id: str = id
        """
        The identifier of the video format. This is the
        value we must use to download the corresponding
        format using the yt-dlp library.
        """
        self.url: str = url
        """
        The url to download the associated video file.
        """
        self.quality: VideoFormatQuality = quality
        """
        The quality of the associated video file.
        """
        self.file_size: int = file_size
        """
        The size of the associated video file.
        """
        self.width: int = width
        """
        The width of the associated video file.
        """
        self.height: int = height
        """
        The height of the associated video file.
        """
        self.extension: VideoFormatExtension = extension
        """
        The extension of the associated video file.

        TODO: Is this the same value as 'video_extension' (?)
        """
        self.video_extension: str = video_extension
        """
        The extension of the associated video file.

        TODO: Is this the same value as 'extension' (?)
        TODO: Please, use VideoExtension enum
        """
        self.fps: float = fps
        """
        The number of frames per second of the associated
        video file. There are values like 29,97.
        """
        self.aspect_ratio: float = aspect_ratio
        """
        The aspect ratio of the associated video file, 
        which is the proportional relationship between
        the width of a video image compared to its
        height.
        """
        self.vbr: float = vbr
        """
        The video bit rate value.

        TODO: I don't know if it can be string ('none')
        """

    def __str__(
        self
    ) -> str:
        def _format_size(
            size: int
        ) -> str:
            for unit in ("B", "KB", "MB", "GB"):
                if size < 1024:
                    return f"{size:.2f} {unit}"
                size /= 1024
            return f"{size:.2f} TB"

        return (
            "VideoFormat(\n"
            f"  id='{self.id}',\n"
            f"  quality='{self.quality.value}',\n"
            f"  resolution={self.width}x{self.height},\n"
            f"  aspect_ratio={self.aspect_ratio:.2f},\n"
            f"  fps={self.fps:.2f},\n"
            f"  extension='{self.extension.value}',\n"
            f"  video_extension='{self.video_extension}',\n"
            f"  vbr={self.vbr},\n"
            f"  file_size={_format_size(self.file_size)},\n"
            f"  url='{self.url}'\n"
            ")"
        )


@dataclass
class YoutubeVideoReturn:
    """
    @dataclass
    Class to represent a youtube video (or only its
    audio) that has been downloaded and to return the
    information about that video (including its id
    for non-repeating purposes) and the filename with
    which the video has been downloaded.
    """

    @property
    def id(
        self
    ):
        """
        The id of the youtube video that has been
        downloaded.
        """
        return self.youtube_video.id

    def __init__(
        self,
        youtube_video: 'YoutubeVideo',
        output_filename: str
    ):
        self.youtube_video: 'YoutubeVideo' = youtube_video
        """
        The 'YoutubeVideo' dataclass instance that holds the
        information about the video found.

        The video that has been downloaded. Remember that
        the download could have been only the audio, but
        here it is the information about the whole video.
        """
        self.output_filename: str = output_filename
        """
        The local filename with which the video has been
        downloaded and stored locally.
        """