# Gable CLI and SDK

`gable` is Gable on the command line. It publishes contracts, registers data assets and more.

```bash
gable --help
Usage: gable [OPTIONS] COMMAND [ARGS]...

Options:
  --endpoint TEXT  Customer API endpoint for Gable, in the format
                   https://api.company.gable.ai/
  --api-key TEXT   API Key for Gable
  --version        Show the version and exit.
  --help           Show this message and exit.

Commands:
  auth        View configured Gable authentication information
  contract    Validate/publish contracts and check data asset compliance
  data-asset  Commands for data assets
  ping        Pings the Gable API to check for connectivity
```

## Getting Started

`gable` is [hosted on PyPi](https://pypi.org/project/gable/), so to install it just run:

```bash
pip install gable
```

### Installing Additional Modules for MySQL and PostgreSQL

Gable's CLI allows you to introspect your database and register tables as data assets within Gable's system. Connecting to these databases require additional packages to communicate with your database(s) of choice.

For MySQL, install the additional packages by running:

```bash
pip install 'gable[mysql]'
```

For PostgreSQL, install the additional packages by running:

```bash
pip install 'gable[postgres]'
```

To install all additional dependencies at once, you can run:

```bash
pip install 'gable[all]'
```

## Setting up zsh/bash Autocomplete

The Gable CLI supports shell autocomplete for `zsh` and `bash` so you can hit `TAB` to see available commands and options as you write the command.

To enable it, run the following commands:

```bash
_SHELL=zsh # or bash
GABLE_CONFIG_DIR=~/.config/gable
mkdir -p $GABLE_CONFIG_DIR
_GABLE_COMPLETE=${_SHELL}_source gable > $GABLE_CONFIG_DIR/complete.sh
```

Then add the following to your shell startup scripts (e.g. `.zshrc`, `.bashrc`):

```bash
source ~/.config/gable/complete.sh
```

### Authentication

To establish an authenticated connection with Gable via the CLI, you need:

- The API endpoint associated with your organization
- An API key that corresponds to the endpoint

In order to find your API key and API endpoint, see the documentation in your Gable web app at (`/docs/settings/api_keys`).

There are two supported methods for providing this config to the CLI:

#### Authenticating with CLI Arguments

You have the option to pass the endpoint and API key information directly as arguments during the CLI invocation. For example:

```bash
gable --endpoint "https://api.yourorganization.gable.ai" --api-key "yourapikey" ping
```

#### Authenticating with Environment Variables

To avoid providing this config every time you execute a command, you can set them as environment variables: `GABLE_API_ENDPOINT` and `GABLE_API_KEY`. To make them persistent in your environment, add this to your shell initialization file (e.g. `.zshrc` or `.bashrc`):

```bash
export GABLE_API_ENDPOINT="https://api.yourorganization.gable.ai"
export GABLE_API_KEY="yourapikey"
```

Then, you can simply use the CLI as follows:

```bash
gable ping
```

### Accessing APIs Behind Proxies (Custom API Headers)

To access the Gable API behind corporate or customer proxies that require custom authentication, users can provide additional HTTP headers using the `GABLE_API_HEADERS` environment variable. This feature is essential for organizations whose infrastructure enforces proxy authentication or requires custom metadata in API requests.

#### Usage
Set the `GABLE_API_HEADERS` environment variable as a JSON string containing your custom headers:

```sh
export GABLE_API_HEADERS='{"Authorization": "Bearer YOUR_TOKEN", "X-Proxy-Header": "proxy-value"}'
```

When set, these headers are automatically included in every API request made by the CLI or client library. Custom headers will override default headers (such as `X-API-KEY`), allowing flexible integration with proxies, gateways, or custom authentication schemes.

#### Example
```sh
export GABLE_API_KEY=your_api_key
export GABLE_API_ENDPOINT=https://api.example.com
export GABLE_API_HEADERS='{"Authorization": "Bearer YOUR_TOKEN", "X-Proxy-Header": "proxy-value"}'
gable ping
```
