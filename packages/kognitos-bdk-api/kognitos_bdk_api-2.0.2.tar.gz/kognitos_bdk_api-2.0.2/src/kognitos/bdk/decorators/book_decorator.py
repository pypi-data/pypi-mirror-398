import inspect
from importlib.resources import files
from typing import List, Optional, Type, get_origin

from kognitos.bdk.api import NounPhrase

from ..docstring import DocstringParser
from ..errors import SignatureError
from ..reflection import ConceptDescriptor
from ..reflection.factory import BookConfigFactory, BookFactory
from ..reflection.factory.trigger_resolver import check_and_resolve_trigger
from ..reflection.factory.types import (ConceptTypeFactory,
                                        check_and_resolve_async_procedure,
                                        is_none)
from .rules import (AsyncFinalResolverOutputsRule, AsyncProcedureOutputsRule,
                    AsyncResolverInputsRule,
                    AsyncResolverNoUnresolvedPromisesRule,
                    IntermediateAsyncResolverOutputsRule,
                    TriggerConfigurationDescriptionRule,
                    TriggerEventExtractionRule, TriggerResolverExistsRule,
                    TriggerResolverInputsRule)

DEFAULT_ICON = """
<?xml version="1.0" encoding="UTF-8"?>
<svg id="Layer_1" data-name="Layer 1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 634.58 800">
  <defs>
    <style>
      .cls-1 {
        fill: #000;
        stroke-width: 0px;
      }
    </style>
  </defs>
  <path class="cls-1" d="M634.42,20.18c0-11.16-9.03-20.18-20.18-20.18H124.55C55.79,0,0,55.96,0,124.55v550.89c0,68.76,55.96,124.55,124.55,124.55h489.85c11.16,0,20.18-9.03,20.18-20.18V229.09c0-11.16-9.03-20.18-20.18-20.18H124.55c-46.44,0-84.35-37.91-84.35-84.35S78.11,40.21,124.55,40.21h489.85c10.99,0,20.02-9.03,20.02-20.02ZM124.55,249.11h469.66v510.69H124.55c-46.44,0-84.35-37.91-84.35-84.35V216.12c22.15,20.51,51.86,32.98,84.35,32.98Z"/>
  <path class="cls-1" d="M131.45,106.34c-11.16,0-20.18,9.03-20.18,20.18s9.03,20.18,20.18,20.18h459.65c11.16,0,20.18-9.03,20.18-20.18s-9.03-20.18-20.18-20.18H131.45Z"/>
  <path class="cls-1" d="M485.11,443.88c-3.66-10.13-8.28-19.93-13.75-29.24-5.47-9.32-11.92-18.07-19.05-26.23-.86-1.05-1.79-2.02-2.72-3.02l-2.77-2.98-1.39-1.48-1.45-1.42-2.92-2.84-1.46-1.41c-.49-.47-1.01-.9-1.52-1.35l-3.07-2.68c-2-1.83-4.17-3.48-6.29-5.17-8.55-6.7-17.7-12.64-27.33-17.7-9.64-5.06-19.78-9.17-30.18-12.37-2.62-.74-5.23-1.52-7.86-2.21l-7.96-1.85-8.04-1.46-1-.18-1.01-.13-2.02-.26-4.06-.52c-21.67-2.3-43.76-.86-64.83,4.65-21.07,5.51-41.08,14.95-58.6,27.72-8.77,6.37-16.99,13.49-24.42,21.35-7.45,7.83-14.12,16.38-19.98,25.43-11.64,18.12-19.94,38.33-24,59.28.02-.08.04-.17.07-.25,6.99-26.06,24.17-48.38,47.7-61.69,16.15-9.14,34.81-14.35,54.71-14.35,32.36,0,62.11,18.46,83.01,44.88,4.78,6.05,8.95,12.55,12.67,19.29,43.8,79.08,88.97,89.26,104,90.34,3.02.36,6.38.41,10.14.12,19.47-1.52,35.37-18.24,35.38-40.73.02.54.06,1.08.08,1.62.68-21.34-2.76-42.89-10.04-63.15ZM460.55,492.91c-.28,0-.55.02-.82.02-29.07,0-73.36-75.86-101.33-87.88,25.07,8.39,47.03,23.56,63.68,43.32-30-45.74-81.84-75.97-140.77-75.97-29.09,0-51.67,4.87-75.53,17.83,28.57-28.7,68.18-46.47,111.95-46.47,17.69,0,34.7,2.91,50.58,8.25,54.53,18.38,94.03,65.85,103.39,122.45,1.22,7.44.39,18.45-11.15,18.45Z"/>
  <path class="cls-1" d="M428.92,600.32c-20.72,4.13-42.52,2.79-63.08-4.24l-8.45-2.89c-21.74-7.43-39.18-22.4-55.23-38.8-28.23-28.87-53.82-67.27-71.77-89.74-8.65-10.82-21.51-17.65-35.38-18.08-.52-.02-1.04-.02-1.57-.02-8.39,0-16.3,2.11-23.2,5.83-13.35,7.19-22.24,20.48-24.41,35.39l-.6,4.14c-1.32,11.87-1.33,23.87.28,35.7,11.66,85.65,85.33,151.67,174.48,151.67,78.35,0,144.74-50.99,167.6-121.49l4.57-15.9c-8.45,29.64-32.86,52.36-63.22,58.41ZM384.72,643c-1.04.39-2.08.78-3.12,1.15-6.21,2.24-12.26,4.16-18.15,5.74-.98.26-1.96.52-2.94.77-10.71,2.71-20.89,4.38-30.56,5.15-.88.07-1.75.13-2.62.19-2.61.16-5.19.26-7.72.3-1.69.02-3.37.02-5.02-.01-5.8-.11-11.4-.54-16.79-1.26-1.54-.21-3.07-.44-4.58-.69s-3.01-.53-4.48-.82c-5.17-1.04-10.14-2.34-14.91-3.89-4.09-1.31-8.03-2.79-11.84-4.42-.63-.27-1.26-.54-1.89-.82-1.25-.56-2.49-1.13-3.71-1.71-3.06-1.46-6.01-3.02-8.87-4.65-1.14-.65-2.27-1.31-3.39-1.98-.56-.34-1.11-.68-1.66-1.02-1.1-.68-2.18-1.38-3.25-2.08-1.6-1.06-3.17-2.13-4.7-3.24-1.02-.73-2.03-1.47-3.03-2.21-.5-.37-.99-.75-1.47-1.12-.98-.75-1.94-1.51-2.89-2.28-6.16-4.99-11.68-10.22-16.61-15.44-3.79-4.02-7.21-8.03-10.3-11.92-.31-.39-.61-.78-.91-1.16-1.2-1.54-2.35-3.08-3.45-4.57-.55-.75-1.08-1.49-1.6-2.22-2.33-3.3-4.4-6.43-6.19-9.32-.2-.32-.39-.64-.59-.95-2.31-3.77-4.15-7.08-5.52-9.73-.48-.92-.96-1.88-1.44-2.86-.24-.49-.48-.98-.72-1.48-1.18-2.5-2.31-5.15-3.25-7.86-.74-2.17-1.36-4.4-1.79-6.63-.21-1.12-.37-2.24-.48-3.37-.1-1.12-.15-2.24-.13-3.36.11-5.81,1.48-11.04,3.78-15.56.42-.82.86-1.62,1.34-2.39s.98-1.53,1.51-2.25c.53-.73,1.09-1.43,1.67-2.11.29-.34.59-.67.89-1,1.51-1.63,3.19-3.12,4.96-4.42.32-.24.65-.47.98-.69,13.64-9.34,32.21-6.8,43.3,5.44,12.9,14.24,28.02,34.23,60.45,59.44,1.02.79,2.1,1.48,3.16,2.19,5.27,3.59,10.54,6.81,15.76,9.72,1.04.58,2.08,1.14,3.13,1.7,11.44,6.09,22.58,10.64,32.87,14.03,1.87.62,3.71,1.19,5.52,1.74,1.81.54,3.59,1.05,5.33,1.52s3.45.91,5.12,1.32c22.52,5.53,37.98,5.4,37.98,5.39-8.85,3.06-17.63,5.09-26.3,6.27-2.16.29-4.33.54-6.48.73s-4.3.33-6.42.42c-12.79.55-25.24-.62-37.12-2.99-5.94-1.18-11.73-2.65-17.35-4.36-1.25-.38-2.48-.77-3.72-1.17-4.31-1.4-8.52-2.93-12.59-4.55-.58-.23-1.16-.46-1.74-.7-3.47-1.41-6.84-2.9-10.12-4.42-.54-.25-1.09-.51-1.63-.77-5.94-2.82-11.55-5.79-16.77-8.78-.47-.27-.94-.54-1.41-.81-25.25-14.66-40.97-29.45-40.97-29.45,9.85,11.15,20.13,20.58,30.56,28.54.65.5,1.3.99,1.96,1.47,1.96,1.46,3.93,2.87,5.9,4.23.66.45,1.31.9,1.97,1.34,4.6,3.1,9.22,5.92,13.82,8.51s9.22,4.93,13.78,7.04c1.3.6,2.61,1.19,3.92,1.76,13.67,5.98,27.04,10.01,39.52,12.67,1.19.25,2.36.49,3.54.72s2.33.45,3.49.65c1.15.21,2.29.4,3.44.58.57.09,1.13.18,1.69.27,2.25.35,4.46.65,6.63.91.54.07,1.08.13,1.61.19,5.36.61,10.45.99,15.19,1.2l1.41.06c3.28.12,6.37.16,9.28.15.41,0,.83-.01,1.23-.01,15.89-.2,25.72-2.15,25.73-2.15-6.55,3.07-12.97,5.78-19.23,8.13Z"/>
</svg>"""


