## ScurryKit

[![PyPI version](https://badge.fury.io/py/scurry-kit.svg)](https://badge.fury.io/py/scurry-kit)

ScurryKit is a collection of addons built on top of [ScurryPy](https://github.com/scurry-works/scurrypy), providing decorators, routing, structured patterns, and higher-level convenience features.

All addons in `scurry-kit/addons` are self-contained and can be reused independently in your own projects.

## Features

* Declarative style using decorators
* Built-in command and event routing
* Configurable caching by object type
* Unix-shell-style wildcards for component routing
* Fully compatible with ScurryPy (no lock-in)

## Installation

```bash
pip install scurry-kit
```

## Examples

These examples are ideal starting points:

* [Event](examples/basic_event.py)
* [Prefix](examples/basic_prefix.py)
* [Slash Command](examples/basic_command.py)

## Advanced Examples

The `examples/` directory also includes more advanced examples:

### Commands
* [Command Options](examples/command_options.py)
* [Stateful Bot](examples/stateful_bot.py)
* [Autocomplete Interaction](examples/autocomplete.py)
* [Deferred Interaction](examples/deferred.py)

### Components
* [Buttons](examples/button.py)
* [V2 Components](examples/v2_components.py)
* [Select Components](examples/select_components.py)
* [Modal](examples/modal.py)

### Interactions & Responses
* [Ephemeral Interaction](examples/ephemeral.py)
* [Context Menu](examples/context_menu.py)
* [Pagination](examples/pagination.py)

### Utility / Setup
* [Building Embeds](examples/building_embeds.py)
* [Error Handling](examples/error_handling.py)
* [Configuring Caches](examples/configuring_cache.py)
