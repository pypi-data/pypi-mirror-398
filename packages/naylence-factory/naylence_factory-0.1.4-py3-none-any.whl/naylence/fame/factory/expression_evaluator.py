import os
from typing import Any, Optional


class MissingEnvironmentVariableError(Exception):
    """Raised when an environment variable is required but not defined."""

    pass


class ExpressionRecursionError(Exception):
    """Raised when expression evaluation exceeds the maximum recursion depth."""

    pass


class ExpressionEvaluator:
    """
    Pure expression evaluator with no external dependencies.

    Supports expressions like:
    - ${env:VAR:default} - Environment variable with optional default

    Can handle both full-string expressions and partial substitutions within strings.
    Examples:
    - "${env:HOST}" -> "localhost" (full replacement)
    - "${env:HOST}/api/v1" -> "localhost/api/v1" (partial substitution)

    This class only handles the actual evaluation logic.
    Policy decisions about when to evaluate are handled by the caller.
    """

    _max_evaluation_depth = 10
    _expression_start = "${"
    _env_prefix = "env:"

    @classmethod
    def is_expression(cls, value: Any) -> bool:
        """
        Check if a value contains any expressions that can be evaluated.

        Args:
            value: The value to check

        Returns:
            True if the value is a string containing expressions, False otherwise
        """
        if not isinstance(value, str):
            return False

        if cls._env_prefix not in value:
            return False

        return cls._find_next_expression(value, 0) is not None

    @classmethod
    def evaluate(cls, value: Any, target_type: Optional[type] = None) -> Any:
        """
        Evaluate expressions in the given value and optionally convert to target type.

        Args:
            value: The value to evaluate (only strings are processed)
            target_type: Optional target type for scalar conversion (int, float, bool)

        Returns:
            The evaluated value, optionally converted to the target type
        """
        # Only process string values
        if not isinstance(value, str):
            return value

        evaluated = cls._evaluate_string(value, 0)

        # If target type is specified and it's a scalar type, try conversion
        if target_type and target_type in (int, float, bool):
            return cls._convert_to_scalar(evaluated, target_type)

        return evaluated

    @classmethod
    def _evaluate_string(cls, value: str, depth: int) -> str:
        """
        Evaluate all expressions in a string value using substitution.

        Args:
            value: The string value to evaluate

        Returns:
            The string with all expressions substituted

        Raises:
            MissingEnvironmentVariableError: If an environment variable is required
                                           but not defined and no default is provided
        """

        if depth > cls._max_evaluation_depth:
            raise ExpressionRecursionError(
                f"Expression evaluation exceeded the maximum recursion depth: {value}"
            )

        result_parts = []
        index = 0

        while index < len(value):
            expression = cls._find_next_expression(value, index)
            if expression is None:
                result_parts.append(value[index:])
                break

            start, end, var_name, default_value = expression
            if start > index:
                result_parts.append(value[index:start])

            resolved = cls._resolve_environment_variable(
                var_name, default_value, depth
            )
            result_parts.append(resolved)
            index = end + 1

        return "".join(result_parts)

    @classmethod
    def _resolve_environment_variable(
        cls, var_name: str, default_value: Optional[str], depth: int
    ) -> str:
        if var_name in os.environ:
            return os.environ[var_name]

        if default_value is not None:
            return cls._evaluate_default(default_value, depth)

        raise MissingEnvironmentVariableError(
            f"Environment variable '{var_name}' is required but not defined. "
            f"Either set the environment variable or provide a default value in the expression."
        )

    @classmethod
    def _evaluate_default(cls, default_value: str, depth: int) -> str:
        if cls._env_prefix not in default_value:
            return default_value

        return cls._evaluate_string(default_value, depth + 1)

    @classmethod
    def _find_next_expression(
        cls, value: str, start_index: int
    ) -> Optional[tuple[int, int, str, Optional[str]]]:
        search_index = start_index

        while search_index < len(value):
            start = value.find(cls._expression_start, search_index)
            if start == -1:
                return None

            type_start = start + len(cls._expression_start)
            type_separator = value.find(":", type_start)
            if type_separator == -1:
                search_index = start + len(cls._expression_start)
                continue

            expr_type = value[type_start:type_separator]
            if expr_type != "env":
                search_index = start + len(cls._expression_start)
                continue

            index = type_separator + 1
            key_start = index
            while index < len(value):
                char = value[index]
                if char in (":", "}"):
                    break
                index += 1

            if index >= len(value):
                return None

            var_name = value[key_start:index]
            if not var_name:
                search_index = start + len(cls._expression_start)
                continue

            if value[index] == "}":
                return (start, index, var_name, None)

            default_start = index + 1
            level = 1
            index = default_start

            while index < len(value):
                char = value[index]
                next_char = value[index + 1] if index + 1 < len(value) else ""

                if char == "$" and next_char == "{":
                    level += 1
                    index += 2
                    continue

                if char == "}":
                    level -= 1
                    if level == 0:
                        default_value = value[default_start:index]
                        return (start, index, var_name, default_value)

                index += 1

            return None

        return None

    @classmethod
    def _convert_to_scalar(cls, value: str, target_type: type) -> Any:
        """
        Convert a string value to the target scalar type if possible.

        Args:
            value: The string value to convert
            target_type: The target type (int, float, or bool)

        Returns:
            The converted value, or the original string if conversion fails
        """
        try:
            if target_type is bool:
                # Handle boolean conversion
                lower = value.lower()
                if lower in ("true", "1", "yes", "on"):
                    return True
                elif lower in ("false", "0", "no", "off"):
                    return False
                else:
                    # If it doesn't look like a boolean, keep as string
                    return value
            elif target_type is int:
                # Only convert if it looks like an integer
                if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
                    return int(value)
                else:
                    return value
            elif target_type is float:
                # Try to convert to float
                return float(value)
        except ValueError:
            # If conversion fails, return the original string
            pass

        return value
