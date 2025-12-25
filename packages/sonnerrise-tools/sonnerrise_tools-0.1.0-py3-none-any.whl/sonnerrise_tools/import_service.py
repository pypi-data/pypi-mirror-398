"""Import service for Sonnerrise database loading."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from sonnerrise_tools.schemas import (
    BackupData,
    BackupInfo,
    EntityCounts,
    ImportOptions,
    ImportResult,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from sonnerrise_core import SonnerriseConfig


class ImportService:
    """Service for importing data from backup files."""

    def __init__(self, session: Session, config: SonnerriseConfig | None = None) -> None:
        """Initialize import service.

        Args:
            session: SQLAlchemy database session.
            config: Optional Sonnerrise configuration.
        """
        self.session = session
        self.config = config

    def get_backup_info(self, file_path: str | Path) -> BackupInfo:
        """Get information about a backup file without importing.

        Args:
            file_path: Path to backup file.

        Returns:
            BackupInfo with file metadata.
        """
        path = Path(file_path)
        data = self._read_file(path)
        backup = BackupData.model_validate(data)

        return BackupInfo(
            version=backup.version,
            created_at=backup.created_at,
            counts=backup.counts,
            file_path=str(path.absolute()),
            file_size=path.stat().st_size,
        )

    def validate(self, file_path: str | Path) -> ImportResult:
        """Validate a backup file without importing.

        Args:
            file_path: Path to backup file.

        Returns:
            ImportResult with validation results.
        """
        options = ImportOptions(validate_only=True)
        return self.import_all(file_path, options)

    def import_all(
        self,
        file_path: str | Path,
        options: ImportOptions | None = None,
    ) -> ImportResult:
        """Import all data from a backup file.

        Args:
            file_path: Path to backup file.
            options: Import options.

        Returns:
            ImportResult with import statistics.
        """
        if options is None:
            options = ImportOptions()

        result = ImportResult()

        try:
            path = Path(file_path)
            data = self._read_file(path)
            backup = BackupData.model_validate(data)

            # Check version compatibility
            if not backup.version.startswith("1."):
                result.errors.append(
                    f"Incompatible backup version: {backup.version}. Expected 1.x"
                )
                result.success = False
                return result

            result.total_records = backup.counts.total

            if options.validate_only:
                return result

            if options.create_tables:
                self._ensure_tables()

            if options.clear_existing:
                self._clear_all_data()

            # Import in dependency order
            self._import_personas(backup.entities.personas, options, result)
            self._import_definitions(backup.entities.definitions, options, result)
            self._import_definition_links(backup.entities.definition_links, options, result)
            self._import_tracks(backup.entities.tracks, options, result)
            self._import_track_links(backup.entities.track_links, options, result)
            self._import_track_events(backup.entities.track_events, options, result)
            self._import_promos(backup.entities.promos, options, result)
            self._import_promo_links(backup.entities.promo_links, options, result)

            self.session.commit()

        except Exception as e:
            self.session.rollback()
            result.errors.append(str(e))
            result.success = False

        return result

    def _read_file(self, path: Path) -> dict[str, Any]:
        """Read backup file.

        Args:
            path: Path to backup file.

        Returns:
            Parsed backup data.
        """
        with open(path) as f:
            content = f.read()

        if path.suffix.lower() in (".yaml", ".yml"):
            return yaml.safe_load(content)
        else:
            return json.loads(content)

    def _ensure_tables(self) -> None:
        """Ensure all required tables exist."""
        from sonnerrise_core.models import BaseModel

        BaseModel.metadata.create_all(self.session.get_bind())

    def _clear_all_data(self) -> None:
        """Clear all existing data."""
        from sonnerrise_definitions import Definition, DefinitionLink
        from sonnerrise_personas import Persona
        from sonnerrise_promo import Promo, PromoLink
        from sonnerrise_tracks import Track, TrackEvent, TrackLink

        # Delete in reverse dependency order
        self.session.query(PromoLink).delete()
        self.session.query(Promo).delete()
        self.session.query(TrackEvent).delete()
        self.session.query(TrackLink).delete()
        self.session.query(Track).delete()
        self.session.query(DefinitionLink).delete()
        self.session.query(Definition).delete()
        self.session.query(Persona).delete()

        # Flush deletes and expunge all to clear identity map
        self.session.flush()
        self.session.expunge_all()

    def _import_personas(
        self,
        personas: list[dict[str, Any]],
        options: ImportOptions,
        result: ImportResult,
    ) -> None:
        """Import personas."""
        from sonnerrise_personas import Persona

        for data in personas:
            try:
                if options.skip_existing:
                    existing = self.session.query(Persona).filter_by(id=data.get("id")).first()
                    if existing:
                        result.skipped.personas += 1
                        continue

                persona = Persona(**self._prepare_data(data))
                self.session.merge(persona)
                result.imported.personas += 1
            except Exception as e:
                result.errors.append(f"Error importing persona {data.get('id')}: {e}")

    def _import_definitions(
        self,
        definitions: list[dict[str, Any]],
        options: ImportOptions,
        result: ImportResult,
    ) -> None:
        """Import definitions."""
        from sonnerrise_definitions import Definition

        for data in definitions:
            try:
                if options.skip_existing:
                    existing = self.session.query(Definition).filter_by(id=data.get("id")).first()
                    if existing:
                        result.skipped.definitions += 1
                        continue

                definition = Definition(**self._prepare_data(data))
                self.session.merge(definition)
                result.imported.definitions += 1
            except Exception as e:
                result.errors.append(f"Error importing definition {data.get('id')}: {e}")

    def _import_definition_links(
        self,
        links: list[dict[str, Any]],
        options: ImportOptions,
        result: ImportResult,
    ) -> None:
        """Import definition links."""
        from sonnerrise_definitions import DefinitionLink

        for data in links:
            try:
                if options.skip_existing:
                    existing = self.session.query(DefinitionLink).filter_by(id=data.get("id")).first()
                    if existing:
                        result.skipped.definition_links += 1
                        continue

                link = DefinitionLink(**self._prepare_data(data))
                self.session.merge(link)
                result.imported.definition_links += 1
            except Exception as e:
                result.errors.append(f"Error importing definition link {data.get('id')}: {e}")

    def _import_tracks(
        self,
        tracks: list[dict[str, Any]],
        options: ImportOptions,
        result: ImportResult,
    ) -> None:
        """Import tracks."""
        from sonnerrise_tracks import Track

        for data in tracks:
            try:
                if options.skip_existing:
                    existing = self.session.query(Track).filter_by(id=data.get("id")).first()
                    if existing:
                        result.skipped.tracks += 1
                        continue

                track = Track(**self._prepare_data(data))
                self.session.merge(track)
                result.imported.tracks += 1
            except Exception as e:
                result.errors.append(f"Error importing track {data.get('id')}: {e}")

    def _import_track_links(
        self,
        links: list[dict[str, Any]],
        options: ImportOptions,
        result: ImportResult,
    ) -> None:
        """Import track links."""
        from sonnerrise_tracks import TrackLink

        for data in links:
            try:
                if options.skip_existing:
                    existing = self.session.query(TrackLink).filter_by(id=data.get("id")).first()
                    if existing:
                        result.skipped.track_links += 1
                        continue

                link = TrackLink(**self._prepare_data(data))
                self.session.merge(link)
                result.imported.track_links += 1
            except Exception as e:
                result.errors.append(f"Error importing track link {data.get('id')}: {e}")

    def _import_track_events(
        self,
        events: list[dict[str, Any]],
        options: ImportOptions,
        result: ImportResult,
    ) -> None:
        """Import track events."""
        from sonnerrise_tracks import TrackEvent

        for data in events:
            try:
                if options.skip_existing:
                    existing = self.session.query(TrackEvent).filter_by(id=data.get("id")).first()
                    if existing:
                        result.skipped.track_events += 1
                        continue

                event = TrackEvent(**self._prepare_data(data))
                self.session.merge(event)
                result.imported.track_events += 1
            except Exception as e:
                result.errors.append(f"Error importing track event {data.get('id')}: {e}")

    def _import_promos(
        self,
        promos: list[dict[str, Any]],
        options: ImportOptions,
        result: ImportResult,
    ) -> None:
        """Import promos."""
        from sonnerrise_promo import Promo

        for data in promos:
            try:
                if options.skip_existing:
                    existing = self.session.query(Promo).filter_by(id=data.get("id")).first()
                    if existing:
                        result.skipped.promos += 1
                        continue

                promo = Promo(**self._prepare_data(data))
                self.session.merge(promo)
                result.imported.promos += 1
            except Exception as e:
                result.errors.append(f"Error importing promo {data.get('id')}: {e}")

    def _import_promo_links(
        self,
        links: list[dict[str, Any]],
        options: ImportOptions,
        result: ImportResult,
    ) -> None:
        """Import promo links."""
        from sonnerrise_promo import PromoLink

        for data in links:
            try:
                if options.skip_existing:
                    existing = self.session.query(PromoLink).filter_by(id=data.get("id")).first()
                    if existing:
                        result.skipped.promo_links += 1
                        continue

                link = PromoLink(**self._prepare_data(data))
                self.session.merge(link)
                result.imported.promo_links += 1
            except Exception as e:
                result.errors.append(f"Error importing promo link {data.get('id')}: {e}")

    def _prepare_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Prepare data for model creation.

        Handles datetime parsing and other type conversions.

        Args:
            data: Raw data dictionary.

        Returns:
            Prepared data dictionary.
        """
        result = {}
        for key, value in data.items():
            if value is None:
                result[key] = value
            elif key.endswith("_at") and isinstance(value, str):
                # Parse datetime strings
                try:
                    result[key] = datetime.fromisoformat(value)
                except ValueError:
                    result[key] = value
            else:
                result[key] = value
        return result
