"""
DVT (Data Virtualization Tool) Profile Extensions

This module extends the dbt Profile class to support multiple named connections
per profile, enabling multi-source data federation.
"""


from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from dbt.adapters.contracts.connection import Credentials
from dbt.config.profile import Profile
from dbt.exceptions import DbtProfileError, DbtRuntimeError
from dbt_common.dataclass_schema import ValidationError


@dataclass
class DVTProfile(Profile):
    """
    Extended Profile class that supports multiple named connections.

    In addition to the standard dbt Profile fields (profile_name, target_name, threads, credentials),
    DVTProfile adds:
    - connections: Dict of named connections (each with its own Credentials)
    - default_target: The connection name to use for materialization by default

    The 'credentials' field is maintained for backward compatibility and points to the default_target credentials.
    """

    # Additional DVT-specific fields
    outputs: Dict[str, Credentials] = field(default_factory=dict)
    default_target: Optional[str] = None

    def __init__(
        self,
        profile_name: str,
        target_name: str,
        threads: int,
        credentials: Credentials,
        connections: Optional[Dict[str, Credentials]] = None,
        default_target: Optional[str] = None,
    ) -> None:
        """
        Initialize DVT Profile with multi-connection support.

        :param profile_name: Name of the profile
        :param target_name: Name of the target (for backward compatibility)
        :param threads: Number of threads for parallel execution
        :param credentials: Default credentials (for backward compatibility)
        :param connections: Dictionary of named outputs (same as dbt)
        :param default_target: Default output name for materialization
        """
        super().__init__(
            profile_name=profile_name,
            target_name=target_name,
            threads=threads,
            credentials=credentials,
        )

        self.outputs = connections or {}
        self.default_target = default_target

        # If outputs dict is provided but default_target is not, use target_name
        if self.outputs and not self.default_target:
            self.default_target = target_name

        # Ensure backward compatibility: if outputs is empty, populate with single credentials
        if not self.outputs and credentials:
            self.outputs[target_name] = credentials
            self.default_target = target_name

    def get_connection(self, connection_name: Optional[str] = None) -> Credentials:
        """
        Get credentials for a specific output.

        :param connection_name: Name of the output. If None, returns default_target credentials.
        :returns: Credentials for the specified output
        :raises DbtProfileError: If connection_name not found
        """
        name = connection_name or self.default_target

        if not name:
            raise DbtProfileError("No output name specified and no default_target configured")

        if name not in self.outputs:
            available = ", ".join(self.outputs.keys())
            raise DbtProfileError(
                f"Output '{name}' not found in profile '{self.profile_name}'. "
                f"Available outputs: {available}"
            )

        return self.outputs[name]

    def to_profile_info(self, serialize_credentials: bool = False) -> Dict[str, Any]:
        """
        Serialize DVT profile to dict.

        :param serialize_credentials: If True, serialize all credentials to dicts
        :returns: Serialized profile dict
        """
        result = super().to_profile_info(serialize_credentials=serialize_credentials)

        # DVT uses standard dbt format - no need to serialize outputs separately
        # since multi-output support is just for convenience, validation uses single target

        return result

    @staticmethod
    def _parse_connections_from_profile(
        profile: Dict[str, Any], profile_name: str
    ) -> Tuple[Dict[str, Credentials], Optional[str]]:
        """
        Parse multiple outputs from profile configuration.

        DVT uses standard dbt format with 'outputs' key and optional multi-output support:
           outputs:
             postgres_prod:
               type: postgres
               host: prod.example.com
               ...
             snowflake_warehouse:
               type: snowflake
               account: abc123
               ...
           target: postgres_prod

        :param profile: Raw profile dict from YAML
        :param profile_name: Name of the profile
        :returns: Tuple of (outputs dict, default_target name)
        :raises DbtProfileError: If profile format is invalid
        """
        # avoid an import cycle
        from dbt.adapters.factory import load_plugin

        outputs = {}
        default_target = None

        # Check for 'outputs' key (standard dbt format)
        if "outputs" in profile:
            raw_outputs = profile["outputs"]

            if not isinstance(raw_outputs, dict):
                raise DbtProfileError(
                    f"'outputs' in profile '{profile_name}' must be a dictionary"
                )

            # Parse each output
            for output_name, output_data in raw_outputs.items():
                if not isinstance(output_data, dict):
                    raise DbtProfileError(
                        f"Output '{output_name}' in profile '{profile_name}' must be a dictionary"
                    )

                if "type" not in output_data:
                    raise DbtProfileError(
                        f"Output '{output_name}' in profile '{profile_name}' missing required 'type' field"
                    )

                # Parse credentials for this output
                output_data_copy = output_data.copy()
                typename = output_data_copy.pop("type")

                try:
                    cls = load_plugin(typename)
                    data = cls.translate_aliases(output_data_copy)
                    cls.validate(data)
                    credentials = cls.from_dict(data)
                    outputs[output_name] = credentials
                except (DbtRuntimeError, ValidationError) as e:
                    msg = str(e) if isinstance(e, DbtRuntimeError) else e.message
                    raise DbtProfileError(
                        f"Credentials for output '{output_name}' in profile '{profile_name}' invalid: {msg}"
                    ) from e

            # Get default target - use 'target' field (standard dbt)
            # Also support 'default_target' for backward compatibility
            default_target = profile.get("target") or profile.get("default_target")
            if not default_target and outputs:
                # If not specified, use first output as default
                default_target = list(outputs.keys())[0]

            if default_target and default_target not in outputs:
                raise DbtProfileError(
                    f"target '{default_target}' not found in outputs of profile '{profile_name}'"
                )

        return outputs, default_target

    @classmethod
    def from_raw_profile_info(
        cls,
        raw_profile: Dict[str, Any],
        profile_name: str,
        renderer: Any,  # ProfileRenderer
        target_override: Optional[str] = None,
        threads_override: Optional[int] = None,
    ) -> "DVTProfile":
        """
        Create a DVTProfile from raw profile information.

        This method supports both DVT multi-connection format and legacy dbt format.

        :param raw_profile: The profile data for a single profile
        :param profile_name: The profile name used
        :param renderer: The config renderer
        :param target_override: The target to use, if provided on the command line
        :param threads_override: The thread count to use, if provided
        :returns: The new DVTProfile object
        :raises DbtProfileError: If the profile is invalid
        """
        # Check if this is a DVT multi-output profile
        if "outputs" in raw_profile and len(raw_profile.get("outputs", {})) > 0:
            # Parse outputs
            outputs, default_target = cls._parse_connections_from_profile(
                raw_profile, profile_name
            )

            if not outputs:
                raise DbtProfileError(
                    f"Profile '{profile_name}' has 'outputs' key but no valid outputs defined"
                )

            # Get threads
            threads = raw_profile.get("threads", 1)
            if threads_override is not None:
                threads = threads_override

            # Determine target name
            if target_override:
                target_name = target_override
                if target_name not in outputs:
                    raise DbtProfileError(
                        f"Target override '{target_name}' not found in outputs of profile '{profile_name}'"
                    )
                default_target = target_name
            else:
                target_name = default_target or list(outputs.keys())[0]

            # Get default credentials for backward compatibility
            credentials = outputs[target_name]

            profile = cls(
                profile_name=profile_name,
                target_name=target_name,
                threads=threads,
                credentials=credentials,
                connections=outputs,
                default_target=default_target,
            )
            profile.validate()
            return profile

        else:
            # Fall back to legacy dbt format - use parent class implementation
            legacy_profile = Profile.from_raw_profile_info(
                raw_profile=raw_profile,
                profile_name=profile_name,
                renderer=renderer,
                target_override=target_override,
                threads_override=threads_override,
            )

            # Convert to DVTProfile for consistency
            return cls(
                profile_name=legacy_profile.profile_name,
                target_name=legacy_profile.target_name,
                threads=legacy_profile.threads,
                credentials=legacy_profile.credentials,
                connections={legacy_profile.target_name: legacy_profile.credentials},
                default_target=legacy_profile.target_name,
            )

    @classmethod
    def from_raw_profiles(
        cls,
        raw_profiles: Dict[str, Any],
        profile_name: str,
        renderer: Any,  # ProfileRenderer
        target_override: Optional[str] = None,
        threads_override: Optional[int] = None,
    ) -> "DVTProfile":
        """
        Create DVTProfile from raw profiles dict.

        :param raw_profiles: The profile data, from disk as yaml
        :param profile_name: The profile name to use
        :param renderer: The config renderer
        :param target_override: The target to use, if provided
        :param threads_override: The thread count to use, if provided
        :returns: The new DVTProfile object
        """
        from dbt.exceptions import DbtProjectError

        if profile_name not in raw_profiles:
            raise DbtProjectError(f"Could not find profile named '{profile_name}'")

        raw_profile = raw_profiles[profile_name]
        if not raw_profile:
            raise DbtProfileError(f"Profile {profile_name} in profiles.yml is empty")

        return cls.from_raw_profile_info(
            raw_profile=raw_profile,
            profile_name=profile_name,
            renderer=renderer,
            target_override=target_override,
            threads_override=threads_override,
        )

    @classmethod
    def render(
        cls,
        renderer: Any,  # ProfileRenderer
        project_profile_name: Optional[str],
        profile_name_override: Optional[str] = None,
        target_override: Optional[str] = None,
        threads_override: Optional[int] = None,
    ) -> "DVTProfile":
        """
        Render a DVTProfile from disk.

        :param renderer: The config renderer
        :param project_profile_name: The profile name from project
        :param profile_name_override: Profile name override from CLI
        :param target_override: Target override from CLI
        :param threads_override: Threads override from CLI
        :returns: The new DVTProfile object
        """
        from dbt.config.profile import read_profile
        from dbt.flags import get_flags

        flags = get_flags()
        raw_profiles = read_profile(flags.PROFILES_DIR)
        profile_name = cls.pick_profile_name(profile_name_override, project_profile_name)

        return cls.from_raw_profiles(
            raw_profiles=raw_profiles,
            profile_name=profile_name,
            renderer=renderer,
            target_override=target_override,
            threads_override=threads_override,
        )
