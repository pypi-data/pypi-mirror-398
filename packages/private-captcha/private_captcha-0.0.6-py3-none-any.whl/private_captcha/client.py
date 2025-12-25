"""Private Captcha API client implementation."""

import json
import logging
import time
from http import HTTPStatus
from typing import Optional
from urllib import request
from urllib.error import HTTPError as URLLibHTTPError
from urllib.error import URLError

from .exceptions import (
    APIKeyError,
    RetriableError,
    RetriableHTTPError,
    SolutionError,
    HTTPError,
    VerificationFailedError,
)
from .models import VerifyOutput

log = logging.getLogger(__name__)

GLOBAL_DOMAIN = "api.privatecaptcha.com"
EU_DOMAIN = "api.eu.privatecaptcha.com"
DEFAULT_FORM_FIELD = "private-captcha-solution"
VERSION = "0.0.6"
MIN_BACKOFF_MILLIS = 250
BACKOFF_FACTOR = 2.0
RETRIABLE_STATUSES = {
    HTTPStatus.TOO_MANY_REQUESTS,
    HTTPStatus.INTERNAL_SERVER_ERROR,
    HTTPStatus.BAD_GATEWAY,
    HTTPStatus.SERVICE_UNAVAILABLE,
    HTTPStatus.GATEWAY_TIMEOUT,
    HTTPStatus.REQUEST_TIMEOUT,
    HTTPStatus.TOO_EARLY,  # pylint: disable=no-member
}


class Client:
    """Private Captcha API client."""

    def __init__(
        self,
        api_key: str,
        domain: Optional[str] = None,
        form_field: str = DEFAULT_FORM_FIELD,
        timeout: Optional[float] = None,
    ):
        """
        Initializes the Private Captcha client.

        :param api_key: Your API key.
        :param domain: The API domain to use. Defaults to the global domain.
        :param form_field: The form field name for the solution.
        :param timeout: Request timeout in seconds.
        """
        if not api_key:
            raise APIKeyError("API key is empty")

        if not domain:
            domain = GLOBAL_DOMAIN
        elif domain.startswith("http"):
            domain = domain.lstrip("https://").lstrip("http://")

        self.endpoint = f"https://{domain.rstrip('/')}/verify"
        self.api_key = api_key
        self.form_field = form_field
        self.timeout = timeout

    def _do_verify(self, solution: str, sitekey: str = '') -> tuple[dict, str]:
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "text/plain",
            "User-Agent": "private-captcha-py/" + VERSION,
        }
        if sitekey:
            headers["X-PC-Sitekey"] = sitekey

        req = request.Request(
            self.endpoint,
            data=solution.encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                trace_id = resp.headers.get("X-Trace-ID")
                response_body = resp.read().decode("utf-8")
                response_data = json.loads(response_body)
                return response_data, trace_id
        except URLLibHTTPError as e:
            trace_id = e.headers.get("X-Trace-ID") if e.headers else None

            if e.code in RETRIABLE_STATUSES:
                retry_after = 0
                if e.code == HTTPStatus.TOO_MANY_REQUESTS:
                    retry_after_header = e.headers.get("Retry-After")
                    if retry_after_header:
                        try:
                            retry_after = int(retry_after_header)
                        except (ValueError, TypeError):
                            log.warning(
                                "Invalid Retry-After header: %s", retry_after_header
                            )
                            retry_after = 0

                raise RetriableHTTPError(e.code, retry_after=retry_after, trace_id=trace_id) from e

            raise HTTPError(e.code, trace_id=trace_id) from e
        except (json.JSONDecodeError, URLError) as e:
            # URLError for network issues, JSONDecodeError for malformed responses
            raise RetriableError() from e

    def verify(
        self,
        solution: str,
        sitekey: str = '',
        max_backoff_seconds: int = 10,
        attempts: int = 5,
    ) -> VerifyOutput:
        """
        Verifies a captcha solution.

        :param solution: The captcha solution string.
        :param sitekey: An expected sitekey to verify.
        :param max_backoff_seconds: Maximum backoff time between retries.
        :param attempts: Maximum number of attempts.
        :return: A VerifyOutput object with the verification result.
        :raises PrivateCaptchaError: On non-retriable errors or after all attempts fail.
        """
        if not solution:
            raise SolutionError("solution is empty")

        if attempts <= 0:
            attempts = 5

        if max_backoff_seconds <= 0:
            max_backoff_seconds = 20

        b_max = float(max_backoff_seconds)
        current_backoff = MIN_BACKOFF_MILLIS / 1000.0
        last_err: Optional[Exception] = None
        last_trace_id: Optional[str] = None

        for i in range(attempts):
            if i > 0:
                sleep_duration = current_backoff
                if (
                    isinstance(last_err, RetriableHTTPError)
                    and last_err.retry_after > 0
                ):
                    sleep_duration = max(sleep_duration, float(last_err.retry_after))

                time.sleep(min(sleep_duration, b_max))
                current_backoff = min(b_max, current_backoff * BACKOFF_FACTOR)

            try:
                response_data, trace_id = self._do_verify(solution, sitekey)
                return VerifyOutput.from_dict(
                    response_data, _trace_id=trace_id, _attempt=i + 1
                )
            except RetriableError as e:
                last_err = e
                if isinstance(e, RetriableHTTPError):
                    last_trace_id = e.trace_id
                log.debug("Retriable error on attempt %d of %d: %s", i + 1, attempts, e)
                continue

        log.error("Failed to verify solution after %d attempts.", attempts)
        raise VerificationFailedError(
            f"Failed to verify solution after {attempts} attempts", attempts, trace_id=last_trace_id
        )

    def verify_request(self, form_data: dict) -> None:
        """
        Verifies a captcha solution from form data. Raises SolutionError on failure.

        :param form_data: A dictionary-like object containing form data (e.g., request.POST).
        """
        solution = form_data.get(self.form_field)
        output = self.verify(solution)
        if not output.ok():
            raise SolutionError(f"Captcha verification failed: {output.code}")
