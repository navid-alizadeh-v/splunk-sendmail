# Splunk SendMail
### Centralized Email Notification Management for Splunk

Splunk SendMail is a lightweight custom search command that centralizes email recipient management for Splunk alerts and searches.

Instead of maintaining recipient addresses independently in hundreds of alert definitions, teams can reference centrally managed recipient groups such as `soc`, `infra`, or `management`. When personnel join, leave, or change responsibilities, administrators update one recipient file rather than editing every alert.

## Why this project?

Consider an organization with 700 scheduled alerts. Many of them notify the same SOC, infrastructure, or management teams.

When an employee joins or leaves the organization, or a team mailbox changes, maintaining recipient lists in every alert becomes repetitive, error-prone, and difficult to audit. A missed update can result in notifications being sent to an outdated mailbox; inconsistent edits can also cause alerts to reach the wrong audience.

Splunk SendMail addresses this operational problem by separating **alert logic** from **recipient administration**:

- Alert searches refer to a group name, not a hard-coded list of addresses.
- Recipient membership is maintained centrally in a plain-text configuration file.
- The custom command resolves the requested groups at execution time.
- The command delegates delivery to Splunk's native `sendemail` command and the SMTP settings already configured in Splunk.

For example, an alert can use `to=soc` today and continue using the same SPL after the SOC distribution list changes.

## Key features

- **Centralized recipient groups:** Maintain groups in one `Email_bank.txt` file.
- **No per-alert recipient maintenance:** Update a group once instead of editing every alert that uses it.
- **No app restart for recipient changes:** The recipient file is loaded when the command runs. Changes to the file are therefore picked up by subsequent executions without restarting Splunk, provided the file is saved and readable by the Splunk service account.
- **Native Splunk email delivery:** Uses Splunk's built-in `sendemail` command and configured SMTP settings. The app does not implement a separate SMTP client or store SMTP credentials.
- **Group-based SPL interface:** Alerts specify group names such as `soc` or `soc,infra`.
- **Recipient de-duplication:** Duplicate addresses are removed within a group and across the requested groups.
- **Input validation:** Group names and email address entries are validated. Malformed entries, unknown groups, empty requested groups, and addresses outside a defined group are rejected.
- **Explicit command risk declaration:** The command is marked as risky in Splunk configuration because it sends email, allowing Splunk's risky-command safeguards to apply.
- **Python 3:** The command is configured to run with Splunk's Python 3 runtime.

## How it works

1. A scheduled alert or ad-hoc search invokes `sendmail` with one or more group names.
2. Splunk starts the custom search command.
3. The command parses and validates its arguments.
4. The recipient manager reads `lookups/Email_bank.txt` and resolves the requested groups.
5. Duplicate recipients are removed.
6. The email engine uses the Splunk session key passed to the command to submit a secondary search through Splunk's authenticated REST interface.
7. That search invokes Splunk's native `sendemail` command.
8. Splunk handles delivery using its configured email/SMTP settings.

```text
Scheduled Alert / SPL
        |
        v
| sendmail to=soc title="..." body="..."
        |
        v
Argument validation
        |
        v
Email_bank.txt  ---> Resolve groups / validate addresses / de-duplicate
        |
        v
Splunk authenticated REST search endpoint
        |
        v
Native Splunk sendemail command
        |
        v
SMTP server configured in Splunk
```

## Repository layout

```text
splunk_sendmail/
├── bin/
│   ├── sendmail.py
│   ├── recipient_manager.py
│   └── email_engine.py
├── default/
│   ├── app.conf
│   └── commands.conf
├── lookups/
│   └── Email_bank.txt
└── metadata/
    └── default.meta
```

The repository also includes deployment, security, usage, and example documentation.

## Requirements

- A Splunk Enterprise Search Head where the app can be installed.
- Splunk configured to send email successfully using its native email settings.
- Python 3 support in the Splunk environment.
- A Splunk account permitted to run searches and the custom command under the organization's Splunk RBAC policy.

This project was developed and tested in a Splunk Enterprise 9.3.0 environment using the embedded Python 3 runtime. Compatibility with other Splunk versions should be validated in a test environment before production deployment.

## Installation

1. Copy the `splunk_sendmail` app directory into:

   ```text
   $SPLUNK_HOME/etc/apps/
   ```

