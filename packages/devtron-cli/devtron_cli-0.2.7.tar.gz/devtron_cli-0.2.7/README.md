# Tron - Devtron Infrastructure and Application Automation Tool

Tron is a command-line tool designed to automate Devtron infrastructure and application management through modular YAML configuration files.

## Features

- Create Devtron applications via YAML configuration
- Update existing Devtron applications
- Manage environments and pipelines
- Simple CLI interface
- Can be used as a Python module in other projects

## Installation

```bash
pip or pip3 install devtron-cli
```

## Usage

### Command Line Interface

```bash
# Create a new application (provide Devtron URL and API token via command line or environment variables)
tron --config config.yaml create-app --devtron-url https://devtron.example.com --api-token your-api-token

# Update an existing application
tron --config config.yaml update-app --devtron-url https://devtron.example.com --api-token your-api-token

# Or set environment variables and omit the URL and token from command line
export DEVTRON_URL=https://devtron.example.com
export DEVTRON_API_TOKEN=your-api-token
tron --config config.yaml create-app
```

## Development

To contribute to this project:

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Make your changes
4. Test your changes
5. Submit a pull request

## License

This project is licensed under the MIT License.
