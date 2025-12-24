import abc
import inspect
import logging
import os
from pathlib import Path
from typing import Any

from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from pydantic_settings.sources import PydanticBaseEnvSettingsSource


class AppNames:
    """
    A convenience class to normalize application names
    based on a prefix and optional suffix.
    """

    def __init__(self, prefix: str, suffix: str = ""):
        self._prefix_lower = prefix.strip().lower()

        self._has_suffix = len(suffix) > 0
        self._suffix_lower = suffix.strip().lower()

        self._name_lower = f"{self._prefix_lower}app"
        if self._has_suffix:
            self._name_lower = f"{self._name_lower}{self._suffix_lower}"

        self._name_upper = self._name_lower.upper()

        self._name_camel = "app" if len(prefix) == 0 else f"{self._prefix_lower}App"
        if self._has_suffix:
            self._name_camel = f"{self._name_camel}{self._suffix_lower.capitalize()}"

        self._name_camel_upper = f"{self._prefix_lower.capitalize()}App"
        if self._has_suffix:
            self._name_camel_upper = f"{self._name_camel_upper}{self._suffix_lower.capitalize()}"

        if self._has_suffix:
            self._env_prefix = f"{self._prefix_lower.upper()}APP_{self._suffix_lower.upper()}"
        else:
            self._env_prefix = f"{self._prefix_lower.upper()}APP"

    @property
    def name_lower(self) -> str:
        return self._name_lower

    @property
    def name_upper(self) -> str:
        return self._name_upper

    @property
    def name_camel(self) -> str:
        return self._name_camel

    @property
    def name_camel_upper(self) -> str:
        return self._name_camel_upper

    @property
    def env_prefix(self) -> str:
        return self._env_prefix

    @property
    def prefix_lower(self) -> str:
        return self._prefix_lower

    @property
    def has_suffix(self) -> bool:
        return self._has_suffix

    @property
    def suffix_lower(self) -> str | None:
        if self.has_suffix is False:
            return None

        return self._suffix_lower


class AppPorts:
    """
    A wrapper around application port information
    """

    def __init__(self, default_port: int):
        self._default_port = default_port

    @property
    def port(self) -> int:
        return self._default_port


class DictSettingsSource(PydanticBaseEnvSettingsSource):
    _logger = logging.getLogger("apppy.env.DictSettingsSource")

    def __init__(
        self,
        settings_cls: type[BaseSettings],
        env_prefix: str,
        d: dict | None,
    ) -> None:
        super().__init__(
            settings_cls,
            case_sensitive=False,
            env_prefix=env_prefix,
        )
        self._dict: dict | None = d

    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        # See implementation in EnvSettingsSource
        dict_val: str | None = None
        for field_key, env_name, value_is_complex in self._extract_field_info(field, field_name):  # noqa: B007
            # In some cases (e.g. Env object with no overrides)
            # the central dictionary will be None so we'll just
            # return with the field information
            if self._dict is None:
                # Because we break here, we're technically
                # returning the first field information
                break

            dict_val = self._dict.get(env_name.upper())
            if dict_val is not None:
                break

            dict_val = self._dict.get(env_name.lower())
            if dict_val is not None:
                break

            # Attempt a lookup by the field key so that we
            # accept that as well (i.e. the Robustness Principle)
            dict_val = self._dict.get(field_key)
            if dict_val is not None:
                break

        return dict_val, field_key, value_is_complex


##### ##### ##### Environment ##### ##### #####
# An environment represents the external space
# in which an application is executing.


