# hiws

A Python package for interacting with WhatsApp's Cloud API.

## Installation

```bash
pip install hiws
```

## Usage

```python
from hiws import WhatsAppMessenger

messenger = WhatsAppMessenger(access_token="YOUR_ACCESS_TOKEN", phone_number_id="YOUR_PHONE_NUMBER_ID")

# Example usage
message_id = await messenger.send_text(recipient_phone_number="1234567890", text="Hello, World!")

print(message_id)
```

## Development

To install in development mode:

```bash
git clone https://github.com/cervant-ai/hiws.git
cd hiws
pip install -e .
```

To install development dependencies:

```bash
pip install -e ".[dev]"
```

## Testing

```bash
pytest
```

```bash
pip install -e ".[dev]"
```

## Testing

```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
