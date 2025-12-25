from __future__ import annotations

from pathlib import Path

from doogat.core.domain.entities.zettel.zettel import Zettel
from doogat.core.domain.interfaces.zettel_repository import ZettelRepository
from doogat.core.infrastructure.persistence.file_parsers.zettel_file_parser import (
    ZettelFileParser,
)


class MarkdownZettelRepository(ZettelRepository):
    def find_by_location(
        self: MarkdownZettelRepository,
        repository_location: str,
    ) -> Zettel:
        zettel_data = ZettelFileParser.from_file(Path(repository_location))
        return Zettel(zettel_data)

    def save(self: ZettelRepository, zettel: Zettel) -> None:
        raise NotImplementedError

    def find_by_id(self: ZettelRepository, zettel_id: str) -> Zettel:
        raise NotImplementedError

    def find_all(self: ZettelRepository) -> list[Zettel]:
        raise NotImplementedError
