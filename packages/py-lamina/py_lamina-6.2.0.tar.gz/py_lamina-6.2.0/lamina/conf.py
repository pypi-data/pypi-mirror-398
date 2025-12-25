import importlib
import os
import tomllib
from dataclasses import dataclass
from typing import Any, Callable, Dict

HookCallable = Callable[..., Any]


def get_toml_configuration() -> Dict[str, Any]:
    """
    Reads the pyproject.toml file and returns its content as a dictionary.

    Returns:
        A dictionary containing the contents of the pyproject.toml file.
        If the file does not exist or cannot be read, an empty dictionary is returned.
    """
    current_dir = os.getcwd()
    while True:
        if os.path.isfile(os.path.join(current_dir, "pyproject.toml")):
            break
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Reached the root directory
            return {}
        current_dir = parent_dir

    file_path = os.path.join(current_dir, "pyproject.toml")
    try:
        with open(file_path, "rb") as f:
            all_data = tomllib.load(f)
            return all_data.get("tool", {}).get("lamina", {})
    except (FileNotFoundError, tomllib.TOMLDecodeError):
        return {}


@dataclass
class LaminaSettings:
    settings: Dict[str, Any]

    def _get_setting(self, name: str, default: Any = None) -> Any:
        full_name = f"LAMINA_{name.upper()}"
        # First, check environment variables
        value = os.getenv(full_name, None)
        if not value:
            # Then check the settings dictionary
            value = self.settings.get(name, default)

        if "." in str(value) or ":" in str(value):
            module_path = (
                ".".join(value.split(".")[:-1])
                if ":" not in value
                else value.split(":")[0]
            )
            func_name = (
                value.split(".")[-1] if ":" not in value else value.split(":")[1]
            )
            try:
                module = importlib.import_module(module_path)
                value = getattr(module, func_name)
            except (ImportError, AttributeError) as error:
                raise ImportError(
                    f"Could not import '{value}' for setting '{full_name}'"
                ) from error

        return value

    @property
    def LAMINA_PRE_PARSE_CALLBACK(self) -> HookCallable:
        return self._get_setting("pre_parse_callback", default="lamina.hooks.pre_parse")

    @property
    def LAMINA_PRE_EXECUTE_CALLBACK(self) -> HookCallable:
        return self._get_setting(
            "pre_execute_callback", default="lamina.hooks.pre_execute"
        )

    @property
    def LAMINA_POS_EXECUTE_CALLBACK(self) -> HookCallable:
        return self._get_setting(
            "pos_execute_callback", default="lamina.hooks.pos_execute"
        )

    @property
    def LAMINA_PRE_RESPONSE_CALLBACK(self) -> HookCallable:
        return self._get_setting(
            "pre_response_callback", default="lamina.hooks.pre_response"
        )

    @property
    def LAMINA_USE_OBJECT_NAME(self) -> str:
        # Options are: package, module, function
        return self._get_setting("use_object_name", "function")

    @property
    def LAMINA_DEFAULT_AUTH_HEADER_NAME(self) -> str:
        return self._get_setting("default_auth_header_name", "Authorization")

    @property
    def LAMINA_DEFAULT_ERROR_KEY(self) -> str:
        return self._get_setting("default_error_key", "detail")

    @property
    def LAMINA_API_URL(self) -> str | None:
        return self._get_setting("api_url")

    @property
    def LAMINA_DEFAULT_SUCCESS_STATUS_CODE(self) -> int:
        return int(self._get_setting("default_success_status_code", 200))

    @property
    def LAMINA_GENERATE_FIELD_TABLES_IN_DOCS(self):
        return self._get_setting("generate_field_tables_in_docs", True)


# Create a single instance of the settings class
_lamina_settings = LaminaSettings(get_toml_configuration())


def __getattr__(name: str) -> Any:
    """
    Implement PEP 562 __getattr__ to lazily load settings.

    This function is called when an attribute is not found in the module's
    global namespace. It delegates to the _lamina_settings instance.
    """
    return getattr(_lamina_settings, name)
