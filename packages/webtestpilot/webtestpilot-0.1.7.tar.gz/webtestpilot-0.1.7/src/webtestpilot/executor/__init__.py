import io
import base64
import logging
from pathlib import Path

from PIL import Image as PILImage
from baml_py import Image
from baml_py.baml_py import BamlImagePy

import webtestpilot.executor.automators as automator
from webtestpilot.config import Config
from webtestpilot.baml_client.sync_client import b
from webtestpilot.baml_client.types import Feedback
from webtestpilot.executor.assertion_api.session import Session
from webtestpilot.executor.assertion_api import execute_assertion
from webtestpilot.executor.utils import (
    get_screenshot, 
    crop_screenshot, 
    mask_screenshot, 
    propose_som_actions,
    propose_coordinates,
    mark_page,
    unmark_page
)

BASE_DIR = Path(__file__).parent
logger = logging.getLogger(__name__)


class BugReport(Exception):
    def __init__(self, message, screenshots=None, steps=None):
        super().__init__(message)
        self.screenshots = screenshots or []
        self.steps = steps or []


def execute_action(session: Session, action: str, config: Config):
    """
    Executes a natural language action on the current page using a two-step process:
    1. GUI Grounding: Propose coordinates for the target element.
    2. Set-of-Mark (SoM): Identify elements near the proposed coordinates and generate specific code to interact with them.

    Args:
        session (Session): The current browser session containing the page and trace history.
        action (str): The natural language description of the action to perform.
        config (Config): Configuration object for model registries and other settings.

    Raises:
        Exception: If the action fails to execute after retries or encounters a critical error.
    """
    logger.info(f"Action: '{action}'")

    som_options = {"client_registry": config.action_proposer, "collector": session.collector}
    grounding_options = {"client_registry": config.ui_locator, "collector": session.collector}

    page = session.page
    mask_points = []

    for _ in range(3):
        # Step 1: GUI grounding model
        # Capture a fresh screenshot each time to account for masks
        grounding_screenshot = get_screenshot(page)
        for mask_point in mask_points:
            grounding_screenshot = mask_screenshot(grounding_screenshot, mask_point)

        x, y = propose_coordinates(grounding_screenshot, action, grounding_options)

        # Step 2: Set-of-Mark prompt model
        # Generate executable code based on the cropped, marked screenshot
        som_mapping, text_mapping = mark_page(page, x, y)
        cropped_screenshot = crop_screenshot(get_screenshot(page), center=(x, y))
        code = propose_som_actions(cropped_screenshot, action, som_mapping, text_mapping, som_options)
        unmark_page(page)

        try:
            # Execute the generated code
            trace, no_answer = automator.execute(code, page, som_mapping)

            if no_answer: 
                # If the model couldn't determine an answer, record this area to mask
                # in the next iteration to force the model to look elsewhere
                logger.info(f"No answer found at ({x}, {y}). Masking and retrying.")
                mask_points.append((x, y))
                continue
            else:
                # Success: Update session history and state
                session.trace.extend(trace)
                session.page.wait_for_load_state(timeout=0)
                session.capture_state(prev_action=action)
                break

        except Exception as e:
            logger.error(f"Action failed: {e}")
            raise


def verify_postcondition(session: Session, action: str, expectation: str, config: Config):
    logger.info(f"Expectation: {expectation}")

    client_registry = config.assertion_generation
    collector = session.collector
    max_tries = config.max_tries
    history = session.get_history()

    logger.info("Capturing screenshot")
    screenshot = session.page.screenshot(type="png", timeout=0)
    screenshot_b64 = base64.b64encode(screenshot).decode("utf-8")
    screenshot: BamlImagePy = Image.from_base64("image/png", screenshot_b64)

    feedback: list[Feedback] = []
  
    for _ in range(1, max_tries + 1):
        logger.info("Generating assertion")
        response = b.GeneratePostcondition(
            screenshot,
            history,
            action,
            expectation,
            feedback,
            baml_options={"client_registry": client_registry, "collector": collector},
        )
        logger.info(f"Response: {response}")

        logger.info("Executing assertion")
        passed, current_message = execute_assertion(response, session)
        if passed:
            logger.info("Assertion passed")
            return
        else:
            message = current_message
            logger.error(f"Assertion failed: {message}")
            feedback_item = Feedback(response=response, reason=message)
            feedback.append(feedback_item)

    logger.error("Assertion failed after all retries, raising bug report")
    raise BugReport(message)
