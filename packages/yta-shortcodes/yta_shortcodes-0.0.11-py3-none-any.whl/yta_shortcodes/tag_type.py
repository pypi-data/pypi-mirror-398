from yta_constants.enum import YTAEnum as Enum


class ShortcodeTagType(Enum):
    """
    The different type of shortcodes that we can handle
    according to their scopes. It could be simple [tag]
    shortcode or a block-scoped one [tag] ... [/tag].
    """
    
    BLOCK = 'block'
    """
    Shortcode type that is built with a start tag [tag], an
    end tag [/tag] and a content between both of those tags.
    """
    SIMPLE = 'simple'
    """
    Shortcode type that is built with a simple tag [tag].
    Also known as atomic shortcode in the native library.
    """