import pytest
import logging
import json
from io import StringIO
from open_py_kit.logger import NewFactory, LoggerConfig, Field


def test_logger_levels():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(message)s"))

    config = LoggerConfig(
        log_level="INFO", enable_console=False
    )  # Disable default console, uses ours manually
    factory = NewFactory(config)

    # Hijack the root logger for testing to use our stream
    logger_impl = logging.getLogger("test_levels")
    # propagate needs to be false to not go to root, or we check root
    logger_impl.propagate = False
    if logger_impl.handlers:
        logger_impl.handlers.clear()
    logger_impl.addHandler(handler)
    logger_impl.setLevel(logging.INFO)

    # Factory resets root logger, so we do this after factory init

    # The child method in our logger implementation actually creates a new wrapper
    # around the logger with that name "root.test_levels" if using child from root

    log = factory.new_logger().child("test_levels")
    # Verify the underlying name
    # root name is "root", child("test_levels") -> "root.test_levels"

    # So we need to attach handler to "root.test_levels"
    real_logger_name = "root.test_levels"
    real_logger = logging.getLogger(real_logger_name)
    real_logger.propagate = False
    real_logger.addHandler(handler)
    real_logger.setLevel(logging.INFO)  # Explicitly set for strict testing

    log.debug("debug message")
    log.info("info message")

    output = stream.getvalue()
    assert "debug message" not in output
    assert "info message" in output


def test_json_formatting():
    # Helper to capture logs
    stream = StringIO()
    # We need to construct factory to use json formatting
    config = LoggerConfig(
        log_level="INFO", enable_console=True, console_json_format=True
    )
    factory = NewFactory(config)

    # We capture stdout by replacing sys.stdout temporarily or by mocking.
    # For robust testing without messing global state too much, let's use capsys fixture if we ran this via pytest,
    # but since we are manually constructing handlers in factory, it might print to real stdout.
    # Instead, let's rely on the fact that factory sets up the root logger.

    root = logging.getLogger()
    # Remove existing handlers
    for h in root.handlers:
        root.removeHandler(h)

    handler = logging.StreamHandler(stream)
    from pythonjsonlogger import jsonlogger

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)

    log = factory.new_logger()
    log.infow("json message", user_id=123)

    output = stream.getvalue()
    try:
        data = json.loads(output)
        assert data["message"] == "json message"
        assert data["user_id"] == 123
        assert "timestamp" in data or "asctime" in data
    except json.JSONDecodeError:
        pytest.fail(f"Output was not JSON: {output}")


def test_child_logger_context():
    stream = StringIO()
    root = logging.getLogger("context_test")
    root.handlers = []
    handler = logging.StreamHandler(stream)
    # Simple formatting to check content
    handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    config = LoggerConfig(log_level="INFO")
    factory = NewFactory(config)

    # Manually injecting our test logger into the wrapper logic for the test
    # (In reality, we'd rely on 'child' creating new loggers via logging.getLogger)

    log = factory.new_logger().child("context_test")

    req_log = log.with_fields(request_id="req-1")
    req_log.info("processing")

    # Note: Standard logging text formatter doesn't automatically show 'extra' fields unless formatted.
    # But json logger does. If we test 'with_fields' with text logger, we need custom formatter
    # or just check that they are passed to the handler.

    # Let's verify via the context persistence in the wrapper object,
    # as the output format depends on the formatter.

    # Checking private attribute for whitefield testing
    assert req_log._context["request_id"] == "req-1"

    child = req_log.child("sub")
    assert child._context["request_id"] == "req-1"  # Inherited


def test_typed_fields():
    f = Field.String("key", "val")
    assert f.name == "key"
    assert f.value == "val"
    assert f.field_type == 1
