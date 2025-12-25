import subprocess
import sys
from typing import Any, Dict, List
from spx_sdk.registry import register_class
from spx_sdk.actions.action import Action
from spx_sdk.components import SpxComponentState
from spx_sdk.diagnostics import trace
from spx_sdk.validation.decorators import definition_schema


@register_class(name="pip_install")
@definition_schema({
    "type": "object",
    "required": ["pip_install"],
    "properties": {
        "pip_install": {
            "description": "Placeholder output reference; typically null when used as a side-effect action.",
            "type": ["string", "null"]
        },
        "packages": {
            "description": "Single package name or a list of packages to install.",
            "oneOf": [
                {"type": "string", "minLength": 1},
                {"type": "array", "items": {"type": "string", "minLength": 1}, "minItems": 1}
            ]
        },
        "requirements": {
            "description": "Path or list of paths to requirements files.",
            "oneOf": [
                {"type": "string", "minLength": 1},
                {"type": "array", "items": {"type": "string", "minLength": 1}, "minItems": 1}
            ]
        },
        "upgrade": {"type": "boolean"},
        "pip_args": {
            "description": "Additional arguments appended to the pip command.",
            "oneOf": [
                {"type": "string"},
                {"type": "array", "items": {"type": "string"}, "minItems": 1}
            ]
        },
        "pip_executable": {
            "type": "string",
            "description": "Override the Python executable used to invoke pip (defaults to sys.executable)."
        },
    },
    "additionalProperties": False,
}, validation_scope="parent")
class PipInstallAction(Action):
    """
    Action that executes `pip install` for declared packages or requirements files.
    Designed as an explicit, opt-in side-effect action to hydrate dependencies before other actions run.
    """

    def _populate(self, definition: Dict[str, Any]) -> None:
        self.packages = self._normalize_sequence(definition.pop("packages", None))
        self.requirements = self._normalize_sequence(definition.pop("requirements", None))
        self.upgrade = bool(definition.pop("upgrade", False))
        self.pip_args = self._normalize_sequence(definition.pop("pip_args", None), allow_scalar=True)
        pip_exec = definition.pop("pip_executable", None)
        if pip_exec is not None and not isinstance(pip_exec, str):
            raise ValueError("pip_executable must be a string path to the Python executable.")
        self.pip_executable = pip_exec or sys.executable
        super()._populate(definition)

    def run(self, *args, **kwargs) -> Any:
        base_result = super().run()
        if base_result is True:
            return True  # Action disabled
        if not (self.packages or self.requirements):
            self.state = SpxComponentState.STOPPED
            return True  # Nothing to install

        cmd = [self.pip_executable, "-m", "pip", "install"]
        if self.upgrade:
            cmd.append("--upgrade")
        cmd.extend(self.packages)
        for req in self.requirements:
            cmd.extend(["-r", req])
        cmd.extend(self.pip_args)

        # Run pip with diagnostics; errors bubble to surface installation failures.
        with trace(self, action="actions.pip_install.install", bubble=True, http_status=500, extra={"cmd": cmd}):
            subprocess.run(cmd, check=True)
        self.state = SpxComponentState.STOPPED
        return True

    def _normalize_sequence(self, value: Any, allow_scalar: bool = True) -> List[str]:
        """
        Normalize optional scalar or list configuration entries to a list of strings.
        """
        if value is None:
            return []
        if isinstance(value, str):
            return [value] if allow_scalar else [value]
        if isinstance(value, list):
            normalized: List[str] = []
            for item in value:
                if not isinstance(item, str):
                    raise ValueError("pip_install action expects strings in list-type fields.")
                normalized.append(item)
            return normalized
        raise ValueError("pip_install action fields must be strings or lists of strings.")
