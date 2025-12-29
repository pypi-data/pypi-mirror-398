"""
This has been deducted by manually extracting 
different videos information and analyzing it.

Audio formats are written like this:
-1.0 is dubbed
2.0 is low
3.0 is medium

Video formats are written like this:
5.0 is 240p
6.0 is 360p
7.0 is 480p
8.0 is 720p
9.0 is 1080p
"""
from yta_constants.file import SubtitleFileExtension, AudioFileExtension, VideoFileExtension
from yta_constants.lang import Language
from yta_constants.enum import YTAEnum as Enum
from typing import Union


class AudioFormatQuality(Enum):
    """
    The quality possible values in an audio
    format.
    """
    
    DUBBED = -1.0
    """
    An audio that is actually a dub in the
    specific language, so it is a specific
    file uploaded to be included with the
    video, not the original video audio.
    """
    LOW_DRC = 1.5
    """
    Original video audio in low quality and
    with drc.
    """
    LOW = 2.0
    """
    Original video audio but in low quality.
    """
    MEDIUM_DRC = 2.5
    """
    Original video audio in medium quality
    and with drc.
    """
    MEDIUM = 3.0
    """
    Original video audio but in medium
    quality.
    """
    # These ones below are created by me to be
    # able to handle them dynamically
    BEST = 999
    """
    The best available quality, that guarantees that
    one of the existing qualities will be chosen
    dynamically when processing. This is very useful
    when you prioritize the quality.
    """
    WORST = 998
    """
    The worst available quality, that guarantees that
    one of the existing qualities will be choosen
    dynamically when processing. This is very useful 
    when you prioritize the speed.
    """
    # TODO: Is there any other audio quality (?)

    @property
    def as_key(
        self
    ) -> str:
        """
        The audio format quality as a string that can
        be used to identify an audio format once it's
        been processed by our system.

        The 'BEST' and 'WORST' items cannot be
        transformed into a string because they have
        been created for dynamic quality choosing.
        """
        if self in AudioFormatQuality.special_values():
            # TODO: Make this exception message dynamic
            raise Exception('The BEST and WORST qualities cannot use the "as_key" property.')

        return {
            AudioFormatQuality.DUBBED: 'dubbed',
            AudioFormatQuality.LOW_DRC: 'low_drc',
            AudioFormatQuality.LOW: 'low',
            AudioFormatQuality.MEDIUM_DRC: 'medium_drc',
            AudioFormatQuality.MEDIUM: 'medium',
        }[self]

    @staticmethod
    def real_values(
    ) -> list['Enum']:
        """
        Obtain all the values that are actually extension
        values and not special and dynamic values to be
        processed in a special way.
        """
        return AudioFormatQuality.get_all() - AudioFormatQuality.special_values()
    
    @staticmethod
    def special_values(
    ) -> list['Enum']:
        """
        Obtain all the values that are special an dynamic
        to be processed in a special way.
        """
        return [AudioFormatQuality.BEST, AudioFormatQuality.WORST]
    
    @staticmethod
    def formats_ordered_by_quality(
    ) -> list['Enum']:
        """
        The audio formats but ordered by quality to get 
        dynamically the best quality format that is
        available.

        You can use this keys, in order, to access to
        the first available extension for our audio
        formats that have been processed.
        """
        return [
            AudioFormatQuality.MEDIUM,
            AudioFormatQuality.MEDIUM_DRC,
            AudioFormatQuality.LOW,
            AudioFormatQuality.LOW_DRC,
            AudioFormatQuality.DUBBED
        ]

