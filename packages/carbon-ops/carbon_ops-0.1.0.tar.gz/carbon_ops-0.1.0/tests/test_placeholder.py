from carbon_ops.pipeline import EstimationInput, EstimationPipeline


class DummyEnergyModel:
    async def kwh_for_job(self, *, cpu_hours: float, gpu_hours: float, _region: str) -> float:
        return cpu_hours * 0.7 + gpu_hours * 1.9


class DummyIntensityProvider:
    async def grams_co2_per_kwh(self, _region: str) -> float:
        return 420.0


async def test_pipeline_runs_with_dummy_components() -> None:
    pipeline = EstimationPipeline(DummyEnergyModel(), DummyIntensityProvider())
    result = await pipeline.run(EstimationInput(job_id="test", cpu_hours=2.0, gpu_hours=1.0, region="us"))
    assert result.job_id == "test"
    assert round(result.kwh, 2) == 3.3
    assert round(result.grams_co2e, 1) == 1386.0