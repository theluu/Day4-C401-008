---
name: email
track: extension
kind: action
provider: Gmail SMTP
requires_env: [EMAIL_USER, EMAIL_PASS]
inputs: [to, subject, body, confirmed]
outputs: [status, message]
side_effect: true
---
# email

Sends an email via Gmail SMTP server.
Requires EMAIL_USER and EMAIL_PASS environment variables (falls back to simulation mode if missing).
Requires explicit user confirmation before executing.
