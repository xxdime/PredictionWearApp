from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.infrastructure.db.models import Part
from app.infrastructure.db.session import get_session


class PartRepository:
    def list(self) -> Iterable[Part]:
        with get_session() as session:
            stmt = select(Part).order_by(Part.created_at.desc())
            return session.scalars(stmt).all()

    def get(self, part_id: int) -> Part | None:
        with get_session() as session:
            return session.get(Part, part_id)

    def create(
        self,
        template_id: int,
        name: str,
        serial_number: str | None = None,
        installation_place: str | None = None,
        notes: str | None = None,
    ) -> Part:
        try:
            with get_session() as session:
                part = Part(
                    template_id=template_id,
                    name=name,
                    serial_number=serial_number,
                    installation_place=installation_place,
                    notes=notes,
                )
                session.add(part)
                session.flush()
                session.refresh(part)
                return part
        except IntegrityError as exc:
            raise ValueError("Не удалось создать деталь (проверьте уникальность/ссылки).") from exc

    def update(
        self,
        part_id: int,
        template_id: int,
        name: str,
        serial_number: str | None = None,
        installation_place: str | None = None,
        notes: str | None = None,
    ) -> None:
        with get_session() as session:
            part = session.get(Part, part_id)
            if part is None:
                return
            part.template_id = template_id
            part.name = name
            part.serial_number = serial_number
            part.installation_place = installation_place
            part.notes = notes
            session.flush()

    def delete(self, part_id: int) -> None:
        with get_session() as session:
            part = session.get(Part, part_id)
            if part is not None:
                session.delete(part)
