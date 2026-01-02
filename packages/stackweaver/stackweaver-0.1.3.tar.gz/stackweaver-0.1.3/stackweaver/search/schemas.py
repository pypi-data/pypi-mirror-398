"""
Pydantic schemas for tool definitions with strict validation.

These schemas ensure 100% valid tool catalog entries and prevent AI hallucinations.
"""

from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class EnvVarSchema(BaseModel):
    """Environment variable definition for a tool."""

    key: str = Field(..., description="Environment variable name (e.g., POSTGRES_PASSWORD)")
    required: bool = Field(..., description="Whether this env var must be set")
    default: str | None = Field(None, description="Default value if not required")
    description: str = Field(..., description="Human-readable description of the variable")
    secret: bool = Field(False, description="Whether this is a secret (password, API key)")

    @field_validator("key")
    @classmethod
    def validate_key_format(cls, v: str) -> str:
        """
        Ensure env var key follows reasonable conventions.

        Relaxed validation: allows uppercase, underscores, and double underscores
        for OSS tools with non-standard naming (e.g., GITEA__database__PASSWD).
        """
        # Allow alphanumeric, underscores, and must start with letter/underscore
        if not v:
            raise ValueError("Environment variable key cannot be empty")
        if not (v[0].isalpha() or v[0] == "_"):
            raise ValueError(f"Environment variable key must start with letter or underscore: {v}")
        # Allow alphanumeric + underscores (uppercase preferred but not enforced)
        allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_abcdefghijklmnopqrstuvwxyz")
        if not all(c in allowed_chars for c in v):
            raise ValueError(f"Environment variable key contains invalid characters: {v}")
        return v

    @model_validator(mode="after")
    def validate_required_default(self) -> "EnvVarSchema":
        """If required=True, default must be None. If required=False, default should be set."""
        if self.required and self.default is not None:
            raise ValueError("Required env vars cannot have a default value")
        if not self.required and self.default is None and not self.secret:
            # Warn but don't fail: non-required, non-secret vars should have defaults
            pass
        return self


class VolumeSchema(BaseModel):
    """Volume mount definition for a tool."""

    name: str = Field(..., description="Volume name (e.g., taiga-data)")
    mount_path: str = Field(
        ..., description="Container mount path (e.g., /var/lib/postgresql/data)"
    )
    description: str = Field(..., description="What this volume stores")

    @field_validator("name")
    @classmethod
    def validate_name_format(cls, v: str) -> str:
        """Ensure volume name uses lowercase-with-hyphens."""
        if not v.islower() or not v.replace("-", "").isalnum():
            raise ValueError(f"Volume name must be lowercase-with-hyphens: {v}")
        return v

    @field_validator("mount_path")
    @classmethod
    def validate_mount_path(cls, v: str) -> str:
        """Ensure mount path is absolute and Unix-style."""
        if not v.startswith("/"):
            raise ValueError(f"Mount path must be absolute (start with /): {v}")
        return v


