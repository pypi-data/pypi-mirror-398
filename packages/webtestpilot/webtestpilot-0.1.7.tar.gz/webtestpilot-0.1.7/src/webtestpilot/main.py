import logging
import traceback
from typing import Optional, Callable

from webtestpilot.baml_client.types import Step
from webtestpilot.executor import (
    execute_action,
    verify_postcondition,
    BugReport,
)
from webtestpilot.executor.assertion_api import Session


logger = logging.getLogger(__name__)
Hook = Callable[[BugReport], None]


class WebTestPilot:
    @staticmethod
    def run(
        session: Session,
        steps: list["Step"],
        assertion: bool,
        hooks: Optional[list[Hook]] = None,
    ) -> None:
        """
        Execute a test case on the given Session.

        Params:
            session: The current test session.
            test_input: Description string, a single Step, or list of Steps.
            hooks: Optional list of hooks to trigger (Callables) when a BugReport occurs.
        """
        assert isinstance(steps, list)
        assert all(isinstance(s, Step) for s in steps)

        config = session.config
        hooks = hooks or []

        for step in steps:
            try:
                execute_action(session, step.action, config)
                if assertion and step.expectation:
                    verify_postcondition(
                        session, step.action, step.expectation, config
                    )

            except BugReport as report:
                logger.error(f"Bug reported: {str(report)}")
                for hook in hooks:
                    try:
                        hook(report)
                    except Exception:
                        logger.error("Exception in hook:", traceback.format_exc())
                        raise
                raise report
            except Exception:
                logger.error("Exception in test session:", traceback.format_exc())
                raise
