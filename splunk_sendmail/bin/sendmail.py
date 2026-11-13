
import shlex
import sys
import traceback
import io

import splunk.Intersplunk

from recipient_manager import resolve_recipients, RecipientError
from email_engine import send_email, EmailDeliveryError


def parse_arguments(arguments):
    """
    Parse command arguments in key=value format.
    """

    try:
        tokens = shlex.split(" ".join(arguments))
    except ValueError as exc:
        raise ValueError(
            "Invalid command arguments: {}".format(exc)
        )

    parsed = {}

    for token in tokens:
        if "=" not in token:
            raise ValueError(
                "Invalid argument '{}'. Expected key=value.".format(token)
            )

        key, value = token.split("=", 1)
        key = key.strip().lower()
        value = value.strip()

        if key not in ("to", "title", "body"):
            raise ValueError(
                "Unsupported argument: {}".format(key)
            )

        if key in parsed:
            raise ValueError(
                "Duplicate argument: {}".format(key)
            )

        parsed[key] = value

    required = ("to", "title", "body")

    for key in required:
        if not parsed.get(key):
            raise ValueError(
                "Missing required argument: {}".format(key)
            )

    return parsed


def main():
    if sys.version_info >= (3, 0):
        input_buf = io.TextIOWrapper(
            sys.stdin.buffer,
            encoding="utf-8",
            errors="backslashreplace"
        )
    else:
        input_buf = sys.stdin

    results, dummy_results, settings = (
        splunk.Intersplunk.getOrganizedResults(input_buf)
    )

    try:
        arguments = parse_arguments(sys.argv[1:])

        recipients = resolve_recipients(
            arguments["to"]
        )

        session_key = settings.get("sessionKey")

        if not session_key:
            raise EmailDeliveryError(
                "Session key was not passed by Splunk."
            )

        send_email(
            session_key=session_key,
            recipients=recipients,
            subject=arguments["title"],
            message=arguments["body"]
        )

        sys.stderr.write(
            "Splunk SendMail: email request submitted successfully. "
            "Recipient count: {}\n".format(len(recipients))
        )

    except (
        ValueError,
        RecipientError,
        EmailDeliveryError
    ) as exc:

        sys.stderr.write(
            "Splunk SendMail ERROR: {}\n".format(exc)
        )

        raise SystemExit(1)

    except Exception:
        sys.stderr.write(
            "Splunk SendMail UNEXPECTED ERROR:\n"
        )
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(1)

    splunk.Intersplunk.outputResults(results)


if __name__ == "__main__":
    main()