2. Ensure the app files and recipient file are readable by the operating-system account that runs Splunk. Example commands for a typical Linux deployment:

   ```bash
   sudo chown -R splunk:splunk "$SPLUNK_HOME/etc/apps/splunk_sendmail"
   sudo find "$SPLUNK_HOME/etc/apps/splunk_sendmail" -type d -exec chmod 750 {} \;
   sudo find "$SPLUNK_HOME/etc/apps/splunk_sendmail" -type f -exec chmod 640 {} \;
   ```

   Adjust the service account and permissions to match your deployment and security policy. Do not make the recipient file world-readable or world-writable.

3. Configure the recipient groups in:

   ```text
   $SPLUNK_HOME/etc/apps/splunk_sendmail/lookups/Email_bank.txt
   ```

4. Verify that Splunk's native email configuration works independently.

5. Validate the command configuration:

   ```bash
   sudo -u splunk "$SPLUNK_HOME/bin/splunk" btool commands list sendmail --debug
   ```

6. Run a controlled test search using a test-only recipient group.

A restart may be required when first installing or changing app configuration files, depending on the deployment and how the app is distributed. **Changing only `Email_bank.txt` does not require a Splunk restart**: the file is read at command execution time.

See [Deployment Guide](docs/INSTALLATION.md) for the full procedure.

## Recipient file format

`lookups/Email_bank.txt` uses a simple INI-like format:

```ini
# One group per section; one address per line.

[soc]
soc1@example.com
soc2@example.com

[infra]
admin1@example.com
admin2@example.com

[management]
manager@example.com
```

Rules:

- Group names use letters, numbers, underscores, dots, or hyphens.
- Group names are treated case-insensitively.
- Each address must be inside a group.
- Blank lines and lines beginning with `#` are ignored.
- Duplicate addresses in a group are ignored.
- A requested group must exist and contain at least one address.
- The command accepts group names, not arbitrary recipient addresses.

Do not commit real employee addresses, internal distribution lists, or other organization-specific recipient data to a public repository. Use the sanitized example file as a template.

## SPL usage examples

### Send to one group

```spl
| makeresults
| sendmail to=soc title="SOC Notification Test" body="This is a test notification."
```

### Send to multiple groups

```spl
| makeresults
| sendmail to=soc,infra title="Infrastructure Alert" body="An infrastructure event requires investigation."
```

### Use in a scheduled alert

```spl
index=security sourcetype=your_security_source
| where severity="high"
| stats count by host, signature
| sendmail to=soc title="High Severity Security Alert" body="A high-severity event was detected. Review the alert results in Splunk."
```

### Notify a management group

```spl
| makeresults
| sendmail to=management title="Daily Security Summary" body="The daily security summary is ready for review."
```

### Reuse the same group in many alerts

Each alert can reference the same stable group name:

```spl
... | sendmail to=soc title="Alert A" body="..."
```

If SOC membership changes, update only the `[soc]` section in `Email_bank.txt`. The next command execution uses the updated membership.

For additional examples and operational notes, see [Usage Guide](docs/USAGE.md).

## Security considerations

Splunk SendMail is designed to reduce hard-coded recipient sprawl, but it does not replace organizational access controls.

- The command accepts group identifiers and resolves addresses from the managed file; users cannot specify arbitrary email addresses through the documented `to` argument.
- Administrators should restrict who can modify `Email_bank.txt` at the operating-system level.
- Restrict who can install or modify the app and its Python code.
- Apply Splunk RBAC so only authorized users can run searches and use this email-sending command.
- The command is configured with `is_risky = true` because sending email is a side effect.
- The app does not store SMTP passwords. It relies on Splunk's existing email configuration and the session key provided by Splunk for its REST request.
- The app's validation is not a substitute for an approved recipient-domain policy. If your organization requires strict domain restrictions, enforce them through the appropriate Splunk mail settings and/or add an explicit domain allowlist to the application and test it.
- Use a dedicated test group and test mailbox before enabling production alerts.
- Avoid placing confidential information in email subjects or bodies unless the organization's email and data-handling policies permit it.

See [Security Guide](docs/SECURITY.md).

## Limitations and operational notes

- The app delegates sending to Splunk's native `sendemail`; it does not independently guarantee final delivery to a recipient's inbox.
- A successful command execution indicates that the request was submitted without a detected REST/search error. Confirm delivery through a test mailbox and monitor Splunk's relevant logs and mail infrastructure.
- The current implementation uses a simple line-oriented recipient file. It is not a full identity-management or directory-synchronization integration.
- Changes to the recipient file are read on subsequent command executions; an execution already in progress is not dynamically reconfigured.
- Validate compatibility, permissions, SMTP behavior, and RBAC in a non-production environment before rollout.

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE).