class VideoFormatQuality(Enum):
    """
    The quality possible values in a video
    format. The values are the ones that
    youtube use to identify those qualities.
    """

    SUPER_LOW_SD = 0.0
    """
    A quality of 144p. Its corresponding 
    string key is `144`.
    """
    LOW_SD = 5.0
    """
    A quality of 240p. Its corresponding 
    string key is `240`.
    """
    SD = 6.0
    """
    A quality of 360p. Its corresponding
    string key is `360`.
    """
    HIGH_SD = 7.0
    """
    A quality of 480p. Its corresponding
    string key is `480`.
    """
    HD = 8.0
    """
    A quality of 720p. Its corresponding
    string key is `720`.
    """
    FULL_HD = 9.0
    """
    A quality of 1080p. Its corresponding
    string key is `1080`.
    """
    QUAD_HD_2K = 10.0
    """
    A quality of 1440p. Its corresponding
    string key is `1440`.
    """
    ULTRA_HD_4K = 11.0
    """
    A quality of 2160p. Its corresponding
    string key is `2160`.
    """
    ULTRA_HD_8K = 12.0
    """
    A quality of 4320p. Its corresponding
    string key is `4320`.

    # TODO: Not sure if it is 12.0
    """
    # These ones below are created by me to be
    # able to handle them dynamically
    BEST = 999
    """
    The best available quality, that guarantees that
    one of the existing qualities will be chosen
    dynamically when processing. This is very useful
    when you prioritize the quality.
    """
    WORST = 998
    """
    The worst available quality, that guarantees that
    one of the existing qualities will be choosen
    dynamically when processing. This is very useful 
    when you prioritize the speed.
    """
    # TODO: Maybe we need to ask for a video that is
    # available in 4k and obtain its quality value

    @property
    def as_key(
        self
    ) -> str:
        """
        The video format quality as a string that can
        be used to identify a video format once it's
        been processed by our system.

        The 'BEST' and 'WORST' items cannot be
        transformed into a string because they have
        been created for dynamic quality choosing.
        """
        if self in AudioFormatQuality.special_values():
            # TODO: Make this exception message dynamic
            raise Exception('The BEST and WORST qualities cannot use the "as_key" property.')

        return {
            VideoFormatQuality.SUPER_LOW_SD: '144',
            VideoFormatQuality.LOW_SD: '240',
            VideoFormatQuality.SD: '360',
            VideoFormatQuality.HIGH_SD: '480',
            VideoFormatQuality.HD: '720',
            VideoFormatQuality.FULL_HD: '1080',
            VideoFormatQuality.QUAD_HD_2K: '1440',
            VideoFormatQuality.ULTRA_HD_4K: '2160',
            VideoFormatQuality.ULTRA_HD_8K: '4320'
        }[self]

    @staticmethod
    def from_key(
        key: str
    ) -> Union['VideoFormatQuality', None]:
        """
        Turn a string video format quality key to the
        corresponding VideoFormatQuality Enum instance.
        """
        return {
            '144': VideoFormatQuality.SUPER_LOW_SD,
            '240': VideoFormatQuality.LOW_SD,
            '360': VideoFormatQuality.SD,
            '480': VideoFormatQuality.HIGH_SD,
            '720': VideoFormatQuality.HD,
            '1080': VideoFormatQuality.FULL_HD,
            '1440': VideoFormatQuality.QUAD_HD_2K,
            '2160': VideoFormatQuality.ULTRA_HD_4K,
            '4320': VideoFormatQuality.ULTRA_HD_8K
        }.get(key, None)
    
    @staticmethod
    def real_values(
    ) -> list['Enum']:
        """
        Obtain all the values that are actually extension
        values and not special and dynamic values to be
        processed in a special way.
        """
        return VideoFormatQuality.get_all() - VideoFormatQuality.special_values()
    
    @staticmethod
    def special_values(
    ) -> list['Enum']:
        """
        Obtain all the values that are special an dynamic
        to be processed in a special way.
        """
        return [VideoFormatQuality.BEST, VideoFormatQuality.WORST]

    @staticmethod
    def formats_ordered_by_quality(
    ) -> list['Enum']:
        """
        The video formats but ordered by quality to get 
        dynamically the best quality format that is
        available.

        You can use this keys, in order, to access to
        the first available extension for our audio
        formats that have been processed.
        """
        return [
            VideoFormatQuality.ULTRA_HD_8K,
            VideoFormatQuality.ULTRA_HD_4K,
            VideoFormatQuality.QUAD_HD_2K,
            VideoFormatQuality.FULL_HD,
            VideoFormatQuality.HD,
            VideoFormatQuality.HIGH_SD,
            VideoFormatQuality.SD,
            VideoFormatQuality.LOW_SD,
            VideoFormatQuality.SUPER_LOW_SD
        ]

