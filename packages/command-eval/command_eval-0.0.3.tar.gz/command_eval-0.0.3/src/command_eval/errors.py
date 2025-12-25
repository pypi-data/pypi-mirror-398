"""command_eval/errors.py - Custom exception definitions."""


class CommandEvalError(Exception):
    """Base exception class for command_eval."""

    pass


class DomainError(CommandEvalError):
    """Domain layer exception."""

    pass


class ValidationError(DomainError):
    """Validation error."""

    pass


class InvalidStateTransitionError(DomainError):
    """Invalid state transition error."""

    def __init__(self, current_state: str, target_state: str) -> None:
        self.current_state = current_state
        self.target_state = target_state
        super().__init__(
            f"Invalid state transition: {current_state} -> {target_state}"
        )


class InfrastructureError(CommandEvalError):
    """Infrastructure layer exception."""

    pass


class DataLoaderError(InfrastructureError):
    """Data loading error."""

    pass


class UnsupportedFileFormatError(DataLoaderError):
    """Unsupported file format error."""

    def __init__(self, file_path: str, supported: tuple[str, ...]) -> None:
        self.file_path = file_path
        self.supported = supported
        super().__init__(
            f"Unsupported file format: {file_path}. "
            f"Supported formats: {', '.join(supported)}"
        )


class ExecutionError(InfrastructureError):
    """Command execution error."""

    pass


class ProcessTimeoutError(ExecutionError):
    """Process timeout error."""

    def __init__(self, timeout_ms: int, command: str) -> None:
        self.timeout_ms = timeout_ms
        self.command = command
        super().__init__(f"Process timed out after {timeout_ms}ms: {command}")


class OutputFileNotFoundError(ExecutionError):
    """Output file not found error."""

    def __init__(self, output_file: str) -> None:
        self.output_file = output_file
        super().__init__(f"Output file not found: {output_file}")


class EvaluationError(InfrastructureError):
    """Evaluation execution error."""

    pass


class UnsupportedMetricError(EvaluationError):
    """Unsupported metric error."""

    def __init__(self, metric_type: str, sdk_name: str) -> None:
        self.metric_type = metric_type
        self.sdk_name = sdk_name
        super().__init__(
            f"Metric '{metric_type}' is not supported by {sdk_name}"
        )
