
import json

from splunk.rest import simpleRequest


class EmailDeliveryError(Exception):
    pass


def _build_spl_string(value):
    """
    Safely encode a Python string as an SPL double-quoted string.
    """

    return json.dumps(str(value), ensure_ascii=False)


def _build_search(recipients, subject, message):
    """
    Build a secondary search that delegates delivery to native sendemail.
    """

    recipient_string = ",".join(recipients)

    search = (
        "| makeresults "
        "| sendemail "
        "to={} "
        "subject={} "
        "message={}"
    ).format(
        _build_spl_string(recipient_string),
        _build_spl_string(subject),
        _build_spl_string(message)
    )

    return search


def _check_response(response_body):
    """
    Detect error messages returned by the REST export endpoint.
    """

    if isinstance(response_body, bytes):
        response_body = response_body.decode(
            "utf-8",
            errors="replace"
        )

    if not response_body:
        return

    for line in response_body.splitlines():
        line = line.strip()

        if not line:
            continue

        try:
            item = json.loads(line)
        except (ValueError, TypeError):
            continue

        messages = item.get("messages", [])

        for message in messages:
            message_type = str(message.get("type", "")).upper()

            if message_type in ("ERROR", "FATAL"):
                raise EmailDeliveryError(
                    message.get("text", "Splunk search returned an error.")
                )


def send_email(session_key, recipients, subject, message):
    """
    Execute native Splunk sendemail using an authenticated REST request.

    The SMTP configuration remains managed by Splunk.
    """

    if not session_key:
        raise EmailDeliveryError(
            "Splunk session key is unavailable."
        )

    if not recipients:
        raise EmailDeliveryError(
            "Recipient list is empty."
        )

    search = _build_search(
        recipients,
        subject,
        message
    )

    try:
        headers, response_body = simpleRequest(
            "/services/search/jobs/export",
            method="POST",
            postargs={
                "search": search,
                "output_mode": "json"
            },
            sessionKey=session_key,
            timeout=120
        )

    except Exception as exc:
        raise EmailDeliveryError(
            "Unable to execute native Splunk sendemail: {}".format(exc)
        )

    _check_response(response_body)

    return True
