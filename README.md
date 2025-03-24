# Camunda Cloud Python Worker

This project implements a Python worker that connects to Camunda Cloud and processes external tasks.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. The `.env` file is already configured with your Camunda Cloud credentials.

## Usage

To start the worker:
```bash
python worker.py
```

The worker will:
1. Connect to your Camunda Cloud instance using the provided credentials
2. Subscribe to the "example-topic" topic
3. Process any external tasks that arrive

## Customization

To customize the worker for your specific needs:

1. Modify the `handle_task` function in `worker.py` to implement your business logic
2. Change the topic name in the `worker.subscribe()` call to match your process definition
3. Add any additional variables or processing logic as needed

## Security Note

The `.env` file contains sensitive credentials. Make sure to:
- Never commit this file to version control
- Keep your credentials secure
- Use appropriate access controls for your Camunda Cloud instance 