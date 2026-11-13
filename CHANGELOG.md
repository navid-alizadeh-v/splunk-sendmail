# Changelog

All notable changes to this project are documented here.

## 0.1.0 - 2026-11-13

- Initial public documentation package.
- Centralized recipient groups using `Email_bank.txt`.
- Custom `sendmail` search command.
- Recipient validation and de-duplication.
- Delegation to Splunk's native `sendemail` functionality.
- Runtime loading of recipient configuration, so recipient-file changes do not require a Splunk restart.