class AudioFormatExtension(Enum):
    """
    The extension possible values in an audio
    format.
    """

    WEBM = AudioFileExtension.WEBM.value
    M4A = AudioFileExtension.M4A.value
    # Yes, they use mp4 extension for dubbed audios, so
    # they only get the audio from that file and they 
    # flag it with 'resolution = "audio only"'
    MP4 = VideoFileExtension.MP4.value
    # Especial value to obtain it dynamically 
    BEST = 'best'
    """
    The best available extension, that guarantees that
    one of the existing extensions will be chosen
    dynamically when processing. This is very useful
    when you prioritize the quality.
    """
    WORST = 'worst'
    """
    The worst available extension, that guarantees that
    one of the existing extensions will be choosen
    dynamically when processing. This is very useful 
    when you prioritize the speed.
    """

    @staticmethod
    def real_values(
    ) -> list['Enum']:
        """
        Obtain all the values that are actually extension
        values and not special and dynamic values to be
        processed in a special way.
        """
        return AudioFormatExtension.get_all() - AudioFormatExtension.special_values()
    
    @staticmethod
    def special_values(
    ) -> list['Enum']:
        """
        Obtain all the values that are special an dynamic
        to be processed in a special way.
        """
        return [AudioFormatExtension.BEST, AudioFormatExtension.WORST]
    
    @staticmethod
    def formats_ordered_by_quality(
    ) -> list['Enum']:
        """
        The audio formats but ordered by quality to get 
        dynamically the best quality format that is
        available.

        You can use this keys, in order, to access to
        the first available extension for our audio
        formats that have been processed.
        """
        return [
            AudioFormatExtension.M4A,
            AudioFormatExtension.MP4,
            AudioFormatExtension.WEBM
        ]

class VideoFormatExtension(Enum):
    """
    The extension possible values in a video
    format.
    """

    MP4 = VideoFileExtension.MP4.value
    WEBM = VideoFileExtension.WEBM.value
    # Especial value to obtain it dynamically below
    BEST = 'best'
    """
    The best available extension, that guarantees that
    one of the existing extensions will be chosen
    dynamically when processing. This is very useful
    when you prioritize the quality.
    """
    WORST = 'worst'
    """
    The worst available extension, that guarantees that
    one of the existing extensions will be choosen
    dynamically when processing. This is very useful 
    when you prioritize the speed.
    """

    @staticmethod
    def real_values(
    ) -> list['Enum']:
        """
        Obtain all the values that are actually extension
        values and not special and dynamic values to be
        processed in a special way.
        """
        return VideoFormatExtension.get_all() - VideoFormatExtension.special_values()
    
    @staticmethod
    def special_values(
    ) -> list['Enum']:
        """
        Obtain all the values that are special an dynamic
        to be processed in a special way.
        """
        return [VideoFormatExtension.BEST, VideoFormatExtension.WORST]
    
    @staticmethod
    def formats_ordered_by_quality(
    ) -> list['Enum']:
        """
        The video formats but ordered by quality to get 
        dynamically the best quality format that is
        available.

        You can use this keys, in order, to access to
        the first available extension for our video
        formats that have been processed.
        """
        return [
            VideoFormatExtension.WEBM,
            VideoFormatExtension.MP4
        ]
    
