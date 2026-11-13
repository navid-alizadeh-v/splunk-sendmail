# Security Design and Operational Controls

Splunk SendMail centralizes recipient administration and applies input validation. It should be deployed as a controlled administrative component, not treated as a replacement for Splunk RBAC or organizational email policy.

## 1. Recipient allow-list by indirection

The command's `to` argument accepts group identifiers, for example:

```spl
| sendmail to=soc title="..." body="..."
```

The command resolves those identifiers against `lookups/Email_bank.txt`. It does not accept a raw email address as the documented recipient value. This prevents a search author from simply placing an arbitrary address in `to`; the destination must be present in a configured group.

This is an application-level recipient directory, not a complete domain allowlist. If policy requires that recipients must belong to specific domains, enforce that policy in Splunk's mail configuration and/or implement an explicit domain allowlist in the application. Do not assume that the current Python validation enforces an organization's domain policy.

## 2. Validation

The recipient manager validates:

- Group-name syntax.
- Duplicate group definitions.
- Email address format.
- Email entries appearing outside a group.
- Requested group existence.
- Requested group non-emptiness.

Invalid configuration is reported as an error rather than being silently accepted.

The email format check is intentionally lightweight. It checks common address structure; it does not prove that a mailbox exists or can receive mail.

## 3. Duplicate prevention

Addresses are normalized to lowercase and duplicate entries within a group are ignored. When multiple groups are requested, recipients are merged without duplicates.

This avoids sending multiple copies to the same normalized address merely because it appears in more than one selected group.

## 4. File-system permissions

`Email_bank.txt` controls who can receive notifications from each group. Treat it as security-relevant configuration.

Recommended controls:

- Make the file readable by the Splunk service account.
- Allow write access only to designated administrators or an approved configuration-management process.
- Keep the app's Python files and configuration protected from unauthorized modification.
- Avoid world-writable permissions.
- Review changes to recipient membership through the organization's change process.

Example Linux permissions (adapt to the actual service account and policy):

```bash
sudo chown -R splunk:splunk "$SPLUNK_HOME/etc/apps/splunk_sendmail"
sudo find "$SPLUNK_HOME/etc/apps/splunk_sendmail" -type d -exec chmod 750 {} \;
sudo find "$SPLUNK_HOME/etc/apps/splunk_sendmail" -type f -exec chmod 640 {} \;
```

## 5. Splunk authentication and SMTP credentials

The application does not store a separate SMTP username or password. It delegates message delivery to Splunk's native `sendemail` command and uses the session key passed by Splunk to submit the secondary search through Splunk's REST interface.

This means:

- SMTP configuration remains centrally managed by Splunk.
- No SMTP password is hard-coded in this app.
- The REST request uses Splunk's session context.
- Splunk authentication and authorization still apply; this is not an unauthenticated command.

Protect session keys and Splunk configuration as part of the platform's normal security controls. Never log or publish session keys.

## 6. Risky command declaration

The command is configured with:

```ini
is_risky = true
```

This is deliberate: sending email is an external side effect. Splunk's risky-command safeguards should remain enabled. Do not change this to `false` merely to suppress a confirmation prompt.

## 7. RBAC and app administration

The app's command metadata makes the command available according to the configured Splunk app permissions. That does not mean every organization should allow every user to send email to every group.

Before production rollout:

- Review the app's metadata and effective permissions.
- Restrict app installation and file modification to administrators.
- Apply Splunk roles/capabilities and search access according to organizational policy.
- Consider separate groups for different sensitivity levels.
- Test whether the intended roles can and cannot execute the command.
- Review the risk of users being able to invoke email delivery from ad-hoc searches.

The current app metadata should be reviewed against the target organization's RBAC design before deployment. Do not assume that file-system permissions alone control who can execute the search command.

## 8. Data handling

Email subjects and bodies may contain sensitive information. Avoid sending secrets, credentials, unnecessary personal data, or restricted event details. Prefer a concise notification with a link or reference to the Splunk investigation, subject to the organization's policy.

## 9. Public repository hygiene

Never commit:

- Real employee or group email addresses.
- Internal hostnames, IP addresses, domains, or infrastructure details.
- SMTP credentials or session keys.
- Production logs or alert payloads containing sensitive data.
- Environment-specific configuration not intended for public release.

Use `lookups/Email_bank.txt` only as a sanitized example in the public repository.
