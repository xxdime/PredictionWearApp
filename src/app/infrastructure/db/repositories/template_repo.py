from __future__ import annotations

from typing import Iterable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.infrastructure.db.models import Template
from app.infrastructure.db.session import get_session


class TemplateRepository:
    def list(self) -> Iterable[Template]:
        with get_session() as session:
            return session.scalars(select(Template).order_by(Template.name)).all()

    def get(self, template_id: int) -> Template | None:
        with get_session() as session:
            return session.get(Template, template_id)

    def create(self, name: str, description: str | None = None) -> Template:
        try:
            with get_session() as session:
                template = Template(name=name, description=description)
                session.add(template)
                session.flush()
                session.refresh(template)
                return template
        except IntegrityError as exc:
            raise ValueError(f"Шаблон с именем '{name}' уже существует.") from exc

    def update(self, template_id: int, name: str, description: str | None) -> None:
        try:
            with get_session() as session:
                template = session.get(Template, template_id)
                if template is None:
                    return
                template.name = name
                template.description = description
                session.flush()
        except IntegrityError as exc:
            raise ValueError(f"Шаблон с именем '{name}' уже существует.") from exc

    def delete(self, template_id: int) -> None:
        try:
            with get_session() as session:
                template = session.get(Template, template_id)
                if template is not None:
                    session.delete(template)
        except IntegrityError as exc:
            raise ValueError(f"Вы не можете удалить шаблон пока существуют детали этого шаблона.") from exc