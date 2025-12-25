from pydantic import BaseModel, Field


class CLIConfig(BaseModel):
    model_config = {"validate_assignment": True}


class AnalysisConfig(BaseModel):
    cache_ttl_hours: int = Field(
        default=24,
        ge=1,
        le=168,  # 1 week
        description="Cache time-to-live in hours (1-168)",
    )
    allow_prerelease: bool = Field(
        default=False,
        description="Allow pre-release versions (alpha, beta, rc) in recommendations",
    )

    model_config = {"validate_assignment": True}


class AppConfig(BaseModel):
    cli: CLIConfig = Field(default_factory=CLIConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)

    model_config = {
        "extra": "forbid",
        "validate_assignment": True,
    }