class ToolSchema(BaseModel):
    """
    Complete tool definition with strict validation.

    This schema prevents hallucinations by enforcing:
    - Valid Docker image names
    - Required fields presence
    - Realistic quality scores
    - At least one exposed port
    """

    # Required identification fields
    id: str = Field(
        ...,
        description="Unique tool identifier (lowercase-with-hyphens)",
        pattern=r"^[a-z0-9-]+$",
    )
    name: str = Field(..., description="Human-readable tool name")
    category: str = Field(
        ...,
        description="Tool category (e.g., CRM, Project Management, Chat)",
    )
    docker_image: str = Field(..., description="Docker Hub image (e.g., taigaio/taiga:latest)")
    description: str = Field(..., description="Tool description for search matching")

    # Quality scoring fields
    github_stars: int = Field(..., ge=0, description="GitHub stars (>1000 for production)")
    last_updated: datetime = Field(..., description="Last image update date")
    security_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Security score (0-1, based on vulnerability scans)",
    )
    stability_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Stability score (0-1, based on release frequency)",
    )

    # Configuration fields
    env_vars: list[EnvVarSchema] = Field(
        default_factory=list,
        description="Environment variables required by the tool",
    )
    volumes: list[VolumeSchema] = Field(
        default_factory=list,
        description="Persistent volumes required by the tool",
    )
    ports: list[int] = Field(
        ...,
        min_length=1,
        description="Exposed ports (at least one required)",
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="Tool dependencies (e.g., ['postgres:15', 'redis:7'])",
    )

    # Metadata
    tags: list[str] = Field(
        default_factory=list,
        description="Search tags (e.g., ['crm', 'sales', 'contacts'])",
    )

    @field_validator("docker_image")
    @classmethod
    def validate_docker_image(cls, v: str) -> str:
        """
        Validate Docker image format: [registry/]repository[:tag]

        Examples:
        - postgres:15
        - taigaio/taiga:latest
        - ghcr.io/owner/repo:v1.0.0
        """
        import re

        # Docker image regex (simplified, covers most cases)
        pattern = r"^([a-z0-9]+([._-][a-z0-9]+)*(\.[a-z]{2,})?/)?[a-z0-9-_.]+(/[a-z0-9-_.]+)*(:[a-z0-9-_.]+)?$"

        if not re.match(pattern, v, re.IGNORECASE):
            raise ValueError(f"Invalid Docker image format: {v}")

        return v

    @field_validator("ports")
    @classmethod
    def validate_ports(cls, v: list[int]) -> list[int]:
        """Ensure ports are in valid range (1-65535)."""
        for port in v:
            if not 1 <= port <= 65535:
                raise ValueError(f"Port must be between 1 and 65535: {port}")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """
        Ensure category uses proper casing.

        Preserves all-caps acronyms (CRM, CMS) and applies title case to others.
        """
        # If all uppercase and len > 1, assume it's an acronym (CRM, CMS)
        if v.isupper() and len(v) > 1:
            return v
        # Otherwise apply title case
        return v.title()

    @model_validator(mode="after")
    def validate_quality_thresholds(self) -> "ToolSchema":
        """
        Enforce quality thresholds for production readiness.

        - GitHub stars >= 1000
        - Last updated within 6 months
        """
        if self.github_stars < 1000:
            raise ValueError(
                f"Tool {self.id} has only {self.github_stars} stars "
                f"(minimum 1000 for production)"
            )

        # Check last updated within 6 months
        from datetime import timedelta

        six_months_ago = datetime.now(UTC) - timedelta(days=180)
        if self.last_updated < six_months_ago:
            raise ValueError(
                f"Tool {self.id} last updated {self.last_updated.date()} "
                f"(must be within 6 months)"
            )

        return self

    def calculate_quality_score(self) -> float:
        """
        Calculate overall quality score (0-10) based on multiple factors.

        Weighted formula:
        - GitHub stars (40%): normalized log scale
        - Security score (30%): 0-1 scale
        - Stability score (20%): 0-1 scale
        - Freshness (10%): days since last update
        """
        import math
        from datetime import datetime

        # GitHub stars component (logarithmic scale, 40% weight)
        # 1K stars = 5.0, 10K = 7.0, 100K = 9.0
        stars_score = min(10.0, 3.0 + math.log10(self.github_stars))
        stars_weighted = stars_score * 0.4

        # Security score component (30% weight, scale 0-10)
        security_weighted = self.security_score * 10 * 0.3

        # Stability score component (20% weight, scale 0-10)
        stability_weighted = self.stability_score * 10 * 0.2

        # Freshness component (10% weight)

        days_old = (datetime.now(UTC) - self.last_updated).days
        freshness = max(0.0, 1.0 - (days_old / 180))  # 0-1 scale, 6 months decay
        freshness_weighted = freshness * 10 * 0.1

        total_score = stars_weighted + security_weighted + stability_weighted + freshness_weighted

        return round(total_score, 1)


class ToolSearchResult(BaseModel):
    """Search result with tool and relevance score."""

    tool: ToolSchema
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Vector similarity score")
    quality_score: float = Field(..., ge=0.0, le=10.0, description="Tool quality score")

    def combined_score(self) -> float:
        """Combined ranking score (relevance * quality)."""
        return round(self.relevance_score * (self.quality_score / 10.0), 3)
