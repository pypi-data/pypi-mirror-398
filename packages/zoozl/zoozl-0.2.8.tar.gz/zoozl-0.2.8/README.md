# zoozl

Server for chatbot services

## Usage

For basic example a chatbot plugin is provided in `zoozl.plugins` package. It is a simple chatbot that allows to play bulls & cows game. It is also a plugin that is loaded in case no configuration file is provided.

### Run websocket server

```bash
python -m zoozl --conf chatbot.toml
```
where `chatbot.toml` is configuration file.

## Architecture

zoozl package contains modules that handle various input interfaces like websocket or http POST and a chatbot interface that must be extended by plugins. Without plugin zoozl is not able to respond to any input. Plugin can be considered as a single chat assistant to handle a specific task. Plugin can be huge and complex or simple and small. It is up to the developer to decide how to structure plugins.
![zoozl_package](docs/images/zoozl_package.svg)


## Plugin

### Mimimal setup

1. Create new toml configuration file (e.g. myconfig.toml)
```
extensions = ['my_plugin_module']
```
2. Make sure `my_plugin_module` is importable from within python that will run zoozl server
3. Create file `my_plugin_module.py`
```
from zoozl.chatbot import Interface

class MyPlugin(Interface):

    aliases = ("call myplugin",)

    def consume(self, context: , package: Package):
        package.callback("Hello this is my plugin response")
```
4. Start zoozl server with your configuration file and asking to bot `call myplugin` it will respond `Hello this is my plugin response`
```bash
python -m zoozl --conf myconfig.toml
```

### Plugin interface

Plugin must implement `consume` method that takes two arguments `context` and `package`. `context` is a InterfaceRoot object that contains information about the current chatbot state and `package` is a `Package` object that contains input message and callback method to send response back to the user.

Plugin may define `aliases` attribute that is a tuple of strings that are used to call the plugin. If `aliases` is not defined, plugin will not be called. Aliases are like commands that user can call to interact with the plugin, however those commands are constructed as embeddings and then compared with input message embeddings to find the best match.

Special aliases are help, cancel and greet. Help alias is used when there is no matching aliases found in plugins, cancel alias is used to cancel current conversation and release it from current plugin handling, greet alias is called immediately before any user message is handled.

If there is only one plugin expected, then aliases most likely should contain all three special aliases, thus plugin will be as soon as connection is made and everytime user asks anything.

### Configuration file

Configuration file must conform to TOML format. Example of configuration:
```
extensions = ["chatbot_fifa_extension", "zoozl.plugins.greeter"]
websocket_port = 80  # if not provided, server will not listen to websocket requests
author = "my_chatbot_name"  # defaults to empty string
slack_port = 8080  # if not provided, server will not listen to slack requests
slack_app_token = "xoxb-12333" # Mandatory if slack_port is provided, oAuth token for slack app to send requests to slack
slack_signing_secret = "abc123" # Mandatory if slack_port is provided, secret key to verify requests from slack
email_port = 8081  # if provided, server will listen to LMTP requests there
email_address = "something@localhost"  # Mandatory if email_port is provided, email address to send back email messages to
email_smtp_port = 25  # Optional port for sending out email messages to, defaults to 25

[chatbot_fifa_extension]  # would be considered as specific configuration for plugin
database_path = "tests/tmp"
administrator = "admin"
```

Root objects like author, extensions are configuration options for chatbot system wide setup, you can pass unlimited objects in configuration, however suggested is to add a component for each plugin and separate those within components.


* TODO: Describe plugin interface and creation
* TODO: Add authentication and authorization interaction between chatbot and plugin
