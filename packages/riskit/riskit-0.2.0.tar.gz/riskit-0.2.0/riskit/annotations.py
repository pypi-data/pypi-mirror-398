import inspect
from typing import Callable, cast
from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedAnnotation[*MetadataT]:
    metadata: tuple[*MetadataT]


def return_annotation_of[*MetadataT](
    function: Callable, *, type: type[tuple[*MetadataT]]
) -> ExtractedAnnotation[*MetadataT]:
    signature = inspect.signature(function)
    annotation = signature.return_annotation

    try:
        metadata = annotation.__value__.__metadata__
        return ExtractedAnnotation(metadata=cast(tuple[*MetadataT], metadata))
    except AttributeError as e:
        # TODO: Test me!
        raise TypeError(
            f"Could not extract annotation metadata from {annotation} of function {function}. "
            "Ensure the return type is properly annotated."
        ) from e
