"""Export service for Sonnerrise database dumps."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from sonnerrise_tools.schemas import (
    BackupData,
    BackupEntities,
    ExportOptions,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from sonnerrise_core import SonnerriseConfig


class ExportService:
    """Service for exporting database data to files."""

    def __init__(self, session: Session, config: SonnerriseConfig | None = None) -> None:
        """Initialize export service.

        Args:
            session: SQLAlchemy database session.
            config: Optional Sonnerrise configuration.
        """
        self.session = session
        self.config = config

    def export_all(
        self,
        output_path: str | Path,
        format: str = "json",
        options: ExportOptions | None = None,
    ) -> BackupData:
        """Export all data to a file.

        Args:
            output_path: Path to output file.
            format: Output format ('json' or 'yaml').
            options: Export options.

        Returns:
            BackupData containing all exported entities.
        """
        if options is None:
            options = ExportOptions()

        entities = BackupEntities()

        if options.include_personas:
            entities.personas = self._export_personas()

        if options.include_definitions:
            entities.definitions = self._export_definitions()
            entities.definition_links = self._export_definition_links()

        if options.include_tracks:
            entities.tracks = self._export_tracks()
            entities.track_links = self._export_track_links()
            entities.track_events = self._export_track_events()

        if options.include_promos:
            entities.promos = self._export_promos()
            entities.promo_links = self._export_promo_links()

        backup = BackupData(
            created_at=datetime.now(),
            entities=entities,
        )
        backup.update_counts()

        self._write_file(output_path, backup, format, options.pretty_print)

        return backup

    def export_personas(
        self,
        output_path: str | Path,
        format: str = "json",
        pretty_print: bool = True,
    ) -> BackupData:
        """Export only personas to a file.

        Args:
            output_path: Path to output file.
            format: Output format ('json' or 'yaml').
            pretty_print: Whether to pretty print output.

        Returns:
            BackupData containing exported personas.
        """
        options = ExportOptions(
            include_personas=True,
            include_definitions=False,
            include_tracks=False,
            include_promos=False,
            pretty_print=pretty_print,
        )
        return self.export_all(output_path, format, options)

    def export_definitions(
        self,
        output_path: str | Path,
        format: str = "json",
        pretty_print: bool = True,
    ) -> BackupData:
        """Export only definitions to a file.

        Args:
            output_path: Path to output file.
            format: Output format ('json' or 'yaml').
            pretty_print: Whether to pretty print output.

        Returns:
            BackupData containing exported definitions.
        """
        options = ExportOptions(
            include_personas=False,
            include_definitions=True,
            include_tracks=False,
            include_promos=False,
            pretty_print=pretty_print,
        )
        return self.export_all(output_path, format, options)

    def export_tracks(
        self,
        output_path: str | Path,
        format: str = "json",
        pretty_print: bool = True,
    ) -> BackupData:
        """Export only tracks to a file.

        Args:
            output_path: Path to output file.
            format: Output format ('json' or 'yaml').
            pretty_print: Whether to pretty print output.

        Returns:
            BackupData containing exported tracks.
        """
        options = ExportOptions(
            include_personas=False,
            include_definitions=False,
            include_tracks=True,
            include_promos=False,
            pretty_print=pretty_print,
        )
        return self.export_all(output_path, format, options)

    def export_promos(
        self,
        output_path: str | Path,
        format: str = "json",
        pretty_print: bool = True,
    ) -> BackupData:
        """Export only promos to a file.

        Args:
            output_path: Path to output file.
            format: Output format ('json' or 'yaml').
            pretty_print: Whether to pretty print output.

        Returns:
            BackupData containing exported promos.
        """
        options = ExportOptions(
            include_personas=False,
            include_definitions=False,
            include_tracks=False,
            include_promos=True,
            pretty_print=pretty_print,
        )
        return self.export_all(output_path, format, options)

    def _export_personas(self) -> list[dict[str, Any]]:
        """Export all personas."""
        from sonnerrise_personas import Persona

        personas = self.session.query(Persona).all()
        return [self._model_to_dict(p) for p in personas]

    def _export_definitions(self) -> list[dict[str, Any]]:
        """Export all definitions."""
        from sonnerrise_definitions import Definition

        definitions = self.session.query(Definition).all()
        return [self._model_to_dict(d) for d in definitions]

    def _export_definition_links(self) -> list[dict[str, Any]]:
        """Export all definition links."""
        from sonnerrise_definitions import DefinitionLink

        links = self.session.query(DefinitionLink).all()
        return [self._model_to_dict(link) for link in links]

    def _export_tracks(self) -> list[dict[str, Any]]:
        """Export all tracks."""
        from sonnerrise_tracks import Track

        tracks = self.session.query(Track).all()
        return [self._model_to_dict(t) for t in tracks]

    def _export_track_links(self) -> list[dict[str, Any]]:
        """Export all track links."""
        from sonnerrise_tracks import TrackLink

        links = self.session.query(TrackLink).all()
        return [self._model_to_dict(link) for link in links]

    def _export_track_events(self) -> list[dict[str, Any]]:
        """Export all track events."""
        from sonnerrise_tracks import TrackEvent

        events = self.session.query(TrackEvent).all()
        return [self._model_to_dict(event) for event in events]

    def _export_promos(self) -> list[dict[str, Any]]:
        """Export all promos."""
        from sonnerrise_promo import Promo

        promos = self.session.query(Promo).all()
        return [self._model_to_dict(p) for p in promos]

    def _export_promo_links(self) -> list[dict[str, Any]]:
        """Export all promo links."""
        from sonnerrise_promo import PromoLink

        links = self.session.query(PromoLink).all()
        return [self._model_to_dict(link) for link in links]

    def _model_to_dict(self, model: Any) -> dict[str, Any]:
        """Convert SQLAlchemy model to dictionary.

        Args:
            model: SQLAlchemy model instance.

        Returns:
            Dictionary representation of model.
        """
        result = {}
        for column in model.__table__.columns:
            value = getattr(model, column.name)
            # Handle datetime serialization
            if isinstance(value, datetime):
                value = value.isoformat()
            # Handle enum serialization
            elif hasattr(value, "value"):
                value = value.value
            result[column.name] = value
        return result

    def _write_file(
        self,
        output_path: str | Path,
        backup: BackupData,
        format: str,
        pretty_print: bool,
    ) -> None:
        """Write backup data to file.

        Args:
            output_path: Path to output file.
            backup: Backup data to write.
            format: Output format ('json' or 'yaml').
            pretty_print: Whether to pretty print output.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for serialization
        data = backup.model_dump(mode="json")

        if format.lower() == "yaml":
            with open(path, "w") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        else:
            with open(path, "w") as f:
                if pretty_print:
                    json.dump(data, f, indent=2, default=str)
                else:
                    json.dump(data, f, default=str)
