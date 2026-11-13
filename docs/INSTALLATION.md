# Deployment and Installation Guide

This guide describes a controlled deployment of Splunk SendMail on a Splunk Enterprise Search Head.

## 1. Prerequisites

- Access to the Search Head operating system.
- Permission to install apps under `$SPLUNK_HOME/etc/apps`.
- A working native Splunk email configuration.
- A Splunk service account (commonly `splunk`) that can read the app files.
- An approved test mailbox.

First, verify that native Splunk email works using the standard `sendemail` command. Splunk SendMail delegates delivery to that command; it does not configure the SMTP server.

## 2. Install the app

Copy the complete `splunk_sendmail` directory to:

```text
$SPLUNK_HOME/etc/apps/splunk_sendmail
```

The expected structure is:

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

Do not copy only the Python files. The command and app configuration files are required.

## 3. Configure the recipient file

Edit:

```text
$SPLUNK_HOME/etc/apps/splunk_sendmail/lookups/Email_bank.txt
```

Example:

```ini
[soc]
soc-team@example.com
soc-oncall@example.com

[infra]
infra-team@example.com

[management]
security-manager@example.com
```

Use one address per line. Group names are case-insensitive. Blank lines and comment lines beginning with `#` are ignored.

Do not put production recipient addresses in a public Git repository.

## 4. Set ownership and permissions

On a typical Linux installation where Splunk runs as user and group `splunk`:

```bash
sudo chown -R splunk:splunk "$SPLUNK_HOME/etc/apps/splunk_sendmail"
sudo find "$SPLUNK_HOME/etc/apps/splunk_sendmail" -type d -exec chmod 750 {} \;
sudo find "$SPLUNK_HOME/etc/apps/splunk_sendmail" -type f -exec chmod 640 {} \;
```

These are example permissions, not a universal policy. Confirm the actual Splunk service account and your organization's requirements before applying them.

At minimum:

- The Splunk service account must be able to traverse the app directories.
- The Splunk service account must be able to read the Python/configuration files and `Email_bank.txt`.
- Only designated administrators should be able to modify the recipient file or app code.
- Do not grant broad write permissions such as `777`.

Check the effective permissions:

```bash
namei -l "$SPLUNK_HOME/etc/apps/splunk_sendmail/lookups/Email_bank.txt"
sudo -u splunk test -r "$SPLUNK_HOME/etc/apps/splunk_sendmail/lookups/Email_bank.txt" && echo "Recipient file is readable"
```

Replace `splunk` in the commands if your service uses a different operating-system account.

## 5. Validate command configuration

Run:

```bash
sudo -u splunk "$SPLUNK_HOME/bin/splunk" btool commands list sendmail --debug
```

Confirm that Splunk reads the intended `commands.conf` stanza and the correct `sendmail.py` path.

The app's command configuration includes:

```ini
[sendmail]
filename = sendmail.py
type = python
python.version = python3
enableheader = true
passauth = true
streaming = false
generating = false
run_in_preview = false
supports_rawargs = true
supports_multivalues = false
is_risky = true
```

The `is_risky = true` setting is intentional because this command sends email.

## 6. Restart considerations

A restart or app reload may be needed for the **initial installation** or changes to app/command configuration, depending on the Splunk version and deployment method. Follow your organization's change-management process.

A restart is **not required for edits limited to `Email_bank.txt`**. The recipient manager reads the file when the command executes, so subsequent executions use the updated group membership.

Ensure the edit is saved and the Splunk service account can read it before testing.

## 7. Test safely

1. Create a test-only group in `Email_bank.txt`:

   ```ini
   [test]
   your-test-mailbox@example.com
   ```

2. Save the file.
3. Run this search in Splunk:

   ```spl
   | makeresults
   | sendmail to=test title="Splunk SendMail Deployment Test" body="Test message from Splunk SendMail."
   ```

4. If Splunk presents a risky-command confirmation, review and approve it only if the action is expected and authorized.
5. Confirm receipt in the test mailbox.
6. Test an unknown group and an empty group to confirm that invalid requests fail safely.

Do not begin with a production distribution list.

## 8. Updating recipients after deployment

When an employee joins, leaves, or changes teams:

1. Confirm the change is approved by the responsible group owner.
2. Edit the relevant section in `Email_bank.txt`.
3. Add or remove the address.
4. Save the file.
5. Confirm file ownership and read access remain correct.
6. Run a controlled test if required by policy.

No restart is needed for this file-only change. Alerts that reference the same group name do not need to be edited.

## 9. Deployment architecture

Install the app on the Search Head that executes the searches/alerts. In a distributed Splunk deployment, follow Splunk's app-distribution practices and make sure the command and recipient file are present on the search tier that runs the search. Do not assume that installing the app only on an indexer makes the command available to Search Head searches.

For clustered or managed deployments, use the organization's approved deployment mechanism and validate the app on the relevant Search Heads.
