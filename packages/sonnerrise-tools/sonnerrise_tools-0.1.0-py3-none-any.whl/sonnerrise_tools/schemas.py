"""Pydantic schemas for Sonnerrise Tools."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# Current schema version
SCHEMA_VERSION = "1.0"


class EntityCounts(BaseModel):
    """Counts of entities in a backup."""

    personas: int = 0
    definitions: int = 0
    definition_links: int = 0
    tracks: int = 0
    track_links: int = 0
    track_events: int = 0
    promos: int = 0
    promo_links: int = 0

    @property
    def total(self) -> int:
        """Total number of records."""
        return (
            self.personas
            + self.definitions
            + self.definition_links
            + self.tracks
            + self.track_links
            + self.track_events
            + self.promos
            + self.promo_links
        )


class BackupEntities(BaseModel):
    """Container for all entity data."""

    personas: list[dict[str, Any]] = Field(default_factory=list)
    definitions: list[dict[str, Any]] = Field(default_factory=list)
    definition_links: list[dict[str, Any]] = Field(default_factory=list)
    tracks: list[dict[str, Any]] = Field(default_factory=list)
    track_links: list[dict[str, Any]] = Field(default_factory=list)
    track_events: list[dict[str, Any]] = Field(default_factory=list)
    promos: list[dict[str, Any]] = Field(default_factory=list)
    promo_links: list[dict[str, Any]] = Field(default_factory=list)


class BackupData(BaseModel):
    """Complete backup data structure."""

    version: str = SCHEMA_VERSION
    created_at: datetime = Field(default_factory=datetime.now)
    entities: BackupEntities = Field(default_factory=BackupEntities)
    counts: EntityCounts = Field(default_factory=EntityCounts)

    def update_counts(self) -> None:
        """Update counts based on entities."""
        self.counts = EntityCounts(
            personas=len(self.entities.personas),
            definitions=len(self.entities.definitions),
            definition_links=len(self.entities.definition_links),
            tracks=len(self.entities.tracks),
            track_links=len(self.entities.track_links),
            track_events=len(self.entities.track_events),
            promos=len(self.entities.promos),
            promo_links=len(self.entities.promo_links),
        )


class ImportResult(BaseModel):
    """Result of an import operation."""

    success: bool = True
    total_records: int = 0
    imported: EntityCounts = Field(default_factory=EntityCounts)
    skipped: EntityCounts = Field(default_factory=EntityCounts)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        """Whether there were any errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Whether there were any warnings."""
        return len(self.warnings) > 0


class ExportOptions(BaseModel):
    """Options for export operations."""

    include_personas: bool = True
    include_definitions: bool = True
    include_tracks: bool = True
    include_promos: bool = True
    pretty_print: bool = True


class ImportOptions(BaseModel):
    """Options for import operations."""

    skip_existing: bool = False
    create_tables: bool = True
    validate_only: bool = False
    clear_existing: bool = False


class BackupInfo(BaseModel):
    """Information about a backup file."""

    version: str
    created_at: datetime
    counts: EntityCounts
    file_path: str
    file_size: int

    @property
    def is_compatible(self) -> bool:
        """Whether the backup is compatible with current schema."""
        # For now, all 1.x versions are compatible
        return self.version.startswith("1.")
