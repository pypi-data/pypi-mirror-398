# Advanced Debugger

Minimalist, colorful, configurable debug logger for Python.

## Why Advanced Debugger?

- 👨‍💻 Simple console logging of actions.
- 🕐 Debug with time specifying for one minute
- 🗄️ Takes only few lines for much debugs.

## Examples

Define debug category:
dbgVar = AdvDBG.define('title of your debug')

Print something:
dbgVar.info('Text to debug!')
OR
dbgVar('Text to debug!')

Available types:
	`WARN`
	`INFO`
	`ERROR`

Returns:
[title of your debug at DATE AND TIME] Text to debug!

Configure existing category:
dbgVar.cfg(title='REQUEST')

BEFORE: title of your debug
AFTER: REQUEST

## Change Log: v0.2.0

- Added export feature

## LICENSE

This module licensed with MIT

## Installation

```bash
pip install advdbg