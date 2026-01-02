# Sendlix Python SDK

This package provides a Python implementation of the Sendlix gRPC SDK that aims for feature parity with the official reference client. It exposes the same high-level clients (`EmailClient`, `GroupClient`) and the same authentication helper (`Auth`).

## Installation

```bash
pip install sendlix
```

## Authentication

API keys are issued in the format `secret.keyId`. You can either pass the key string directly to a client or create a reusable `Auth` instance:

```python
from sendlix import Auth, EmailClient

auth = Auth("sk_xxxxxxxxx.xxx")
email_client = EmailClient(auth)
# or
email_client = EmailClient("sk_xxxxxxxxx.xxx")
```

The token fetched by `Auth` is cached until it expires.

## Available Clients

### EmailClient

Send transactional emails, raw EML messages, or trigger group emails.

Methods:

- `send_email(mail_options, additional_options=None)` – send a regular email with `to`, `cc`, `bcc`, `html`/`text`, attachments, and inline images.
- `send_eml_email(eml, additional_options=None)` – upload raw EML content from a path, bytes, or buffer.
- `send_group_email(group_mail)` – broadcast to a predefined Sendlix group.

### GroupClient

Manage recipients inside Sendlix groups.

- `insert_email_into_group(group_id, email_records, fail_handling="ABORT")`
- `delete_email_from_group(group_id, email)`
- `contains_email_in_group(group_id, email)`

Each method mirrors the semantics and error handling described in the reference SDK documentation.

## Examples

### Sending an email

```python
from sendlix import EmailClient

client = EmailClient("sk_xxxxxxxxx.xxx")

response = client.send_email(
    {
        "from": {"email": "sender@example.com", "name": "Sender"},
        "to": ["recipient@example.com"],
        "subject": "Hello World!",
        "html": "<h1>Welcome!</h1><p>This is a test email.</p>",
    }
)
print(response)
```

### Adding emails to a group

```python
from sendlix import GroupClient

group_client = GroupClient("sk_xxxxxxxxx.xxx")

group_client.insert_email_into_group(
    "groupId123",
    [
        {"email": "a@example.com"},
        {
            "email": {"email": "b@example.com", "name": "User B"},
            "substitutions": {"plan": "pro"},
        },
    ],
)
```

## Development

- Regenerate gRPC stubs: `.\build.cmd`
- Run tests: `pytest`

### Local quickstart

If you are working from a clone of this repository (instead of the published `pip install sendlix` package), make sure you run the code inside the provided virtual environment so that the correct dependency versions (especially `protobuf>=5.29.0`) are available:

```powershell
python -m venv .venv
./.venv/Scripts/Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

Running the SDK with an older global installation of `google.protobuf` (<5.29) will raise an `ImportError: cannot import name 'runtime_version'` when the generated gRPC stubs are imported. Activating the virtual environment (or upgrading `protobuf` in your global interpreter) resolves the issue.

The project uses the Apache-2.0 license.