def _get_blueprints(cls) -> List[type]:
    bases = cls.__bases__
    return list(filter(lambda b: b.__dict__.get("__is_blueprint", False), bases))


def book(*args, **kwargs):  # pylint: disable=invalid-name
    """
    kwargs:
        id: Optional[str] The book identifier
        icon: Optional[str] Path to the book icon
        name: Optional[str] The book name. If not provided, the name will be inferred from the class name.
        noun_phrase: Optional[str] The book noun phrase
        tags: Optional[List[str]] The book tags
    """

    cls: Optional[Type]
    identifier: Optional[str]
    icon: Optional[str]
    name: Optional[str]
    noun_phrase: Optional[str]
    tags: Optional[List[str]]

    if len(args) == 1 and not kwargs and isinstance(args[0], type):
        cls = args[0]
        identifier = None
        icon = None
        name = None
        noun_phrase = None
        tags = None
    else:
        cls = None
        identifier = kwargs.get("id", None)
        icon = kwargs.get("icon", None)
        name = kwargs.get("name", None)
        noun_phrase = kwargs.get("noun_phrase", None)
        tags = kwargs.get("tags", [])

    def decorator(cls):
        if not inspect.isclass(cls):
            raise TypeError("The book decorator can only be applied to classes.")

        if not cls.__doc__:
            raise ValueError("missing docstring")

        # add config elements
        # we do it here since the @property need to run first and might collide
        configuration = []
        property_names = [field for field in cls.__dict__ if isinstance(getattr(cls, field), property) and hasattr(getattr(cls, field).fget, "__noun_phrase__")]
        for property_name in property_names:
            prop = getattr(cls, property_name)
            fget = getattr(prop, "fget", None)

            if fget:
                noun_phrases = getattr(fget, "__noun_phrase__", None)
                default_value = getattr(fget, "__default_value__", None)
                docstring_text = fget.__doc__
                return_annotation = inspect.signature(fget).return_annotation

                parsed_property_docstring = DocstringParser.parse(docstring_text) if docstring_text else None

                if noun_phrases:
                    configuration.append(
                        BookConfigFactory.create(
                            property_name=property_name,
                            noun_phrases=noun_phrases,
                            return_annotation=return_annotation,
                            docstring=parsed_property_docstring,
                            default_value=default_value,
                        )
                    )

        parsed_docstring = DocstringParser.parse(cls.__doc__)

        author = parsed_docstring.author

        short_description = parsed_docstring.short_description
        long_description = parsed_docstring.long_description

        icon_path = None
        if icon is not None:
            module = cls.__module__
            package = module.rsplit(".", 1)[0]
            icon_path = files(package).joinpath(icon)
            with icon_path.open("rb") as file:
                icon_data = file.read()
            icon_path = str(icon_path)
        else:
            icon_data = bytes(DEFAULT_ICON, encoding="utf-8")

        blueprints = _get_blueprints(cls)

        if blueprints:
            cls.__blueprints__ = blueprints

        if not hasattr(cls.__dict__, "__book__"):
            cls.__book__ = BookFactory.create(
                t=cls,
                identifier=identifier,
                name=name,
                noun_phrase_str=noun_phrase,
                author=author,
                short_description=short_description,
                long_description=long_description,
                icon=icon_data,
                icon_path=icon_path,
                configuration=configuration,
                tags=tags,
            )

        # Check async resolvers and correct descriptor return type
        for _, member in inspect.getmembers(cls, predicate=inspect.isfunction):
            if not hasattr(member, "__procedure__") or not (member.__procedure__.is_async or getattr(member, "__is_async__", False)):
                continue

            rules = [
                AsyncProcedureOutputsRule(),
                IntermediateAsyncResolverOutputsRule(),
                AsyncResolverInputsRule(),
                AsyncResolverNoUnresolvedPromisesRule(),
                AsyncFinalResolverOutputsRule(),
            ]
            output_annotation, questions = check_and_resolve_async_procedure(cls, member, rules)
            questions = questions.union(member.__procedure__.questions)
            member.__procedure__.questions = list(questions)

            if get_origin(output_annotation) is tuple:
                output_types = [ConceptTypeFactory.from_type(t) for t in output_annotation.__args__ if not is_none(t)]
            elif not is_none(output_annotation):
                output_types = [ConceptTypeFactory.from_type(output_annotation)]
            else:
                output_types = []

            member_docstring = DocstringParser.parse(member.__doc__ or "")
            if not member.__procedure__.outputs and len(output_types) == 1:
                description = member_docstring.output_description_by_noun_phrases([NounPhrase("answer")])
                member.__procedure__.outputs = [ConceptDescriptor(noun_phrases=[NounPhrase("answer")], type=output_types[0], description=description, default_value=None)]
            else:
                if len(output_types) != len(member.__procedure__.outputs):
                    raise SignatureError("The number of elements in the return tuple do not match the number of outputs of the procedure")

                for i, output_type in enumerate(output_types):
                    member.__procedure__.outputs[i]._type = output_type

        # Resolve trigger resolver functions and extract event information using rules
        for _, member in inspect.getmembers(cls, predicate=inspect.isfunction):
            trigger = getattr(member, "__trigger__", None)
            if not trigger:
                continue

            # Apply trigger validation and resolution rules
            rules = [
                TriggerResolverExistsRule(),
                TriggerResolverInputsRule(),
                TriggerConfigurationDescriptionRule(),
                TriggerEventExtractionRule(),
            ]

            event = check_and_resolve_trigger(cls, member, rules)

            # Update the trigger descriptor with the resolved event
            trigger.event = event

        return cls

    if cls is None:
        return decorator

    return decorator(cls)
