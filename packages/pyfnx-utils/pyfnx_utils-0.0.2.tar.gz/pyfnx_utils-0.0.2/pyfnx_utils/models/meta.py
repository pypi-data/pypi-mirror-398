from dataclasses import dataclass


@dataclass
class MetaEntry:
    id: str
    producer: str
    producer_version: str
    producer_tags: list[str]
    payload: dict

    def __post_init__(self) -> None:
        if not isinstance(self.id, str):
            raise TypeError("id must be a string")
        if not isinstance(self.producer, str):
            raise TypeError("producer must be a string")
        if not isinstance(self.producer_version, str):
            raise TypeError("producer_version must be a string")
        if not isinstance(self.producer_tags, list):
            raise TypeError("producer_tags must be a list")
        if not all(isinstance(tag, str) for tag in self.producer_tags):
            raise TypeError("all producer_tags must be strings")
        if not isinstance(self.payload, dict):
            raise TypeError("payload must be a dictionary")
