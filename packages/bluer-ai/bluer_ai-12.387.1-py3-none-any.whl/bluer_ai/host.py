from typing import List

from bluer_options.host import signature as bluer_options_signature
from bluer_objects import fullname as bluer_objects_fullname

from bluer_ai import fullname


def signature() -> List[str]:
    return [
        fullname(),
        bluer_objects_fullname(),
    ] + bluer_options_signature()