class Env(abc.ABC):
    _logger = logging.getLogger("apppy.env.Env")

    def __init__(self, prefix: str, name: str, overrides: dict | None = None) -> None:
        self.prefix: str = prefix
        self.name: str = name
        self.overrides: dict | None = overrides

    @abc.abstractmethod
    def exists(self) -> bool:
        return False

    @property
    def is_ci(self) -> bool:
        return self.name.startswith("ci") or self.name.endswith("ci")

    @property
    def is_production(self) -> bool:
        return self.name.find("prod") > -1

    @property
    def is_test(self) -> bool:
        return self.name.startswith("test") or self.name.endswith("test")

    @property
    def on_github_actions(self) -> bool:
        return os.getenv("GITHUB_ACTIONS", "").lower() == "true"

    @property
    @abc.abstractmethod
    def settings_config(self) -> SettingsConfigDict:
        pass

    @abc.abstractmethod
    def settings_sources(
        self,
        env_prefix: str,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        pass

    @staticmethod
    def load(prefix: str = "APP", name: str | None = None, overrides: dict | None = None) -> "Env":
        logger = logging.getLogger("apppy.env.Env.load")
        logger.info(
            "Loading environment",
            extra={"provided_prefix": prefix, "provided_name": name, "overrides": overrides},
        )
        env_prefix = prefix.strip().upper()
        if len(env_prefix) == 0:
            logger.critical(
                "Empty env prefix found. This will lead to problems in loading the app configuration values",  # noqa: E501
            )
            raise SystemExit(1)

        env_name = Env._resolve_env_name(env_prefix=env_prefix, env_name=name, logger=logger)

        file_env = FileEnv(prefix=env_prefix, name=env_name, overrides=overrides)
        if file_env.exists():
            logger.info(
                "Using environment found in file",
                extra={"env_file": file_env.env_file, "secrets_dir": file_env.secrets_dir},
            )
            return file_env

        vars_env = VarsEnv(prefix=env_prefix, name=env_name, overrides=overrides)
        if vars_env.exists():
            logger.info(
                "Using environment found in environment variables",
                extra={"env_prefix": env_prefix, "secrets_dir": vars_env.secrets_dir},
            )
            return vars_env

        logger.critical(
            "No environment found!", extra={"env_prefix": env_prefix, "env_name": env_name}
        )
        raise SystemExit(1)

    @staticmethod
    def _resolve_env_name(env_prefix: str, env_name: str | None, logger: logging.Logger) -> str:
        if env_name is not None:
            logger.debug("Received environment name directly", extra={"env_name": env_name})
            return env_name

        env_key = f"{env_prefix}_ENV"
        env_name = os.getenv(env_key)
        if env_name is not None and len(env_name) > 0:
            logger.debug(
                "Found environment name in environment variable",
                extra={"env_key": env_key, "env_name": env_name},
            )
            return env_name
        else:
            logger.critical(
                "Failed to find environment name in environment variables",
                extra={"env_key": env_key},
            )
            raise SystemExit(1)

    @staticmethod
    def find_env_file(env: "Env", logger: logging.Logger) -> Path | None:
        # Never use file-based configuration in production(-like) envs.
        # Instead, these environments should be loaded through environment
        # variables
        if env.is_production:
            logger.info("Skipping env file for production environment")
            return None
        elif env.on_github_actions:
            logger.info("Skipping env file for Github Actions")
            return None

        search_roots = Env._load_search_roots(env, logger)
        if search_roots is None:
            return None

        if env.is_ci or env.is_test:
            for base in search_roots:
                # If we're here, we're not on Github Actions so default
                # to a local configuration for CI
                ci_env_file = (base / ".github" / "ci" / ".env.local").resolve()
                if ci_env_file.is_file():
                    logger.info(
                        "A CI/Test env file was found; it will be INCLUDED "
                        "in settings configuration.",
                        extra={"ci_env_file": ci_env_file},
                    )
                    return ci_env_file
        else:
            # Non-CI: look for application-local .secrets/<env.name> up the tree
            for base in search_roots:
                candidate = (base / f".env.{env.name}").resolve()
                if candidate.is_file():
                    logger.info(
                        "An env file exists for environment; it will be "
                        "INCLUDED in settings configuration.",
                        extra={"env_name": env.name, "candidate": candidate},
                    )
                    return candidate

        logger.info(
            "No env file exists for environment. It will be SKIPPED in settings configuration.",
            extra={"env_name": env.name},
        )
        return None

    @staticmethod
    def find_secrets_dir(env: "Env", logger: logging.Logger) -> Path | None:
        """
        Search upward from the *caller*'s file for either:
          - CI/TEST:   <ancestor>/.github/ci/secrets
          - otherwise: <ancestor>/.secrets/<env.name>

        Returns the resolved Path if found, else None.
        """
        # Never use file-based configuration in production(-like) envs.
        # Instead, these environments should be loaded through environment
        # variables
        if env.is_production:
            logger.info("Skipping secrets directory for production environment")
            return None
        elif env.on_github_actions:
            logger.info("Skipping secrets directory for Github Actions")
            return None

        search_roots = Env._load_search_roots(env, logger)
        if search_roots is None:
            return None

        # CI/TEST: prefer .github/ci/secrets anywhere up the tree (usually repo root)
        if env.is_ci or env.is_test:
            for base in search_roots:
                # If we're here, we're not on Github Actions so default
                # to a local configuration for CI
                ci_dir = (base / ".github" / "ci" / "secrets" / "local").resolve()
                if ci_dir.is_dir():
                    logger.info(
                        "A CI/Test secrets directory was found; it will be INCLUDED "
                        "in settings configuration.",
                        extra={"ci_dir": ci_dir},
                    )
                    return ci_dir
        else:
            # Non-CI: look for application-local .secrets/<env.name> up the tree
            for base in search_roots:
                candidate = (base / ".secrets" / env.name).resolve()
                if candidate.is_dir():
                    logger.info(
                        "A secrets directory exists for environment; it will be "
                        "INCLUDED in settings configuration.",
                        extra={"env_name": env.name, "candidate": candidate},
                    )
                    return candidate

        logger.info(
            "No secrets directory exists for environment. It will be SKIPPED in settings configuration.",  # noqa: E501
            extra={"env_name": env.name},
        )
        return None

    @staticmethod
    def _load_search_roots(env: "Env", logger: logging.Logger) -> list[Path] | None:
        # Never use file-based configuration in production(-like) envs.
        if env.is_production:
            logger.info("Skipping environment directory tree analysis for production environment")
            return None

        # Start from the callsite's directory; fall back to CWD if inspection fails.
        try:
            call_stack = inspect.stack()
            call_file = next(
                Path(frame.filename).resolve()
                for frame in call_stack
                # Skip to the first frame outside of the package
                if (
                    frame.filename.find("/apppy/app/") == -1
                    and frame.filename.find("/apppy/env/") == -1
                )
                or
                # or, as a special case, allow the package to run tests
                (frame.filename.find("/apppy/env") > -1 and frame.filename.endswith("_test.py"))
            )
            start_dir = call_file.parent
        except Exception:
            logger.warning(
                "Exception encountered while loading environment directory tree. "
                + "Defaulting to current working directory",
                exc_info=True,
                extra={"cwd": Path.cwd()},
            )
            start_dir = Path.cwd()

        # Walk upward: start_dir, then its parents up to filesystem root.
        search_roots = [start_dir, *start_dir.parents]
        return search_roots


class DictEnv(Env):
    _logger = logging.getLogger("apppy.env.DictEnv")

    def __init__(self, prefix: str, name: str, d: dict) -> None:
        super().__init__(prefix=prefix, name=name, overrides=None)
        self._dict: dict = d
        # Ensure that the env name is available under
        # the env key (FileEnv and VarsEnv naturally have this construct)
        self._dict["env"] = name

    def __hash__(self):
        # Define a hash function here in order
        # to cache the same envs used in testing
        return hash(frozenset(self._dict.items()))

    def exists(self) -> bool:
        return True

    @property
    def settings_config(self) -> SettingsConfigDict:
        return SettingsConfigDict(
            env_prefix=self.prefix,
            # A DictEnv is only used in narrow testing flows in which
            # secrets should not be necessary so we will force that
            # to be None
            secrets_dir=None,
        )

    def settings_sources(
        self,
        env_prefix: str,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            DictSettingsSource(settings_cls, env_prefix, self._dict),
            file_secret_settings,
        )


class FileEnv(Env):
    _logger = logging.getLogger("apppy.env.FileEnv")

    def __init__(self, prefix: str, name: str, overrides: dict | None = None) -> None:
        super().__init__(prefix=prefix, name=name, overrides=overrides)
        self._secrets_dir = Env.find_secrets_dir(self, self._logger)
        self.env_file: Path | None = Env.find_env_file(self, self._logger)

    def exists(self) -> bool:
        self._logger.info("Checking for FileEnv existence", extra={"env_file": self.env_file})
        return self.env_file is not None and self.env_file.exists()

    @property
    def secrets_dir(self) -> Path | None:
        return self._secrets_dir

    @property
    def settings_config(self) -> SettingsConfigDict:
        return SettingsConfigDict(
            env_file=self.env_file,
            env_prefix=self.prefix,
            secrets_dir=self._secrets_dir,
        )

    def settings_sources(
        self,
        env_prefix: str,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            # Put overrides here so they take precedence over
            # all other settings
            DictSettingsSource(settings_cls, env_prefix, self.overrides),
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


class VarsEnv(Env):
    _logger = logging.getLogger("apppy.env.VarsEnv")

    def __init__(self, prefix: str, name: str, overrides: dict | None = None) -> None:
        super().__init__(prefix=prefix, name=name, overrides=overrides)
        self._secrets_dir = Env.find_secrets_dir(self, self._logger)

    def exists(self) -> bool:
        env_key = f"{self.prefix}_ENV"
        env_name = os.getenv(env_key)
        self._logger.info(
            "Checking for VarsEnv existence", extra={"env_key": env_key, "env_name": env_name}
        )
        return env_name is not None and (
            env_name == self.name or (self.is_test and env_name == "ci")
        )

    @property
    def secrets_dir(self) -> Path | None:
        return self._secrets_dir

    @property
    def settings_config(self) -> SettingsConfigDict:
        return SettingsConfigDict(
            env_prefix=self.prefix,
            secrets_dir=self._secrets_dir,
        )

    def settings_sources(
        self,
        env_prefix: str,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            # Put overrides here so they take precedence over
            # all other settings
            DictSettingsSource(settings_cls, env_prefix, self.overrides),
            init_settings,
            env_settings,
            file_secret_settings,
        )


##### ##### ##### Environment Settings ##### ##### #####


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
    )

    def __init__(self, env: Env, domain_prefix: str | None = None) -> None:
        super().__init__(
            _env_prefix=(
                f"{env.settings_config.get('env_prefix')}_{domain_prefix}_"
                if domain_prefix is not None
                else f"{env.settings_config.get('env_prefix')}_"
            ),
            # Always make the configuration case insensitive to allow for true env var keys
            # e.g. APP_DOMAIN_KEY
            # _case_sensitive=env.settings_config.get("case_sensitive"),
            _case_sensitive=False,
            _nested_model_default_partial_update=env.settings_config.get(
                "nested_model_default_partial_update"
            ),
            _env_file=env.settings_config.get("env_file"),
            _env_file_encoding=env.settings_config.get("env_file_encoding"),
            _env_ignore_empty=env.settings_config.get("env_ignore_empty"),
            _env_nested_delimiter=env.settings_config.get("env_nested_delimiter"),
            _env_parse_none_str=env.settings_config.get("env_parse_none_str"),
            _env_parse_enums=env.settings_config.get("env_parse_enums"),
            # _cli_prog_name: str | None = None,
            # _cli_parse_args: bool | list[str] | tuple[str, ...] | None = None,
            # _cli_settings_source: CliSettingsSource[Any] | None = None,
            # _cli_parse_none_str: str | None = None,
            # _cli_hide_none_type: bool | None = None,
            # _cli_avoid_json: bool | None = None,
            # _cli_enforce_required: bool | None = None,
            # _cli_use_class_docs_for_groups: bool | None = None,
            # _cli_exit_on_error: bool | None = None,
            # _cli_prefix: str | None = None,
            # _cli_flag_prefix_char: str | None = None,
            # _cli_implicit_flags: bool | None = None,
            # _cli_ignore_unknown_args: bool | None = None,
            _secrets_dir=env.settings_config.get("secrets_dir"),
            values=env,
        )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        env = init_settings.init_kwargs["values"]  # type: ignore
        env_prefix = env_settings.env_prefix  # type: ignore
        return env.settings_sources(
            env_prefix,
            settings_cls,
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )
