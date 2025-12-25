# Breezeway Python Client

A Python client library for communicating with Breezeway.io, providing an easy interface for managing authentication and
interacting with Breezeway's API.

## Installation

```sh
pip install breezeway
```

## Example Usage

```python
import breezeway

# Initialize the client
bw = breezeway.BreezewayClient(client_id='your_client_id', client_secret='your_client_secret')

# Get tasks
tasks = bw.get_tasks()
print(tasks)

# Create a new task
new_task = bw.create_task(property_id=12345, title='Inspect HVAC system')
print(new_task)
```

## Contributing

Contributions are welcome! Feel free to submit a pull request or open an issue.

## License

This project is licensed under the MIT License.

