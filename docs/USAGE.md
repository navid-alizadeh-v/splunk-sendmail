# Usage Guide

The custom command syntax is:

```spl
| sendmail to=<group[,group2,...]> title="<subject>" body="<message>"
```

All three arguments are required:

| Argument | Purpose |
|---|---|
| `to` | One or more comma-separated group names defined in `Email_bank.txt` |
| `title` | Email subject |
| `body` | Email message body |

The command accepts group names rather than arbitrary email addresses.

## 1. One group

```spl
| makeresults
| sendmail to=soc title="SOC Test" body="This is a test notification."
```

## 2. Multiple groups

```spl
| makeresults
| sendmail to=soc,infra title="Infrastructure Incident" body="An infrastructure incident requires investigation."
```

If the same address appears in both groups, it is included only once in the resolved recipient list.

## 3. Security alert example

Append the command to the end of an alert search after the search has identified the condition:

```spl
index=security sourcetype=your_security_source
| where severity="high"
| stats count by host, signature
| sendmail to=soc title="High Severity Security Alert" body="A high-severity security event was detected. Review the corresponding search results in Splunk."
```

Adapt the index, sourcetype, field names, and message to your environment. The example is illustrative and is not a complete detection rule.

## 4. Infrastructure alert

```spl
index=infra sourcetype=your_infrastructure_source
| stats count by host
| sendmail to=infra title="Infrastructure Monitoring Alert" body="An infrastructure monitoring condition was triggered. Please review Splunk."
```

## 5. Management notification

```spl
| makeresults
| sendmail to=management title="Daily Security Summary" body="The daily security summary is available in Splunk."
```

## 6. Reuse a recipient group across many alerts

For example, multiple alert definitions can all use:

```spl
... | sendmail to=soc title="..." body="..."
```

When SOC membership changes, update only the `[soc]` section in `Email_bank.txt`. The next command execution reads the new contents. No per-alert edit or Splunk restart is required for this recipient-file-only change.

## 7. Expected validation failures

Examples of invalid conditions include:

- Missing `to`, `title`, or `body`.
- An unknown group name.
- A requested group with no email addresses.
- A malformed email address in the recipient file.
- An address placed before any group section.
- An invalid or duplicate group section.

The command reports an error rather than silently substituting a different recipient group.

## Operational note

The command submits an email request through Splunk's native email mechanism. A successful command execution should not be interpreted as proof that every recipient's mailbox accepted or displayed the message. For production monitoring, validate delivery through mail infrastructure logs or an approved delivery-monitoring process.
