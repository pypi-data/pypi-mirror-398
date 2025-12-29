from yta_constants.enum import YTAEnum as Enum


class ShortcodeDuration(Enum):
    """
    Enum class to represent a dynamic value for 
    the shortcode duration so we can calculate it
    later. This duration is valid for both simple
    and block types because it depends on the tag
    (shortode) that is being used.
    """

    FILE_DURATION = 99999
    """
    Represent the duration of a file. This will be
    replaced by the file duration when the 
    shortcode is related to a file and the file is
    downloaded so we know its real duration.
    """
    SHORTCODE_CONTENT = 99998
    """
    Represent the duration of the shortcode 
    content. This means that the shortcode content
    is measured in time and its duration is 
    calculated to be set as this value.
    """

    @classmethod
    def get_default(
        cls
    ):
        return cls.SHORTCODE_CONTENT
    
class SimpleShortcodeStart(Enum):
    """
    Enum class to represent a dynamic shortcode
    start value for the simple shortcode type.
    This will let us calculate the value
    dynamically when needed according to this
    value.
    """

    BETWEEN_WORDS = 'between_words'
    """
    The shortcode will start just in the middle
    of two words that are dictated in narration.
    After the end of the first one and before 
    the start of the next one.
    """
    
class BlockShortcodeStart(Enum):
    """
    Enum class to represent a dynamic shortcode
    start value for the block shortcode type.
    This will let us calculate the value
    dynamically when needed according to this
    value.
    """

    START_OF_FIRST_SHORTCODE_CONTENT_WORD = 'start_of_first_shortcode_content_word'
    """
    The shortcode will start when the first word
    of its content starts being dictated.
    """
    MIDDLE_OF_FIRST_SHORTCODE_CONTENT_WORD = 'middle_of_first_shortcode_content_word'
    """
    The shortcode will start when the first word
    of its content is being dictated, just in the
    middle time between the start and the end of
    its dictation.
    """
    END_OF_FIRST_SHORTCODE_CONTENT_WORD = 'end_of_first_shortcode_content_word'
    """
    The shortcode will start when the first word
    of its content finishes being dictated.
    """

    @classmethod
    def get_default(
        cls
    ):
        return cls.START_OF_FIRST_SHORTCODE_CONTENT_WORD