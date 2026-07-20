"""Read-only inspection helpers for an open FORScan window."""

from dataclasses import dataclass


FORSCAN_LOG_MARKERS = ("vehicle:", "found module:", "dtcs in ")


class ForscanReaderError(RuntimeError):
    """Base error for FORScan window inspection."""


class ForscanNotFoundError(ForscanReaderError):
    """Raised when no open FORScan window can be found."""


class ForscanDependencyError(ForscanReaderError):
    """Raised when the Windows inspection dependency is unavailable."""


@dataclass
class ControlInfo:
    """Safe diagnostic information exposed by one Windows control."""

    index: int
    control_type: str
    class_name: str
    automation_id: str
    name: str
    text: str

    @property
    def contains_log_data(self):
        return looks_like_forscan_log(self.text)


@dataclass
class ForscanInspection:
    """Read-only snapshot of one FORScan window's exposed controls."""

    backend: str
    window_title: str
    controls: list

    @property
    def log_candidates(self):
        return [control for control in self.controls if control.contains_log_data]


def is_forscan_window_title(title):
    """Return True for a likely FORScan top-level window title."""
    normalized = (title or "").strip().casefold()
    return "forscan" in normalized and "obd-insight" not in normalized


def looks_like_forscan_log(text):
    """Return True when exposed text contains a useful FORScan Log marker."""
    normalized = (text or "").casefold()
    return any(marker in normalized for marker in FORSCAN_LOG_MARKERS)


def inspect_open_forscan(backend="uia", max_controls=250):
    """Inspect controls exposed by an open FORScan window without clicking it."""
    Desktop = _load_desktop()
    desktop = Desktop(backend=backend)
    windows = [
        window
        for window in desktop.windows()
        if is_forscan_window_title(_safe_control_text(window))
    ]
    if not windows:
        raise ForscanNotFoundError(
            f"No open FORScan window was found with the {backend!r} backend."
        )

    window = windows[0]
    window_title = _safe_control_text(window) or "FORScan"
    descendants = window.descendants()
    controls = []

    for index, control in enumerate(descendants[:max_controls], start=1):
        element = getattr(control, "element_info", None)
        controls.append(
            ControlInfo(
                index=index,
                control_type=_safe_attribute(element, "control_type"),
                class_name=_safe_attribute(element, "class_name"),
                automation_id=_safe_attribute(element, "automation_id"),
                name=_safe_attribute(element, "name"),
                text=_extract_control_text(control),
            )
        )

    return ForscanInspection(
        backend=backend,
        window_title=window_title,
        controls=controls,
    )


def _load_desktop():
    try:
        from pywinauto import Desktop
    except ImportError as error:
        raise ForscanDependencyError(
            "pywinauto is not installed. Run: pip install -r requirements.txt"
        ) from error
    return Desktop


def _extract_control_text(control):
    values = []

    window_text = _safe_call(control, "window_text")
    if window_text:
        values.append(window_text)

    texts = _safe_call(control, "texts")
    if isinstance(texts, (list, tuple)):
        values.extend(text for text in texts if isinstance(text, str) and text)

    legacy_properties = _safe_call(control, "legacy_properties")
    if isinstance(legacy_properties, dict):
        legacy_value = legacy_properties.get("Value")
        if legacy_value:
            values.append(str(legacy_value))

    unique_values = []
    for value in values:
        cleaned = str(value).strip()
        if cleaned and cleaned not in unique_values:
            unique_values.append(cleaned)

    return "\n".join(unique_values)


def _safe_control_text(control):
    return _safe_call(control, "window_text") or ""


def _safe_call(value, method_name):
    try:
        method = getattr(value, method_name, None)
        return method() if method else None
    except Exception:
        return None


def _safe_attribute(value, attribute_name):
    try:
        return str(getattr(value, attribute_name, "") or "")
    except Exception:
        return ""
