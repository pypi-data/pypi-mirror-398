from yta_shortcodes.enums import ShortcodeDuration, SimpleShortcodeStart, BlockShortcodeStart
from yta_shortcodes.tag_type import ShortcodeTagType
from yta_programming.decorators.requires_dependency import requires_dependency
from yta_validation import PythonValidator
from typing import Union


class Shortcode:
    """
    Base shortcode class that represent the minimum
    a shortcode can have. This class is pretended 
    to be used as a model to create a custom class.

    This class represent a shortcode once its been
    detected in the code with the Shortcode parser
    based on its corresponding shortcode tag that
    was registered to enable the detection, and
    includes the attributes found, the content (if
    existing) and the indexes of the words that 
    were inmediately before the start and end tag.
    """

    def __init__(
        self,
        tag: str,
        type: ShortcodeTagType,
        context: any,
        content: str,
        attributes: list[dict],
        index_previous_word_start: Union[int, None] = None,
        index_previous_word_end: Union[int, None] = None,
    ):
        type = ShortcodeTagType.to_enum(type)

        self.tag: str = tag
        """
        The tag of the shortcode, which is the specific key that
        will be detected as the shortcode and the unique identifier
        of that shortcode.

        For the shortcodes `[namesh]` and `[namesh]text[/namesh]`,
        the `tag` value is `"namesh"`.
        """
        self._type: ShortcodeTagType = type
        """
        *For internal use only*

        The type of the shortcode, that can be `simple` or `block`
        scoped.
        """
        self._context: any = context
        """
        *For internal use only*

        The specific context of the shortcode, used to identify
        where are we using this shortcode.
        """
        self.content: Union[None, str] = content
        """
        The content of the shortcode, that will be None if it is a
        simple shortcode, or a string if it is a block-scoped
        shortcode.
        """
        self.attributes: list[dict] = attributes
        """
        The list of attributes found when reading the shortcode.
        These attributes can be single values (from args) or
        key-values (from kwargs).
        """
        self.index_previous_word_start: Union[int, None] = index_previous_word_start
        """
        The index of the word that is inmediately before the opening
        tag of this shortcode. Could be None if the shortcode is just
        at the begining. This index is considered within the text
        empty of shortcodes (once they've been detected and removed).
        """
        self.index_previous_word_end: Union[int, None] = index_previous_word_end
        """
        The index of the word that is inmediately before the ending
        tag of this shortcode. It is None if the shortcode is a
        simple one. This index is considered within the text empty of
        shortcodes (once they've been detected and removed).
        """

    @property
    def is_block_scoped(
        self
    ):
        """
        Check if this shortcode is a block-scoped one:
        - `[shortcode_tag]{content}[/shortcode_tag]`
        """
        return self._type == ShortcodeTagType.BLOCK
    
    @property
    def is_simple_scoped(
        self
    ):
        """
        Check if this shortcode is a simple-scoped one:
        - `[shortcode_tag]`
        """
        return self._type == ShortcodeTagType.SIMPLE

