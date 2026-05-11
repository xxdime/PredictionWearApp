from __future__ import annotations

from sqlalchemy import select

from app.infrastructure.db.models import ForecastConfig
from app.infrastructure.db.session import get_session


class ForecastConfigRepository:
    def get_for(self, template_id: int, parameter_id: int) -> ForecastConfig | None:
        with get_session() as session:
            stmt = select(ForecastConfig).where(
                ForecastConfig.template_id == template_id,
                ForecastConfig.parameter_id == parameter_id,
            )
            return session.scalars(stmt).first()

    def get_or_create_default(self, template_id: int, parameter_id: int) -> ForecastConfig:
        with get_session() as session:
            stmt = select(ForecastConfig).where(
                ForecastConfig.template_id == template_id,
                ForecastConfig.parameter_id == parameter_id,
            )
            cfg = session.scalars(stmt).first()
            if cfg is not None:
                return cfg

            cfg = ForecastConfig(
                template_id=template_id,
                parameter_id=parameter_id,
                lsq_model_formula="",
                lsq_param_bounds_json="{}",
                confidence_k=2.0,
            )
            session.add(cfg)
            session.flush()
            session.refresh(cfg)
            return cfg

    def upsert(
        self,
        template_id: int,
        parameter_id: int,
        *,
        lsq_model_formula: str,
        lsq_param_bounds_json: str,
        confidence_k: float,
    ) -> ForecastConfig:
        with get_session() as session:
            stmt = select(ForecastConfig).where(
                ForecastConfig.template_id == template_id,
                ForecastConfig.parameter_id == parameter_id,
            )
            cfg = session.scalars(stmt).first()
            if cfg is None:
                cfg = ForecastConfig(
                    template_id=template_id,
                    parameter_id=parameter_id,
                    lsq_model_formula=lsq_model_formula,
                    lsq_param_bounds_json=lsq_param_bounds_json,
                    confidence_k=confidence_k,
                )
                session.add(cfg)
                session.flush()
                session.refresh(cfg)
                return cfg

            cfg.lsq_model_formula = lsq_model_formula
            cfg.lsq_param_bounds_json = lsq_param_bounds_json
            cfg.confidence_k = float(confidence_k)
            session.flush()
            session.refresh(cfg)
            return cfg
