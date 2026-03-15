from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.infrastructure.db.models import Measurement
from app.infrastructure.db.session import get_session


class MeasurementRepository:
    def list_by_part_and_parameter(self, part_id: int, parameter_id: int) -> Iterable[Measurement]:
        with get_session() as session:
            stmt = (
                select(Measurement)
                .where(
                    Measurement.part_id == part_id,
                    Measurement.parameter_id == parameter_id,
                )
                .order_by(Measurement.operating_hours.asc())
            )
            return session.scalars(stmt).all()

    def create(
        self, part_id: int, parameter_id: int, operating_hours: float, value: float
    ) -> Measurement:
        try:
            with get_session() as session:
                m = Measurement(
                    part_id=part_id,
                    parameter_id=parameter_id,
                    operating_hours=operating_hours,
                    value=value,
                )
                session.add(m)
                session.flush()
                session.refresh(m)
                return m
        except IntegrityError as exc:
            raise ValueError(
                "Измерение с такими часами наработки уже существует для этой детали и параметра."
            ) from exc

    def update(self, measurement_id: int, operating_hours: float, value: float) -> None:
        try:
            with get_session() as session:
                m = session.get(Measurement, measurement_id)
                if m is None:
                    return
                m.operating_hours = operating_hours
                m.value = value
                session.flush()
        except IntegrityError as exc:
            raise ValueError("Нельзя сохранить: точка с такими часами уже существует.") from exc

    def delete(self, measurement_id: int) -> None:
        with get_session() as session:
            m = session.get(Measurement, measurement_id)
            if m is not None:
                session.delete(m)
