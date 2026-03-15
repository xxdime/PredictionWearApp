from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    parameters: Mapped[list[TemplateParameter]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )
    parts: Mapped[list[Part]] = relationship(back_populates="template")


class TemplateParameter(Base):
    __tablename__ = "template_parameters"
    __table_args__ = (UniqueConstraint("template_id", "name", name="uq_template_parameter_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("templates.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), default="mm", nullable=False)
    critical_value: Mapped[float] = mapped_column(Float, nullable=False)

    degradation_direction: Mapped[str] = mapped_column(
        String(32), default="decrease_to_critical", nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    template: Mapped[Template] = relationship(back_populates="parameters")
    measurements: Mapped[list[Measurement]] = relationship(back_populates="parameter")


class Part(Base):
    __tablename__ = "parts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("templates.id", ondelete="RESTRICT"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    serial_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    installation_place: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    template: Mapped[Template] = relationship(back_populates="parts")
    measurements: Mapped[list[Measurement]] = relationship(
        back_populates="part", cascade="all, delete-orphan"
    )


class Measurement(Base):
    __tablename__ = "measurements"
    __table_args__ = (
        UniqueConstraint("part_id", "parameter_id", "operating_hours", name="uq_measurement_point"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    part_id: Mapped[int] = mapped_column(ForeignKey("parts.id", ondelete="CASCADE"), nullable=False)
    parameter_id: Mapped[int] = mapped_column(
        ForeignKey("template_parameters.id", ondelete="RESTRICT"), nullable=False
    )

    operating_hours: Mapped[float] = mapped_column(Float, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    measured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    part: Mapped[Part] = relationship(back_populates="measurements")
    parameter: Mapped[TemplateParameter] = relationship(back_populates="measurements")


class ForecastConfig(Base):
    __tablename__ = "forecast_configs"
    __table_args__ = (
        UniqueConstraint(
            "template_id", "parameter_id", name="uq_forecast_config_template_parameter"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("templates.id", ondelete="CASCADE"), nullable=False
    )
    parameter_id: Mapped[int] = mapped_column(
        ForeignKey("template_parameters.id", ondelete="CASCADE"), nullable=False
    )

    lsq_model_type: Mapped[str] = mapped_column(String(32), default="linear", nullable=False)
    lsq_poly_degree: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    gpr_kernel_type: Mapped[str] = mapped_column(String(64), default="RBF", nullable=False)
    gpr_alpha: Mapped[float] = mapped_column(Float, default=1e-6, nullable=False)
    gpr_confidence_level: Mapped[float] = mapped_column(Float, default=0.95, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
