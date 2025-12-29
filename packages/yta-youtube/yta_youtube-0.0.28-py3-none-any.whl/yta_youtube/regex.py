"""
When working with regular expressions, if we define
groups, that are part of regular expressions wrapped
with parenthesis, we can also obtain the part of the
input string that fits that group. If we don't, we
can only verify, in general, if the input string fits
the regular expression or not.

Holly guacamole, impressive and very useful link below:
- https://webapps.stackexchange.com/questions/54443/format-for-id-of-youtube-video
"""
from yta_constants.regex import RegularExpression as BaseRegularExpression


class RegularExpression(BaseRegularExpression):
    """
    Youtube useful regular expressions.
    """
    
    # TODO: Move this to a more general (or url-specific)
    # regular expression module
    HTTP_OR_HTTPS = r'https?://'
    WWW = r'www\.'

    YOUTUBE_VIDEO_ID = r'[0-9A-Za-z_-]{10}[048AEIMQUYcgkosw]'
    """
    The youtube video id regex.

    Based on this:
    https://webapps.stackexchange.com/questions/54443/format-for-id-of-youtube-video
    """
    YOUTUBE_CHANNEL_ID = r'[0-9A-Za-z_-]{21}[AQgw]'
    """
    The youtube channel id regex.

    Based on this:
    https://webapps.stackexchange.com/questions/54443/format-for-id-of-youtube-video
    """
    YOUTUBE_VIDEO_SHORT_URL = rf'^({HTTP_OR_HTTPS})?({WWW})?(youtu\.be/)({YOUTUBE_VIDEO_ID})(&.*)?$'
    """
    The youtube video short format.
    """
    YOUTUBE_VIDEO_LONG_URL = rf'^({HTTP_OR_HTTPS})?({WWW})?(youtube\.com/watch\?v=)({YOUTUBE_VIDEO_ID})(&.*)?$'
    """
    The youtube video long url format.
    """
    YOUTUBE_VIDEO_URL = rf'({YOUTUBE_VIDEO_SHORT_URL})|({YOUTUBE_VIDEO_LONG_URL})'
    """
    The youtube video url format, that accepts long or short
    urls.
    """
    #YOUTUBE_VIDEO_ID_PART_IN_URL = r'v=([a-zA-Z0-9_-]+)'
    #YOUTUBE_VIDEO_ID_PART_IN_URL = rf'v=(({YOUTUBE_VIDEO_ID})+)'
    YOUTUBE_VIDEO_ID_PART_IN_URL = rf'v=({YOUTUBE_VIDEO_ID})+'
    """
    The youtube video id part in a youtube video url.
    """
    