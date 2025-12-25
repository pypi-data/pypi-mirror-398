import logging
import subprocess  # nosec: we need it to invoke binaries from system
from typing import List, Any

logger = logging.getLogger(__name__)


def run_and_log(args: List[str], **kwargs: Any) -> subprocess.CompletedProcess:
    logger.info("Running command:")
    logger.info(" ".join(args))
    if "text" not in kwargs:
        kwargs["text"] = True

    run_res = subprocess.run(args, **kwargs)  # nosec
    logger.info(f"Command executed, exit code: {run_res.returncode}.")
    return run_res


def run_and_handle_error(args: List[str], expected_error_text: str, **kwargs: Any) -> subprocess.CompletedProcess:
    logger.info("Running command:")
    logger.info(" ".join(args))
    if "text" not in kwargs:
        kwargs["text"] = True

    run_res = subprocess.run(args, **kwargs, capture_output=True)  # nosec
    logger.info(run_res.stdout)
    logger.info(f"Command executed, exit code: {run_res.returncode}.")

    if run_res.returncode != 0 and expected_error_text and expected_error_text in run_res.stderr:
        logger.info(f"Found expected error text '{expected_error_text}' in stderr, overriding exit code to 0")
        run_res.returncode = 0

    return run_res
