"""Input models for task creation and updates."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .enums import TaskType, TaskVisibility


class TaskCreateInput(BaseModel):
    """Payload for creating a new task."""
    
    name: str = Field(..., description="The name of the task.")
    slug: str | None = Field(None, description="Optional custom slug for the task.")
    time_limit: int = Field(..., description="Time limit in milliseconds.", gt=0)
    memory_limit: int = Field(..., description="Memory limit in megabytes.", gt=0)
    type: TaskType | str = Field(..., description="The type of task (e.g., 'batch').")
    visibility: TaskVisibility | str = Field(
        TaskVisibility.PRIVATE, 
        description="Initial visibility of the task."
    )
    
    model_config = ConfigDict(extra="forbid")


class StatementInput(BaseModel):
    """Payload for updating a task statement content in a specific language."""
    
    title: str | None = Field(None, description="The title of the statement.")
    name: str | None = Field(None, description="The display name (often same as title).")
    legend: str | None = Field(None, description="The main problem description.")
    input_format: str | None = Field(None, description="Description of input format.")
    output_format: str | None = Field(None, description="Description of output format.")
    notes: str | None = Field(None, description="Additional notes or constraints.")
    tutorial: str | None = Field(None, description="Tutorial or editorial content.")
    
    model_config = ConfigDict(extra="allow")  # Allow other fields like 'scoring' if needed


class TypeUpdateInput(BaseModel):
    """Payload for updating the task type."""
    type: TaskType | str
    
    model_config = ConfigDict(extra="allow") 


class CheckerSettingsInput(BaseModel):
    """Payload for updating checker settings."""
    checker_type: str = Field(..., description="Type of checker (e.g., 'custom_checker').")
    checker: str | None = Field(None, description="Source code for custom checker.") 
    checker_language: str | None = Field(None, description="Programming language for custom checker.")
    precision: int | None = Field(None, description="Floating point precision for relevant checkers.")
    
    model_config = ConfigDict(extra="allow")
