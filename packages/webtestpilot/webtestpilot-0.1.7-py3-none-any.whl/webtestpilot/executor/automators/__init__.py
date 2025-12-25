import re
import ast
import time
import logging
from copy import deepcopy

from playwright.sync_api import Page, Locator


# -------------------------
# Globals
# -------------------------
logger = logging.getLogger(__name__)
_current_page: Page | None = None
_trace: list[dict] = []
_no_answer: bool = False


def _get_current_page() -> Page:
    global _current_page
    if _current_page is None:
        raise RuntimeError("No active page. Call set_page() first.")
    return _current_page


def _get_som_mapping() -> dict[int, str]:
    global _som_mapping
    if _som_mapping is None:
        raise RuntimeError("No SoM mapping. Get SoM from page first.")
    return _som_mapping


def _set_page(page: Page):
    global _current_page
    _current_page = page


def _set_som_mapping(som_mapping: dict[int, str]):
    global _som_mapping
    _som_mapping = som_mapping


def _set_no_answer(no_answer: bool):
    global _no_answer
    _no_answer = no_answer


def click_by_label(label: int):
    page: Page = _get_current_page()
    som_mapping: dict[int, str] = _get_som_mapping()
    xpath: str = som_mapping.get(int(label), "/html/body")
    locator: Locator = page.locator(f"xpath={xpath}")

    logger.info(
        f"Clicking element with label: [{label}] and xpath: {xpath}"
    )

    box = locator.first.bounding_box()
    x = box["x"] + box["width"] / 2
    y = box["y"] + box["height"] / 2
    
    # Simulate hover and click
    page.mouse.move(x, y)

    try:
        locator.click()
    except:
        page.mouse.click(x, y)


def type(label: int, content: str):
    page: Page = _get_current_page()
    som_mapping: dict[int, str] = _get_som_mapping()
    xpath: str = som_mapping.get(int(label), "/html/body")
    locator: Locator = page.locator(f"xpath={xpath}")

    box = locator.bounding_box()
    x = box["x"] + box["width"] / 2
    y = box["y"] + box["height"] / 2

    try:
        locator.fill(content, force=True)
    except:
        page.mouse.click(x, y)
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        page.keyboard.type(content)


def press(key: str):
    page: Page = _get_current_page()
    page.keyboard.press(key)


def scroll():
    page: Page = _get_current_page()
    page.evaluate("() => {window.scrollBy(0, window.innerHeight);}")


def no_answer():
    _set_no_answer(True)


def wait():
    time.sleep(5)


def finished():
    pass


def filter_python_lines(text: str) -> str:
    kept = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        try:
            ast.parse(line)
            kept.append(line)
        except SyntaxError:
            continue

    return "\n".join(kept)


def execute(code: str, page: Page, som_mapping: dict[int, str]) -> list[dict]:
    """
    Safely execute LLM-generated Python code blocks containing only automation actions.
    Automatically sets the current Playwright Page before execution.
    """
    global _no_answer

    safe_globals = {
        "click_by_label": click_by_label,
        "type": type,
        "press": press,
        "scroll": scroll,
        "wait": wait,
        "no_answer": no_answer,
        "finished": finished,
    }

    # Remove triple backticks and optional 'python' tag
    try:
        _set_page(page)
        _set_som_mapping(som_mapping)
        _set_no_answer(False)

        # Extract content inside a ```python ... ``` block
        match = re.search(r"```python\s*([\s\S]*?)```", code, flags=re.IGNORECASE)
        cleaned_code = match.group(1).strip() if match else filter_python_lines(code)

        exec(cleaned_code, safe_globals, {})
    finally:
        trace = deepcopy(_trace)
        _trace.clear()

    return trace, _no_answer
