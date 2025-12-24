"""Emission estimation pipeline scaffolding."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class GridIntensityProvider(Protocol):
    """Protocol for fetching regional grid intensity data."""

    async def grams_co2_per_kwh(self, region: str) -> float: ...


class EnergyModel(Protocol):
    """Protocol for converting runtime metrics to energy."""

    async def kwh_for_job(self, *, cpu_hours: float, gpu_hours: float, region: str) -> float: ...


@dataclass(slots=True)
class EstimationInput:
    job_id: str
    cpu_hours: float
    gpu_hours: float
    region: str


@dataclass(slots=True)
class EstimationResult:
    job_id: str
    grams_co2e: float
    kwh: float


class EstimationPipeline:
    """Coordinates energy modelling and carbon estimation."""

    def __init__(self, model: EnergyModel, intensity: GridIntensityProvider) -> None:
        self._model = model
        self._intensity = intensity

    async def run(self, payload: EstimationInput) -> EstimationResult:
        kwh = await self._model.kwh_for_job(
            cpu_hours=payload.cpu_hours,
            gpu_hours=payload.gpu_hours,
            region=payload.region,
        )
        grams = kwh * await self._intensity.grams_co2_per_kwh(payload.region)
        return EstimationResult(job_id=payload.job_id, grams_co2e=grams, kwh=kwh)
