import json


class CoreEnrichmentItem:
    """A wrapper class for the EnrichmentItem object
    """

    def __init__(self, id: str) -> None:  # pylint: disable=redefined-builtin
        self.id = id

    def __str__(self) -> str:
        return f"{self.__class__.__name__} {json.dumps(self.__dict__,indent=4)}"
