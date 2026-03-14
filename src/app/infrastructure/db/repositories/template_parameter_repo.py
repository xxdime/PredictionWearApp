from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.infrastructure.db.models import TemplateParameter
from app.infrastructure.db.session import get_session


class TemplateParameterRepository:
    def list_by_template(self, template_id: int) -> Iterable[TemplateParameter]:
        with get_session() as session:
            stmt = (
                select(TemplateParameter)
                .where(TemplateParameter.template_id == template_id)
                .order_by(TemplateParameter.name)
            )
            return session.scalars(stmt).all()

    def get(self, parameter_id: int) -> TemplateParameter | None:
        with get_session() as session:
            return session.get(TemplateParameter, parameter_id)

    def create(
        self,
        template_id: int,
        name: str,
        unit: str,
        critical_value: float,
        degradation_direction: str,
    ) -> TemplateParameter:
        try:
            with get_session() as session:
                param = TemplateParameter(
                    template_id=template_id,
                    name=name,
                    unit=unit,
                    critical_value=critical_value,
                    degradation_direction=degradation_direction,
                )
                session.add(param)
                session.flush()
                session.refresh(param)
                return param
        except IntegrityError as exc:
            raise ValueError(f"Параметр с именем '{name}' уже существует для данного шаблона.") from exc

    def update(
        self,
        parameter_id: int,
        name: str,
        unit: str,
        critical_value: float,
        degradation_direction: str,
    ) -> None:
        try:
            with get_session() as session:
                param = session.get(TemplateParameter, parameter_id)
                if param is None:
                    return
                param.name = name
                param.unit = unit
                param.critical_value = critical_value
                param.degradation_direction = degradation_direction
        except IntegrityError as exc:
            raise ValueError(f"Параметр с именем '{name}' уже существует для данного шаблона.") from exc

    def delete(self, parameter_id: int) -> None:
        with get_session() as session:
            param = session.get(TemplateParameter, parameter_id)
            if param is not None:
                session.delete(param)