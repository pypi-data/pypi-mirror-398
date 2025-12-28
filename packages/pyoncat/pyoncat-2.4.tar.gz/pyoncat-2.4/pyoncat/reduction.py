"""Reduction file builder for creating JSON reduction files."""

from __future__ import annotations

import datetime
import json
import os
import re
import sys
import traceback
from typing import Any


class ReductionFileBuilder:
    """Builder for creating JSON Reduction Files for ONCat cataloging.

    Reduction files document the relationship between raw data and reduced
    data, including all input files (raw data, calibration files, etc.)
    and all output files (processed data, plots, etc.).

    This class does NOT communicate with the ONCat API.  It only creates
    JSON files on disk that can later be cataloged via the API.

    The typical workflow is:

        1. Create builder with user identifier
        2. Add input files (raw data, calibrations, etc.)
        3. Add output files (reduced data, plots, etc.)
        4. Set metadata about the reduction
        5. Write the JSON file to disk

    All mutator methods return `self` for convenient method chaining.
    Use `write_safe()` in autoreduction scripts to ensure cataloging
    failures do not break the reduction.

    Example usage:

        from pyoncat import ReductionFileBuilder, AUTOREDUCTION_USER

        builder = ReductionFileBuilder(user=AUTOREDUCTION_USER)
        builder.add_input(
            "/SNS/ARCS/IPTS-12345/nexus/ARCS_123456.nxs.h5",
            type="raw",
            purpose="sample-data"
        )
        builder.add_output(
            "/SNS/ARCS/IPTS-12345/shared/autoreduce/ARCS_123456.nxs",
            type="processed",
            purpose="reduced-data"
        )
        builder.set_metadata({"ei": 100.0, "t0": 50.0})
        path = builder.write_safe()  # Auto-derives path from inputs

    """

    def __init__(self, user: str, metadata: dict[str, Any] | None = None):
        """Create a new reduction file builder.

        Arguments:
        ---------
            user: str
                XCAMS/UCAMS username or "auto" for autoreduction.  Must be
                lowercase alphanumeric only.  A value must always be
                provided by the caller; there is no default.

            metadata: dict[str, Any] | None
                Optional initial metadata dictionary.  Default: {}

        Example:
            from pyoncat import ReductionFileBuilder, AUTOREDUCTION_USER

            builder = ReductionFileBuilder(user=AUTOREDUCTION_USER)
            builder = ReductionFileBuilder(user="pp4", metadata={"ei": 100.0})

        """
        self._user = user
        self._metadata = metadata if metadata is not None else {}
        self._input_files: list[dict[str, Any]] = []
        self._output_files: list[dict[str, Any]] = []
        self._validation_errors: list[str] = []

    def add_input(
        self,
        location: str,
        type: str,
        purpose: str,
        fields: dict[str, str] | None = None,
        relative_to: str | None = None,
    ) -> ReductionFileBuilder:
        """Add an input file to the reduction.

        Arguments:
        ---------
            location: str
                Path to the input file.  Must be absolute, or relative if
                relative_to is provided.

            type: str
                File type.  Must be one of: "raw", "processed",
                "user-provided", "history".

            purpose: str
                File purpose in kebab-case (e.g., "sample-data",
                "vanadium", "detector-calibration", "mask", "ub-matrix").
                Server validates format but accepts any kebab-case string.

            fields: dict[str, str] | None
                Optional metadata field mappings for this file.  Dict of
                "source.path": "dest_path" for extracting metadata.
                Primarily used for processed files.

            relative_to: str | None
                Base directory for relative paths.  If provided and
                location is relative, will be resolved to absolute path.

        Returns:
        -------
            Self for method chaining.  Never raises; validation errors are
            stored internally and surfaced by validate().

        Example:
            # Absolute path
            builder.add_input(
                "/SNS/ARCS/IPTS-12345/nexus/ARCS_123456.nxs.h5",
                type="raw",
                purpose="sample-data"
            )

            # Relative path with relative_to
            builder.add_input(
                "./van.nxs",
                type="processed",
                purpose="detector-calibration",
                relative_to="/SNS/ARCS/IPTS-12345/shared/autoreduce"
            )

            # Method chaining (use keyword args for clarity)
            builder.add_input(
                file1, type="raw", purpose="sample-data"
            ).add_input(
                file2, type="raw", purpose="vanadium"
            )

        """
        resolved_location = self._resolve_path(location, relative_to)

        file_dict: dict[str, Any] = {
            "location": resolved_location,
            "type": type,
            "purpose": purpose,
        }

        # Only include fields if provided and non-empty
        if fields:
            file_dict["fields"] = fields

        self._input_files.append(file_dict)
        return self

    def add_output(
        self,
        location: str,
        type: str,
        purpose: str,
        fields: dict[str, str] | None = None,
        relative_to: str | None = None,
    ) -> ReductionFileBuilder:
        """Add an output file to the reduction.

        The 'fields' parameter is primarily used for output files to extract
        specific metadata from processed NeXus files, for example:

            fields={
                "mantid_workspace_1.sample.geom_thickness": "thickness",
                "mantid_workspace_1.title": "title"
            }

        Arguments:
        ---------
            location: str
                Path to the output file.  Must be absolute, or relative if
                relative_to is provided.

            type: str
                File type.  Must be one of: "raw", "processed",
                "user-provided", "history".

            purpose: str
                File purpose in kebab-case (e.g., "reduced-data",
                "plot", "log").  Server validates format but accepts any
                kebab-case string.

            fields: dict[str, str] | None
                Optional metadata field mappings for this file.  Dict of
                "source.path": "dest_path" for extracting metadata.
                Commonly used for processed output files.

            relative_to: str | None
                Base directory for relative paths.  If provided and
                location is relative, will be resolved to absolute path.

        Returns:
        -------
            Self for method chaining.  Never raises; validation errors are
            stored internally and surfaced by validate().

        Example:
            builder.add_output(
                "/SNS/ARCS/IPTS-12345/shared/autoreduce/ARCS_123456.nxs",
                type="processed",
                purpose="reduced-data",
                fields={"MDHistoWorkspace.experiment0.logs.ei.value": "ei"}
            )

            # With relative path
            builder.add_output(
                "ARCS_123456.nxs",
                type="processed",
                purpose="reduced-data",
                relative_to=outdir
            )

        """
        resolved_location = self._resolve_path(location, relative_to)

        file_dict: dict[str, Any] = {
            "location": resolved_location,
            "type": type,
            "purpose": purpose,
        }

        # Only include fields if provided and non-empty
        if fields:
            file_dict["fields"] = fields

        self._output_files.append(file_dict)
        return self

    def set_metadata(self, metadata: dict[str, Any]) -> ReductionFileBuilder:
        """Set the reduction metadata, replacing any existing metadata.

        No validation is performed on structure or content.  This is a
        "wild west" field where any valid JSON is accepted.  While no
        validation is enforced, consistency across instruments is
        encouraged.  See documentation for recommended metadata fields.

        Arguments:
        ---------
            metadata: dict[str, Any]
                Dictionary of metadata fields.  Can be empty.

        Returns:
        -------
            Self for method chaining.

        Example:
            builder.set_metadata({
                "ei": 100.0,
                "t0": 50.0,
                "duration": 3600.0,
                "sample": {
                    "name": "MySample",
                    "temperature": 300.0
                }
            })

        """
        self._metadata = metadata
        return self

    def update_metadata(
        self, metadata: dict[str, Any]
    ) -> ReductionFileBuilder:
        """Update the reduction metadata by merging with existing metadata.

        Performs a shallow merge: top-level keys from metadata are merged
        into existing metadata, but nested dictionaries are replaced, not
        merged.

        Arguments:
        ---------
            metadata: dict[str, Any]
                Dictionary of metadata fields to merge.

        Returns:
        -------
            Self for method chaining.

        Example:
            builder.set_metadata({"ei": 100.0})
            builder.update_metadata({"t0": 50.0})
            builder.get_metadata()  # {"ei": 100.0, "t0": 50.0}

            # Nested dicts are replaced, not merged
            builder.set_metadata({"sample": {"name": "A"}})
            builder.update_metadata({"sample": {"temp": 300}})
            builder.get_metadata()  # {"sample": {"temp": 300}}

        """
        self._metadata.update(metadata)
        return self

    def get_metadata(self) -> dict[str, Any]:
        """Get a copy of the current metadata dictionary.

        Returns:
        -------
            Copy of current metadata.  Modifications to the returned dict
            won't affect builder state.

        Example:
            metadata = builder.get_metadata()
            metadata["new_field"] = "value"  # Doesn't affect builder
            builder.set_metadata(metadata)   # Explicit update required

        """
        return self._metadata.copy()

    def clear_outputs(self) -> ReductionFileBuilder:
        """Remove all output files from the builder.

        Useful when re-running a reduction: keep the same inputs but start
        fresh with outputs.

        Returns:
        -------
            Self for method chaining.

        Example:
            builder = ReductionFileBuilder(user="auto")
            builder.add_input(input_file, "raw", "sample-data")
            builder.add_output(output_file, "processed", "reduced-data")

            # Reduction failed, try again
            builder.clear_outputs()
            builder.add_output(new_output_file, "processed", "reduced-data")
            builder.write_safe()

        """
        self._output_files = []
        return self

    def validate(self) -> list[str]:
        """Validate the builder state and return any errors.

        Performs minimal validation:

        - Returns any errors accumulated from mutators (e.g., relative
          paths without relative_to)
        - At least one input file present
        - At least one output file present
        - User is set and non-empty
        - Metadata is a dict
        - If auto-deriving path: at least one input is type="raw" and
          purpose="sample-data"
        - All paths must be absolute and canonical (`/SNS/...` or
          `/HFIR/...` for IPTS directories, or `/SNS/...` or `/HFIR/...`
          for shared directories like /SNS/ARCS/shared/...)

        Does NOT validate:

        - Type/purpose enum values (server validates)
        - Detailed file path patterns beyond canonical roots
        - Fields mapping format (server validates)
        - Metadata structure (intentionally unrestricted)

        Returns:
        -------
            List of error messages.  Empty list if valid.

        Example:
            errors = builder.validate()
            if errors:
                print("Validation failed:")
                for error in errors:
                    print(f"  - {error}")
            else:
                builder.write()

        """
        errors = list(self._validation_errors)  # Copy accumulated errors

        # Check for inputs and outputs
        if not self._input_files:
            errors.append("At least one input file is required")

        if not self._output_files:
            errors.append("At least one output file is required")

        # Check user
        if not self._user:
            errors.append("User must be set and non-empty")

        # Check metadata is a dict
        if not isinstance(self._metadata, dict):
            errors.append("Metadata must be a dictionary")

        # Check for raw sample-data input (needed for auto-derivation)
        has_raw_sample = any(
            f.get("type") == "raw" and f.get("purpose") == "sample-data"
            for f in self._input_files
        )
        if not has_raw_sample:
            errors.append(
                "At least one input file with type='raw' and "
                "purpose='sample-data' is required for path auto-derivation"
            )

        # Validate canonical paths
        for file_list, file_type in [
            (self._input_files, "input"),
            (self._output_files, "output"),
        ]:
            for file_dict in file_list:
                location = file_dict.get("location", "")
                if not location.startswith(
                    "/SNS/"
                ) and not location.startswith("/HFIR/"):
                    msg = (
                        f"Path must be canonical (start with /SNS/ or "
                        f"/HFIR/): {location} ({file_type} file)"
                    )
                    errors.append(msg)

        return errors

    def to_dict(self) -> dict[str, Any]:
        """Preview the JSON structure that will be written (without timestamp).

        Returns:
        -------
            Dictionary representing the reduction file structure.  Does not
            include the 'created' timestamp which is generated on write().

        Example:
            import json
            preview = builder.to_dict()
            print(json.dumps(preview, indent=2))

        """
        return {
            "version": "1.0",
            "input_files": self._input_files,
            "output_files": self._output_files,
            "user": self._user,
            "metadata": self._metadata,
        }

    def write(self, path: str | None = None, overwrite: bool = True) -> str:
        """Write the reduction file to disk.

        Behavior:

        1. Validates builder state via validate()
        2. Generates RFC3339 timestamp with timezone
        3. Derives path if not provided (from first raw sample-data input)
        4. Creates parent directories if needed
        5. Writes JSON file with 4-space indentation, sorted keys
        6. Returns absolute path to written file

        Auto-derived path format:

            /{facility}/{inst}/{experiment}/shared/autoreduce/{inst}_{run}.json

        Arguments:
        ---------
            path: str | None
                Optional explicit path to write to.  If None, auto-derives
                path from first input file with type="raw" and
                purpose="sample-data".

            overwrite: bool
                Whether to overwrite existing file.  Default: True

        Returns:
        -------
            Absolute path to the written file.

        Raises:
        ------
            ValueError
                If validation fails or path cannot be auto-derived.

            FileExistsError
                If file exists and overwrite=False.

            IOError
                If write fails.

        Example:
            # Auto-derive path
            path = builder.write()
            # /SNS/ARCS/IPTS-12345/shared/autoreduce/ARCS_123456.json

            # Explicit path
            path = builder.write("/custom/path/reduction.json")

            # Don't overwrite
            path = builder.write(overwrite=False)  # Raises if exists

        """
        # 1. Validate
        errors = self.validate()
        if errors:
            error_list = "\n".join(f"  - {e}" for e in errors)
            msg = f"Validation failed:\n{error_list}"
            raise ValueError(msg)

        # 2. Derive path if needed
        if path is None:
            path = self._derive_path()

        # 3. Check overwrite
        if not overwrite and os.path.exists(path):
            msg = f"File already exists: {path}"
            raise FileExistsError(msg)

        # 4. Build JSON structure
        content = {
            "version": "1.0",
            "input_files": self._input_files,
            "output_files": self._output_files,
            "created": self._generate_timestamp(),
            "user": self._user,
            "metadata": self._metadata,
        }

        # 5. Create directories
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # 6. Write file
        with open(path, "w") as f:
            json.dump(content, f, indent=4, sort_keys=True)

        return path

    def write_safe(
        self, path: str | None = None, overwrite: bool = True
    ) -> str | None:
        """Write the reduction file to disk with error handling.  Never raises.

        This is a convenience wrapper around write() that catches all
        exceptions and prints them to stderr.  Use this in autoreduction
        scripts where cataloging failures should not break the reduction.

        Arguments:
        ---------
            path: str | None
                Same as write().

            overwrite: bool
                Same as write().

        Returns:
        -------
            Absolute path to written file on success, None on failure.

        Example:
            # In autoreduction script - safe, won't crash reduction
            path = builder.write_safe()
            if path:
                print(f"Reduction cataloged: {path}")
            else:
                print("Warning: Cataloging failed (see stderr)")

        """
        try:
            return self.write(path, overwrite)
        except Exception as e:  # noqa: BLE001
            # Intentionally catch all exceptions - design requirement for
            # autoreduction scripts where cataloging failures should never
            # break the reduction workflow
            msg = f"Warning: Failed to catalog reduction: {e}"
            print(msg, file=sys.stderr)
            traceback.print_exc()
            return None

    @classmethod
    def load(cls, path: str) -> ReductionFileBuilder:
        """Load an existing reduction file for modification.

        Arguments:
        ---------
            path: str
                Path to existing JSON reduction file.

        Returns:
        -------
            New ReductionFileBuilder instance populated with file contents.

        Raises:
        ------
            FileNotFoundError
                If file doesn't exist.

            ValueError
                If file is not valid JSON or missing required fields.

        Example:
            # Load and modify existing file
            builder = ReductionFileBuilder.load(
                "/SNS/ARCS/IPTS-12345/shared/autoreduce/ARCS_123456.json"
            )
            builder.add_output(
                new_output_file, type="processed", purpose="reduced-data"
            )
            builder.write()  # Overwrites original file

        """
        if not os.path.exists(path):
            msg = f"Reduction file not found: {path}"
            raise FileNotFoundError(msg)

        with open(path) as f:
            content = json.load(f)

        # Validate required fields
        required = ["user", "metadata", "input_files", "output_files"]
        missing = [f for f in required if f not in content]
        if missing:
            msg = f"Invalid reduction file, missing fields: {missing}"
            raise ValueError(msg)

        # Create builder
        builder = cls(user=content["user"], metadata=content["metadata"])

        # Add files (without fields if not present)
        for f in content["input_files"]:
            builder.add_input(
                f["location"],
                f["type"],
                f["purpose"],
                fields=f.get("fields"),  # May be None
            )

        for f in content["output_files"]:
            builder.add_output(
                f["location"],
                f["type"],
                f["purpose"],
                fields=f.get("fields"),
            )

        return builder

    # Private helper methods

    def _resolve_path(self, location: str, relative_to: str | None) -> str:
        """Resolve location to absolute path.

        Stores validation errors internally; never raises.
        """
        # If already absolute, use as-is
        # (validation will enforce canonical roots)
        if os.path.isabs(location):
            return location

        # If relative and relative_to provided, resolve
        if relative_to:
            return os.path.abspath(os.path.join(relative_to, location))

        # Relative without relative_to — store error and return as-is
        msg = (
            f"Path must be absolute or have relative_to specified: {location}"
        )
        self._validation_errors.append(msg)
        return location

    def _derive_path(self) -> str:
        """Auto-derive JSON file path from first raw sample-data input.

        Self-contained: duplicates a minimal regex for raw NeXus paths to
        extract facility, instrument, IPTS, and run_number. No imports from
        other parts of this repository.
        """
        # Find first raw sample-data input
        raw_sample = None
        for f in self._input_files:
            if f.get("type") == "raw" and f.get("purpose") == "sample-data":
                raw_sample = f["location"]
                break

        if not raw_sample:
            msg = (
                "Cannot auto-derive path: no input file with type='raw' "
                "and purpose='sample-data'. Either add one or provide "
                "explicit path."
            )
            raise ValueError(msg)

        raw_nexus_regex = re.compile(
            r"^/(?P<facility>SNS|HFIR)/"
            r"(?P<instrument>[A-Z0-9_]+)/"
            r"IPTS-(?P<ipts>\d+)/"
            r"(?:[^/]+/)*"
            r"[^/_]*_(?P<run_number>\d+)"
            r"(?:_event|_histo)?"
            r"\.(?:nxs(?:\.h5)?)$"
        )

        match = raw_nexus_regex.search(raw_sample)
        if not match:
            msg = (
                f"Cannot parse facility/instrument/experiment from: "
                f"{raw_sample}"
            )
            raise ValueError(msg)

        facility = match.group("facility")
        instrument = match.group("instrument")
        ipts = match.group("ipts")
        run_number = match.group("run_number")
        experiment = f"IPTS-{ipts}"

        return (
            f"/{facility}/{instrument}/{experiment}/shared/autoreduce/"
            f"{instrument}_{run_number}.json"
        )

    @staticmethod
    def _generate_timestamp() -> str:
        """Generate RFC3339 timestamp with timezone."""
        now = datetime.datetime.now(datetime.timezone.utc).astimezone()
        return now.isoformat()
