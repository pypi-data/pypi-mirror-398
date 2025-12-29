sparkback
=========

A Python library for generating sparklines.

## Installation

```
$ uv sync --all-extras
$ uv run spark --help
```

## Usage
You can use sparkback from the command line or in your Python scripts.

## Command Line

Run sparkback with a series of numbers:

```
spark --ticks default 10 20 30 40 50
```


You can also use different styles of ticks:

```
spark --ticks block 10 20 30 40 50
spark --ticks ascii 10 20 30 40 50
spark --ticks numeric 10 20 30 40 50
spark --ticks braille 10 20 30 40 50
spark --ticks arrows 10 20 30 40 50
spark --ticks line 10 20 30 40 50
spark --ticks multiline 10 20 30 40 50
```

Use the --stats option to display statistics about your data:

```
spark --ticks default 10 20 30 40 50 --stats
```

## Python API

You can also use sparkback in your Python scripts:

```
import sparkback

data = [10, 20, 30, 40, 50]
ticks = sparkback.scale_data(data, sparkback.TICKS_OPTIONS["default"])
sparkback.print_ansi_spark(ticks)
```

## See also:

* https://github.com/ajacksified/Clark/
* https://github.com/holman/spark