class YoutubeSubtitleFormat(Enum):
    """
    The available formats for the youtube subtitles.
    """

    TTML = SubtitleFileExtension.TTML.value
    """
    Timed Text Markup Language
    """
    SRT = SubtitleFileExtension.SRT.value
    """
    SubRip Subtitle
    """
    VTT = SubtitleFileExtension.VTT.value
    """
    WebVTT
    """
    JSON3 = SubtitleFileExtension.JSON3.value
    """
    Json3
    """
    SRV1 = SubtitleFileExtension.SRV1.value
    """
    Srv1
    """
    SRV2 = SubtitleFileExtension.SRV2.value
    """
    Srv2
    """
    SRV3 = SubtitleFileExtension.SRV3.value
    """
    Srv3
    """
    BEST = 'best'
    """
    The best available subtitles, that guarantees that
    one of the existing subtitles will be chosen
    dynamically when processing.
    """
    WORST = 'worst'
    """
    The worst available subtitles, that guarantees that
    one of the existing subtitles will be chosen
    dynamically when processing. This doesn't make too
    much sense, but here it is. Worst subtitles also 
    means the more simple.
    """

    @staticmethod
    def real_values(
    ) -> list['Enum']:
        """
        Obtain all the values that are actually subtitle
        format values and not special and dynamic values
        to be processed in a special way.
        """
        return YoutubeSubtitleFormat.get_all() - YoutubeSubtitleFormat.special_values()
    
    @staticmethod
    def special_values(
    ) -> list['Enum']:
        """
        Obtain all the values that are special an dynamic
        to be processed in a special way.
        """
        return [YoutubeSubtitleFormat.BEST, YoutubeSubtitleFormat.WORST]

    @staticmethod
    def formats_ordered_by_quality(
    ) -> list['Enum']:
        """
        The subtitle formats but ordered by quality
        to get  dynamically the best quality format
        that is available.

        You can use this keys, in order, to access to
        the first available subtitle format for our
        audio formats that have been processed.
        """
        return [
            YoutubeSubtitleFormat.TTML,
            YoutubeSubtitleFormat.SRT,
            YoutubeSubtitleFormat.VTT,
            YoutubeSubtitleFormat.JSON3,
            YoutubeSubtitleFormat.SRV1,
            YoutubeSubtitleFormat.SRV2,
            YoutubeSubtitleFormat.SRV3
        ]
    
