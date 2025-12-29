"""
This module contains the ShortcodeTag, which
is the shortcode text between square brackets
that will define a shortcode entity within a
text.

This ShortcodeTag is used to be registered in
the shortcode parser to allow it to detect
these kind of shortcodes.

The shortcode tag has a basic handler method
which is used by the parser to handle the
information to make it work properly, but we
have created a 'custom_handler' with which
you can modify the attributes found or do
whatever you need before storing the shortcode
entity foundin the shortcodes array.

Remember that this shortcode tag will be, once
it's been detected in the text' turned into a
shortcode entity that will be handler later
by the software to do something else. You can
modify the way this entity is stored with this
'custom_handler' method. Creat your own
ShortcodeTag class, inherit from this basic
one and make it yours.
"""
from yta_shortcodes.tag_type import ShortcodeTagType
from yta_shortcodes.shortcode import YTAShortcode
from typing import Union
from abc import abstractmethod


class ShortcodeTag:
    """
    Class that represent a shortcode tag, which
    can be a simple or a block scoped shortcode
    including only one tag [tag_name] or one
    start and end tag [tag_name] ... [/tag_name].

    This shortcode tag is passed to the shortcode
    parser to register it and look for that tag
    in the text you provide to the parser. This
    will handle all the shortcodes with that
    'tag_name', not only one.
    """

    name: str
    """
    The tag name, which is the word that comes
    inmediately after the opening square bracket
    and represent the shortcode.
    """
    _type: ShortcodeTagType
    """
    The type of shortcode tag that can be simple
    or block scoped.
    """

    @property
    def is_block_scoped(
        self
    ) -> bool:
        """
        Check if this shortcode is a block-scoped one
        [shortcode_tag] ... [/shortcode_tag].
        """
        return self._type == ShortcodeTagType.BLOCK
    
    @property
    def is_simple_scoped(
        self
    ) -> bool:
        """
        Check if this shortcode is a simple-scoped one
        [shortcode_tag].
        """
        return self._type == ShortcodeTagType.SIMPLE

    def __init__(
        self,
        name: str,
        type: ShortcodeTagType
    ):
        type = ShortcodeTagType.to_enum(type)

        self.name = name
        self._type = type

    def str(
        self,
        content: Union[str, None],
        pargs,
        kwargs,
    ) -> str:
        """
        Get the output string according to its type,
        that is the representation of this shortcode
        as it was detected, as a string, including
        parameters and everything.
        """
        content = (
            ""
            if content is None else
            content
        )

        attributes = {}
        attributes.update({parg: None for parg in pargs})
        attributes.update(kwargs)

        # TODO: Maybe we can externalize this code to a
        # utils or something to keep it reusable
        tag = f'[{self.name}'
        for key, value in attributes:
            tag += (
                f' {key}'
                if value is None else
                f' {key}={str(value)}'
            )
        tag += (
            f']{content}[/{self.name}]'
            if self.is_block_scoped else
            f']'
        )

        return tag

    def str_simplified(
        self,
        content: Union[str, None]
    ) -> str:
        """
        Get the output string, but simplified, according
        to its type, that is the representation of this
        shortcode as it was detected, as a string, but
        including not the parameters, only the tags and
        the 'content' (if block-scoped and provided).

        This will transform:
        - `[example attr="value"]` to `[example]`
        - `[tag attr="3"]text[/tag]` to `[tag]text[/tag]`
        """
        content = (
            ""
            if content is None else
            content
        )

        return (
            f'[{self.name}]'
            if self.is_simple_scoped else
            f'[{self.name}]{content}[/{self.name}]'
        )

    def handler(
        self,
        shortcodes,
        pargs,
        kwargs,
        context,
        **extra_args
        #content: Union[str, None] = None
    ):
        """
        The function that handles the shortcode, fills the provided
        'shortcodes' list with a new shortcode object and all the
        required attributes and values.

        :param shortcodes: A list with the shortcodes that have been
        found previously, so we are able to store the new one.
        :param pargs: The positional arguments found in the shortcode
        tag.
        :param kwargs: The key and value arguments found in the
        shortcode tag.
        :param context: The context (I don't know what this is for...)
        :param **extra_args: Extra arguments we want to pass to this
        function.
        """
        # Fill the attributes
        attributes = {}

        for parg in pargs:
            attributes[parg] = None

        if kwargs:
            for kwarg in kwargs:
                attributes[kwarg] = kwargs[kwarg]

        # We handle the 'content' like this to avoid
        # being an strict parameter
        content = extra_args.get('content', None)

        # Here you can customize it a little bit
        # before storing the final Shortcode entity
        self.custom_handler(shortcodes, attributes, context, content)

        shortcodes.append(YTAShortcode(
            tag = self.name,
            type = self._type,
            context = context,
            content = content,
            attributes = attributes
        ))

        # We will remove all the attributes but keep 
        # the shortcode tags and the content (if
        # existing) to be able to detect it again in
        # the text so we can extract the position for
        # extra purposes
        return self.str_simplified(content)
    
    @abstractmethod
    def custom_handler(
        self,
        shortcodes,
        attributes,
        context,
        content: Union[None, str] = None
    ):
        """
        This part of the code will be called just
        before adding the shortcode found to the
        list so you can do whatever you need with
        the 'attributes' parameter that has been
        build with the received 'pargs' and 'kwargs'
        or the 'context' or 'content'.

        You can replace this method in the subclass
        with anything else you need to do, or can
        keep it as it is to have a basic shortcode.
        """
        pass