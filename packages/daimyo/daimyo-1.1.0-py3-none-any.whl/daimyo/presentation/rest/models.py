"""Pydantic models for REST API requests and responses."""

from pydantic import BaseModel, Field


class CategorySummary(BaseModel):
    """Summary of a category for index endpoint."""

    category: str = Field(..., description="Category key (e.g., 'python.web.testing')")
    when: str = Field(..., description="Applicability description")
    rule_count: int = Field(..., description="Number of rules in this category")

    model_config = {
        "json_schema_extra": {
            "example": {
                "category": "python.web.testing",
                "when": "When testing web interfaces implemented in Python",
                "rule_count": 5,
            }
        }
    }


class IndexResponse(BaseModel):
    """Response for /index endpoint."""

    scope_name: str = Field(..., description="Name of the scope")
    description: str = Field(..., description="Scope description")
    commandments: list[CategorySummary] = Field(
        ..., description="Summary of commandment categories"
    )
    suggestions: list[CategorySummary] = Field(..., description="Summary of suggestion categories")
    sources: list[str] = Field(..., description="Sources that contributed to this scope")

    model_config = {
        "json_schema_extra": {
            "example": {
                "scope_name": "team-backend",
                "description": "Backend team specific rules",
                "commandments": [
                    {
                        "category": "python.web.api",
                        "when": "When building REST APIs",
                        "rule_count": 4,
                    }
                ],
                "suggestions": [
                    {
                        "category": "python.web.api",
                        "when": "When building REST APIs",
                        "rule_count": 3,
                    }
                ],
                "sources": ["local"],
            }
        }
    }


class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str = Field(..., description="Error message")

    model_config = {"json_schema_extra": {"example": {"detail": "Scope 'invalid' not found"}}}


__all__ = ["CategorySummary", "IndexResponse", "ErrorResponse"]
