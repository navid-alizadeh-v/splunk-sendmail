
import os
import re


APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECIPIENT_FILE = os.path.join(
    APP_DIR,
    "lookups",
    "Email_bank.txt"
)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
GROUP_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


class RecipientError(Exception):
    pass


def load_groups(file_path=RECIPIENT_FILE):
    """
    Load recipient groups from an INI-like TXT file.
    """

    if not os.path.isfile(file_path):
        raise RecipientError(
            "Recipient file does not exist: {}".format(file_path)
        )

    groups = {}
    current_group = None

    with open(file_path, "r", encoding="utf-8-sig") as file_handle:
        for line_number, raw_line in enumerate(file_handle, 1):
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            if line.startswith("[") and line.endswith("]"):
                group_name = line[1:-1].strip().lower()

                if not GROUP_PATTERN.match(group_name):
                    raise RecipientError(
                        "Invalid group name at line {}".format(line_number)
                    )

                if group_name in groups:
                    raise RecipientError(
                        "Duplicate group '{}' at line {}".format(
                            group_name,
                            line_number
                        )
                    )

                groups[group_name] = []
                current_group = group_name
                continue

            if current_group is None:
                raise RecipientError(
                    "Email address found outside a group at line {}".format(
                        line_number
                    )
                )

            email_address = line.strip()

            if not EMAIL_PATTERN.match(email_address):
                raise RecipientError(
                    "Invalid email address at line {}".format(line_number)
                )

            normalized_email = email_address.lower()

            if normalized_email not in groups[current_group]:
                groups[current_group].append(normalized_email)

    return groups


def resolve_recipients(group_names, file_path=RECIPIENT_FILE):
    """
    Resolve one or more comma-separated group names.
    """

    if not group_names:
        raise RecipientError("The 'to' argument is required.")

    groups = load_groups(file_path)

    requested_groups = [
        name.strip().lower()
        for name in group_names.split(",")
        if name.strip()
    ]

    if not requested_groups:
        raise RecipientError("No recipient groups were specified.")

    recipients = []

    for group_name in requested_groups:
        if not GROUP_PATTERN.match(group_name):
            raise RecipientError(
                "Invalid group name: {}".format(group_name)
            )

        if group_name not in groups:
            raise RecipientError(
                "Unknown recipient group: {}".format(group_name)
            )

        if not groups[group_name]:
            raise RecipientError(
                "Recipient group '{}' has no email addresses.".format(
                    group_name
                )
            )

        for email_address in groups[group_name]:
            if email_address not in recipients:
                recipients.append(email_address)

    if not recipients:
        raise RecipientError("No valid recipients were found.")

    return recipients