class YoutubeVideoLanguage(Enum):
    """
    The languages that are available in the youtube
    videos. This class includes all the general
    Language Enum class values (because this
    general class works with the Google languages)
    and a pair of values for dynamic purposes.

    A youtube that has been published in youtube
    can have no language set, and if set, it is
    its default language. Thats why we've created
    the DEFAULT and NO_LANGUAGE values, to be 
    able to handle these situations.
    """

    DEFAULT = 'default'
    """
    This value has been created for those cases
    in which there is a default language that is
    being used in the situation we are handling.

    Using this value will provide that default
    language. For example, a Youtube video can
    be in Turkish or in English as default,
    depending on the author. Using this 'default'
    value will ensure you obtain that Youtube
    video because that default language will
    always exist.
    """
    NO_LANGUAGE = 'no_language'
    """
    This value has been created for those cases
    in which there is not language set in the 
    audio format, so we need a way to represent
    it as a dict key. The raw values is None, 
    but we need a valid dict key to be able to
    access it later.
    """
    ABKHAZIAN = Language.ABKHAZIAN.value
    AFAR = Language.AFAR.value
    AFRIKAANS = Language.AFRIKAANS.value
    AKAN = Language.AKAN.value
    ALBANIAN = Language.ALBANIAN.value
    AMHARIC = Language.AMHARIC.value
    ARABIC = Language.ARABIC.value
    ARAGONESE = Language.ARAGONESE.value
    ARMENIAN = Language.ARMENIAN.value
    ASSAMESE = Language.ASSAMESE.value
    AVARIC = Language.AVARIC.value
    AVESTAN = Language.AVESTAN.value
    AYMARA = Language.AYMARA.value
    AZERBAIJANI = Language.AZERBAIJANI.value
    BAMBARA = Language.BAMBARA.value
    BASHKIR = Language.BASHKIR.value
    BASQUE = Language.BASQUE.value
    BELARUSIAN = Language.BELARUSIAN.value
    BENGALI = Language.BENGALI.value
    BISLAMA = Language.BISLAMA.value
    BOSNIAN = Language.BOSNIAN.value
    BRETON = Language.BRETON.value
    BULGARIAN = Language.BULGARIAN.value
    BURMESE = Language.BURMESE.value
    CATALAN = Language.CATALAN.value
    CHAMORRO = Language.CHAMORRO.value
    CHECHEN = Language.CHECHEN.value
    CHICHEWA = Language.CHICHEWA.value
    CHINESE = Language.CHINESE.value
    CHINESE_TRADITIONAL = Language.CHINESE_TRADITIONAL.value
    # TODO: I think there are more complex values like
    # this above, but they are not in the list
    CHURCH_SLAVONIC = Language.CHURCH_SLAVONIC.value
    CHUVASH = Language.CHUVASH.value
    CORNISH = Language.CORNISH.value
    CORSICAN = Language.CORSICAN.value
    CREE = Language.CREE.value
    CROATIAN = Language.CROATIAN.value
    CZECH = Language.CZECH.value
    DANISH = Language.DANISH.value
    DIVEHI = Language.DIVEHI.value
    DUTCH = Language.DUTCH.value
    DZONGKHA = Language.DZONGKHA.value
    ENGLISH = Language.ENGLISH.value
    ENGLISH_FROM_AMERICA = 'en-US'
    ESPERANTO = Language.ESPERANTO.value
    ESTONIAN = Language.ESTONIAN.value
    EWE = Language.EWE.value
    FAROESE = Language.FAROESE.value
    FIJIAN = Language.FIJIAN.value
    FINNISH = Language.FINNISH.value
    FRENCH = Language.FRENCH.value
    WESTERN_FRISIAN = Language.WESTERN_FRISIAN.value
    FULAH = Language.FULAH.value
    GAELIC = Language.GAELIC.value
    GALICIAN = Language.GALICIAN.value
    GANDA = Language.GANDA.value
    GEORGIAN = Language.GEORGIAN.value
    GERMAN = Language.GERMAN.value
    GREEK = Language.GREEK.value
    KALAALLISUT = Language.KALAALLISUT.value
    GUARANI = Language.GUARANI.value
    GUJARATI = Language.GUJARATI.value
    HAITIAN = Language.HAITIAN.value
    HAUSA = Language.HAUSA.value
    HEBREW = Language.HEBREW.value
    HERERO = Language.HERERO.value
    HINDI = Language.HINDI.value
    HIRI_MOTU = Language.HIRI_MOTU.value
    HUNGARIAN = Language.HUNGARIAN.value
    ICELANDIC = Language.ICELANDIC.value
    IDO = Language.IDO.value
    IGBO = Language.IGBO.value
    INDONESIAN = Language.INDONESIAN.value
    INTERLINGUA = Language.INTERLINGUA.value
    INTERLINGUE = Language.INTERLINGUE.value
    INUKTITUT = Language.INUKTITUT.value
    INUPIAQ = Language.INUPIAQ.value
    IRISH = Language.IRISH.value
    ITALIAN = Language.ITALIAN.value
    JAPANESE = Language.JAPANESE.value
    JAVANESE = Language.JAVANESE.value
    KANNADA = Language.KANNADA.value
    KANURI = Language.KANURI.value
    KASHMIRI = Language.KASHMIRI.value
    KAZAKH = Language.KAZAKH.value
    CENTRAL_KHMER = Language.CENTRAL_KHMER.value
    KIKUYU = Language.KIKUYU.value
    KINYARWANDA = Language.KINYARWANDA.value
    KYRGYZ = Language.KYRGYZ.value
    KOMI = Language.KOMI.value
    KONGO = Language.KONGO.value
    KOREAN = Language.KOREAN.value
    KUANYAMA = Language.KUANYAMA.value
    KURDISH = Language.KURDISH.value
    LAO = Language.LAO.value
    LATIN = Language.LATIN.value
    LATVIAN = Language.LATVIAN.value
    LIMBURGAN = Language.LIMBURGAN.value
    LINGALA = Language.LINGALA.value
    LITHUANIAN = Language.LITHUANIAN.value
    LUBA_KATANGA = Language.LUBA_KATANGA.value
    LUXEMBOURGISH = Language.LUXEMBOURGISH.value
    MACEDONIAN = Language.MACEDONIAN.value
    MALAGASY = Language.MALAGASY.value
    MALAY = Language.MALAY.value
    MALAYALAM = Language.MALAYALAM.value
    MALTESE = Language.MALTESE.value
    MANX = Language.MANX.value
    MAORI = Language.MAORI.value
    MARATHI = Language.MARATHI.value
    MARSHALLESE = Language.MARSHALLESE.value
    MONGOLIAN = Language.MONGOLIAN.value
    NAURU = Language.NAURU.value
    NAVAJO = Language.NAVAJO.value
    NORTH_NDEBELE = Language.NORTH_NDEBELE.value
    SOUTH_NDEBELE = Language.SOUTH_NDEBELE.value
    NDONGA = Language.NDONGA.value
    NEPALI = Language.NEPALI.value
    NORWEGIAN = Language.NORWEGIAN.value
    NORWEGIAN_BOKMAL = Language.NORWEGIAN_BOKMAL.value
    NORWEGIAN_NYNORSK = Language.NORWEGIAN_NYNORSK.value
    OCCITAN = Language.OCCITAN.value
    OJIBWA = Language.OJIBWA.value
    ORIYA = Language.ORIYA.value
    OROMO = Language.OROMO.value
    OSSETIAN = Language.OSSETIAN.value
    PALI = Language.PALI.value
    PASHTO = Language.PASHTO.value
    PERSIAN = Language.PERSIAN.value
    POLISH = Language.POLISH.value
    PORTUGUESE = Language.PORTUGUESE.value
    PUNJABI = Language.PUNJABI.value
    QUECHUA = Language.QUECHUA.value
    ROMANIAN = Language.ROMANIAN.value
    ROMANSH = Language.ROMANSH.value
    RUNDI = Language.RUNDI.value
    RUSSIAN = Language.RUSSIAN.value
    NORTHERN_SAMI = Language.NORTHERN_SAMI.value
    SAMOAN = Language.SAMOAN.value
    SANGO = Language.SANGO.value
    SANSKRIT = Language.SANSKRIT.value
    SARDINIAN = Language.SARDINIAN.value
    SERBIAN = Language.SERBIAN.value
    SHONA = Language.SHONA.value
    SINDHI = Language.SINDHI.value
    SINHALA = Language.SINHALA.value
    SLOVAK = Language.SLOVAK.value
    SLOVENIAN = Language.SLOVENIAN.value
    SOMALI = Language.SOMALI.value
    SOUTHERN_SOTHO = Language.SOUTHERN_SOTHO.value
    SPANISH = Language.SPANISH.value
    SPANISH_FROM_AMERICA = 'es-US'
    SUNDANESE = Language.SUNDANESE.value
    SWAHILI = Language.SWAHILI.value
    SWATI = Language.SWATI.value
    SWEDISH = Language.SWEDISH.value
    TAGALOG = Language.TAGALOG.value
    TAHITIAN = Language.TAHITIAN.value
    TAJIK = Language.TAJIK.value
    TAMIL = Language.TAMIL.value
    TATAR = Language.TATAR.value
    TELUGU = Language.TELUGU.value
    THAI = Language.THAI.value
    TIBETAN = Language.TIBETAN.value
    TIGRINYA = Language.TIGRINYA.value
    TONGA = Language.TONGA.value
    TSONGA = Language.TSONGA.value
    TSWANA = Language.TSWANA.value
    TURKISH = Language.TURKISH.value
    TURKMEN = Language.TURKMEN.value
    TWI = Language.TWI.value
    UIGHUR = Language.UIGHUR.value
    UKRAINIAN = Language.UKRAINIAN.value
    URDU = Language.URDU.value
    UZBEK = Language.UZBEK.value
    VENDA = Language.VENDA.value
    VIETNAMESE = Language.VIETNAMESE.value
    VOLAPUK = Language.VOLAPUK.value
    WALLOON = Language.WALLOON.value
    WELSH = Language.WELSH.value
    WOLOF = Language.WOLOF.value
    XHOSA = Language.XHOSA.value
    SICHUAN_YI = Language.SICHUAN_YI.value
    YIDDISH = Language.YIDDISH.value
    YORUBA = Language.YORUBA.value
    ZHUANG = Language.ZHUANG.value
    ZULU = Language.ZULU.value

# TODO: When I'm able to inherit one YTAEnum class
# from another, make both VideoFormatExtension and
# AudioFormatExtension inherit from a common class
# that includes the 'real_values' and
# 'special_values' methods to avoid duplicated code
# and also with VideoFormatQuality and
# AudioFormatQuality

__all__ = [
    'YoutubeVideoLanguage',
    'YoutubeSubtitleFormat',
    'AudioFormatQuality',
    'VideoFormatQuality',
    'AudioFormatExtension',
    'VideoFormatExtension',
]