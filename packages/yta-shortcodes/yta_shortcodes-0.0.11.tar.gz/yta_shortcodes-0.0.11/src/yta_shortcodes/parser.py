"""
Here it is the shortcode parser, the code that
registers the different shortcode tags to find
in a given text and the handler methods to
extract the attributes of those shortcodes and
anything else that has been programmed to do
with them.

The parser registers the shortcode tags you
provide, detects those tags, extract the
information of them, minimizes the shortcodes,
gets the positions in which they are placed and,
finally, remove them to clean and leave the text
only with no shortcodes.

Any unregistered shortcode is unaccepted.
"""
from yta_shortcodes.tag import ShortcodeTag
from yta_shortcodes.shortcode import YTAShortcode
from yta_constants.regex import GeneralRegularExpression
from yta_text.handler import TextHandler
from yta_validation import PythonValidator
from yta_validation.parameter import ParameterValidator
from shortcodes import Parser


class ShortcodeParser:
    """
    This class detects in a text the shortcodes
    you register on it, being able to classify
    the content according to the type and what
    is defined on each shortcode you register.

    _The developer must register manually the
    shortcode parser method for each shortcode_.
    """

    def __init__(
        self,
        shortcode_tags: list[ShortcodeTag]
    ):
        """
        The 'shortcode_tags' parameters is the list of
        shortcodes we want to detect.
        """
        if any(
            not PythonValidator.is_subclass_of(shortcode_tag, ShortcodeTag)
            for shortcode_tag in shortcode_tags
        ):
            raise Exception('At least one of the "shortcodes" provided is not a subclass of ShortcodeTag.')

        self._parser: Parser = Parser(start = '[', end = ']', inherit_globals = False)
        """
        *For internal use only*

        The shortcode parser.
        """
        # TODO: This can be a subclass of YTAShortcode
        # or Shortcode...
        self.shortcodes: list[YTAShortcode] = []
        """
        The list of shortcodes that have been found
        in the last analyzed text.
        """

        # We create a function to register individually each
        # shortcode and it's handler so we don't get the
        # handlers overrided
        def register_shortcode_handler(
            self,
            shortcode_tag
        ):
            """
            Register the shortcode handler specifically and
            individually for each shortcode.
            """
            def handler(
                pargs,
                kwargs,
                context,
                content = None
            ):
                return shortcode_tag.handler(
                    self.shortcodes,
                    pargs,
                    kwargs,
                    context,
                    content = content if shortcode_tag.is_block_scoped else None
                )
            
            # Registra el handler individual para ese shortcode
            self._parser.register(
                handler, 
                shortcode_tag.name,
                (
                    f'/{shortcode_tag.name}'
                    if shortcode_tag.is_block_scoped else
                    None
                )
            )

        for shortcode_tag in shortcode_tags:
            register_shortcode_handler(self, shortcode_tag)

    def parse(
        self,
        text: str
    ) -> str:
        """
        Parse the provided 'text' according to the 
        shortcodes that have been registered.

        This method will store internally the
        shortcode tags that have been detected and
        will return the text without all those
        shortcodes that were inside, and sanitized,
        which means that all the double blank 
        spaces, unseparated periods or parenthesis,
        etc. have been fixed.
        """
        ParameterValidator.validate_mandatory_string('text', text, do_accept_empty = True)
        
        def sanitize_text(
            text: str
        ):
            """
            Remove anything unwanted from the given 'text'.
            """
            text = TextHandler.add_missing_spaces_before_and_after_square_brackets(text)
            text = TextHandler.add_missing_spaces_before_and_after_parenthesis(text)
            text = TextHandler.fix_separated_square_brackets(text)
            text = TextHandler.fix_separated_parenthesis(text)
            text = TextHandler.fix_unseparated_periods(text)
            text = TextHandler.fix_ellipsis(text)
            text = TextHandler.fix_excesive_blank_spaces(text)

            return text
        
        self.text = text
        self.text_sanitized = sanitize_text(text)
        self.text_sanitized_with_simplified_shortcodes = ''
        self.text_sanitized_without_shortcodes = ''
        self.shortcodes = []

        """
        This process involves 2 main steps:
        1. Creating shortcode instances from shortcode
        tags found in text and simplified.
        2. Obtain shortcode positions from simplified
        shortcode tags and clean the text.

        First, we parse the text with the shortcode tags
        we have registered on this parser. When they are
        detected, each shortcode tag handler (that has 
        been registered in the parser to handle its
        corresponding shortcode tag) extracts the 
        attributes (and the content if existing) and 
        appends a new shortcode to the list of shortcodes
        found, with all those attributes. In this step,
        the text is simplified so the shortcode tags are
        reduced to only their names. For example,
        [tag attribute=value] turns into [tag].

        Once we've detected the shortcodes, added them
        and simplified the shortcode tags, we iterate
        over all the shortcodes found to obtain its 
        corresponding simplified shortcode tag in the 
        text, so we can get the previous words positions.
        We update the shortcodes found with those 
        positions and we clear the shortcode tags from
        the text.
        """

        # Parse shortcodes, extract the information
        # and fulfill the 'shortcodes' attribute
        self.text_sanitized_with_simplified_shortcodes = self._parser.parse(self.text_sanitized, context = None)

        """
        After this parse we have 'self.shortcodes' fulfilled
        because the parser has the tags registered, and those
        tags are appending the shortcodes found on the
        shortcodes list that is passed as parameter for each
        handling method
        """
        
        words = self.text_sanitized_with_simplified_shortcodes.split(' ')
        # Here we obtain some blank words that we
        # must remove
        words = list(filter(lambda x: x != '', words))

        # Now lets look for the simplified shortcode
        # positions
        index = 0
        while index < len(words):
            word = words[index]
            if GeneralRegularExpression.SHORTCODE.parse(word):
                # TODO: Improve this to avoid the ones completed
                for shortcode in self.shortcodes:
                    if '/' in word:
                        # End shortcode
                        if shortcode.tag == word.replace('[', '').replace(']', '').replace('/', '') and shortcode.index_previous_word_end is None:
                            # Is that shortcode
                            shortcode.index_previous_word_end = index - 1
                            break
                    else:
                        # Start shortcode
                        if shortcode.tag == word.replace('[', '').replace(']', '') and shortcode.index_previous_word_start is None:
                            # Is that shortcode
                            shortcode.index_previous_word_start = index - 1
                            break

                del(words[index])
            else:
                index += 1

        self.text_sanitized_without_shortcodes = ' '.join(words)

        return self.text_sanitized_without_shortcodes