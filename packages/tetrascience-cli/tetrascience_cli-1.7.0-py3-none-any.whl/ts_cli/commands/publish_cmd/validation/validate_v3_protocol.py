from typing import Any

from ts_cli.errors.critical_error import CriticalError
from ts_cli.util.emit import emit_error, emit_info, emit_warning

try:
    from ts_protocol_virtual_machine import compiler
    from ts_protocol_virtual_machine.messages import Message
except ImportError:
    compiler = None
    Message = Any


def validate_v3_protocol(filename: str, protocol: dict):
    if compiler is None:
        emit_info(
            "Skipping protocol v3 validation because the 'protocol-validation' extra is not installed"
        )
        return

    def format_message(message: Message):
        path = f"[{message.source_path}] " if message.source_path else ""
        expression = f"$( {message.expression} ) " if message.expression else ""
        return f"{filename} >> {path}{expression}{message.content}"

    def emit_warnings(_, warnings):
        for warning in warnings:
            emit_warning(format_message(warning))

    def emit_warnings_and_errors_and_exit(errors, warnings):
        emit_warnings(None, warnings)
        for error in errors:
            emit_error(format_message(error))
        raise CriticalError("Exiting")

    compiler.protocol_lang.to.pvm(protocol).match(
        emit_warnings,
        emit_warnings_and_errors_and_exit,
    )