class YTAShortcode(Shortcode):
    """
    Custom shortcode class that includes the
    ability to calculate the 'start' and 
    'duration' fields from a given transcription
    of the text in which it has been found. It
    will use the words next to the shortcode and
    their transcription time moment to obtain
    this shortcode 'start' and 'duration' values.
    """

    @property
    def t_end(
        self
    ) -> Union[float, None]:
        """
        The end time moment in which the shortcode
        behaviour must end. This is calculated with the
        'start' and 'duration' parameters if set and
        valid and returned as a float number, or as None
        if not able to calculate.
        """
        if (
            PythonValidator.is_number(self.t_start) and
            PythonValidator.is_number(self.duration)
        ):
            return self.t_start + self.duration
        
        return None

    def __init__(
        self,
        tag: str,
        type: ShortcodeTagType,
        context: any,
        content: str,
        attributes: list[dict],
        index_previous_word_start: Union[int, None] = None,
        index_previous_word_end: Union[int, None] = None,
    ):
        super().__init__(
            tag = tag,
            type = type,
            context = context,
            content = content,
            attributes = attributes,
            index_previous_word_start = index_previous_word_start,
            index_previous_word_end = index_previous_word_end
        )

        self.t_start: Union[BlockShortcodeStart, SimpleShortcodeStart, float, None] = (
            float(attributes.get('start', None))
            if attributes.get('start', None) is not None else
            None
        )
        """
        The start time moment in which the shortcode behaviour
        must be applied. This needs to be calculated with a
        transcription of the text provided when obtaining this
        shortcode.
        """

        self.duration: Union[ShortcodeDuration, float, None] = (
            float(attributes.get('duration', None))
            if attributes.get('duration', None) is not None else
            None
        )
        """
        The time the shortcode behaviour must last. This needs
        to be calculated with a transcription of the text provided
        when obtaining this shortcode.
        """

    @requires_dependency('yta_audio_transcription', 'yta_shortcodes', 'yta_audio_transcription')
    def calculate_start_and_duration(
        self,
        transcription: 'AudioTranscription'
    ):
        """
        *Requires the optional library `yta_audio_transcription`*
        
        Processes this shortcode `start` and `duration`
        fields by using the 'transcription' (transcription
        object from `yta_audio` library) if needed (if
        `start` and 'duration' fields are not numbers
        manually set by the user in the shortcode when
        written).

        This will consider the current `start` and
        `duration` strategy and apply them to the words
        related to the shortcode to obtain the real `start`
        and `duration` number values.
        """
        # TODO: Here below I have simplified the code but
        # it is commented because if the value is not one
        # in the dict it will fail... but I think there is
        # no possibility of being not one in the dict
        if PythonValidator.is_instance_of(self.t_start, [SimpleShortcodeStart, BlockShortcodeStart]):
            if self.is_simple_scoped:
                # self.t_start = {
                #     ShortcodeStart.BETWEEN_WORDS: (transcription.words[self.index_previous_word_start].t_start + transcription.words[self.index_previous_word_start + 1].t_start) / 2
                # }[self.t_start]

                self.t_start = {
                    SimpleShortcodeStart.BETWEEN_WORDS: (transcription.words[self.index_previous_word_start].t_start + transcription.words[self.index_previous_word_start + 1].t_start) / 2
                }.get(self.t_start, self.t_start)

                # if self.t_start == SimpleShortcodeStart.BETWEEN_WORDS:
                #     self.t_start = (transcription.words[self.index_previous_word_start].t_start + transcription.words[self.index_previous_word_start + 1].t_start) / 2
            else:
                # self.t_start = {
                #     ShortcodeStart.START_OF_FIRST_SHORTCODE_CONTENT_WORD: transcription.words[self.index_previous_word_start + 1].t_start,
                #     ShortcodeStart.MIDDLE_OF_FIRST_SHORTCODE_CONTENT_WORD: (transcription.words[self.index_previous_word_start + 1].t_start + transcription.words[self.index_previous_word_start + 1].t_end) / 2,
                #     ShortcodeStart.END_OF_FIRST_SHORTCODE_CONTENT_WORD: transcription.words[self.index_previous_word_start + 1].t_end
                # }[self.t_start]

                self.t_start = {
                    BlockShortcodeStart.START_OF_FIRST_SHORTCODE_CONTENT_WORD: transcription.words[self.index_previous_word_start + 1].t_start,
                    BlockShortcodeStart.MIDDLE_OF_FIRST_SHORTCODE_CONTENT_WORD: (transcription.words[self.index_previous_word_start + 1].t_start + transcription.words[self.index_previous_word_start + 1].t_end) / 2,
                    BlockShortcodeStart.END_OF_FIRST_SHORTCODE_CONTENT_WORD: transcription.words[self.index_previous_word_start + 1].t_end
                }.get(self.t_start, self.t_start)

                # if self.t_start == BlockShortcodeStart.START_OF_FIRST_SHORTCODE_CONTENT_WORD:
                #     self.t_start = transcription.words[self.index_previous_word_start + 1].t_start
                # elif self.t_start == BlockShortcodeStart.MIDDLE_OF_FIRST_SHORTCODE_CONTENT_WORD:
                #     self.t_start = (transcription.words[self.index_previous_word_start + 1].t_start + transcription.words[self.index_previous_word_start + 1].t_end) / 2
                # elif self.t_start == BlockShortcodeStart.END_OF_FIRST_SHORTCODE_CONTENT_WORD:
                #     self.t_start = transcription.words[self.index_previous_word_start + 1].t_end

        if PythonValidator.is_instance_of(self.duration, ShortcodeDuration):
            if self._type == ShortcodeTagType.SIMPLE:
                # self.duration = {
                #     ShortcodeDuration.FILE_DURATION: FILE_DURATION
                # }[self.duration]

                self.duration = {
                    ShortcodeDuration.FILE_DURATION: ShortcodeDuration.FILE_DURATION.value
                }.get(self.duration, self.duration)

                # if self.duration == ShortcodeDuration.FILE_DURATION:
                #     # This duration must be set when the file is ready, so 
                #     # we use a number value out of limits to flag it
                #     # TODO: Maybe I can keep the enum and detect it later
                #     self.duration = ShortcodeDuration.FILE_DURATION.value
            else:
                # self.duration = {
                #     ShortcodeDuration.SHORTCODE_CONTENT: transcription.words[self.previous_end_word_index].t_end - transcription.words[self.previous_start_word_index + 1].t_start
                # }[self.duration]

                self.duration = {
                    ShortcodeDuration.SHORTCODE_CONTENT: transcription.words[self.index_previous_word_end].t_end - transcription.words[self.index_previous_word_end + 1].t_start
                }.get(self.duration, self.duration)

                # if self.duration == ShortcodeDuration.SHORTCODE_CONTENT:
                #     self.duration = transcription.words[self.index_previous_word_end].t_end - transcription.words[self.index_previous_word_end + 1].t_start