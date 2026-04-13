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
                lsq_model_type="linear",
                lsq_poly_degree=1,
                gpr_kernel_type="RBF",
                gpr_alpha=1e-6,
                gpr_confidence_level=0.95,
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
        lsq_model_type: str,
        lsq_poly_degree: int,
        gpr_kernel_type: str,
        gpr_alpha: float,
        gpr_confidence_level: float,
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
                    lsq_model_type=lsq_model_type,
                    lsq_poly_degree=lsq_poly_degree,
                    gpr_kernel_type=gpr_kernel_type,
                    gpr_alpha=gpr_alpha,
                    gpr_confidence_level=gpr_confidence_level,
                )
                session.add(cfg)
                session.flush()
                session.refresh(cfg)
                return cfg

            cfg.lsq_model_type = lsq_model_type
            cfg.lsq_poly_degree = int(lsq_poly_degree)
            cfg.gpr_kernel_type = gpr_kernel_type
            cfg.gpr_alpha = float(gpr_alpha)
            cfg.gpr_confidence_level = float(gpr_confidence_level)
            session.flush()
            session.refresh(cfg)
            return cfg
