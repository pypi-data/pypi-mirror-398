# libjam
A library jam for Python.

## Installing
libjam is available on [PyPI](https://pypi.org/project/libjam/), and can be installed using pip.
```
pip install libjam
```
To install the latest bleeding edge:
```
pip install git+https://github.com/philippkosarev/libjam.git
```

## Modules

### Captain
Makes creating command line interfaces easy.

#### Example CLI project:
example.py:
```python
#! /usr/bin/env python3

from libjam import Captain

def shout(text: str):
  'Shouts the given text back'
  if options.get('world'):
    text += ' world'
  print(text + '!')

captain = Captain(shout, program='shout')
captain.add_option(
  'world', ['world', 'w'],
  "Adds ' world' before the exclamation mark",
)
global options
args, options = captain.parse()
shout(*args)
```

Usage:
```sh
$ ./example.py
shout: missing argument <TEXT>

$ ./example.py Hello
Hello!

$ ./example.py Hello --world
Hello world!

$ ./example.py --help
Usage:
  shout [OPTION]... <TEXT>
Description:
  Shouts the given text back.
Options:
  -w, --world - Adds ' world' before the exclamation mark.
  -h, --help  - Prints this page.
```

### Drawer
Responsible for file operations. Accepts `/` as the file separator regardless the operating system.

#### Example CLI for calculating filesizes
mass.py:
```python
#! /usr/bin/env python3

from libjam import Captain, drawer, typewriter
import sys

def print_progress(todo, done):
  typewriter.print_progress('Calculating file size', todo, done)

def mass(*paths):
  'Prints human-readable size of files'
  if len(paths) == 0:
    paths = ['./']
  n_paths = len(paths)
  results = {}
  for i, path in enumerate(paths):
    if n_paths > 1:
      print_progress(i+1, n_paths)
    if not drawer.exists(path):
      typewriter.clear_lines(0)
      print(f'{path}: No such file or directory.', file=sys.stderr)
      continue
    size = drawer.get_filesize(path)
    results[path] = size
  results = dict(sorted(results.items(), key=lambda item: item[1], reverse=True))
  typewriter.clear_lines(0)
  for file in results:
    size = results.get(file)
    size, units, _ = drawer.get_readable_filesize(size)
    size = round(size, 1)
    print(f'{file}: {size} {units.upper()}')

captain = Captain(mass)

def main():
  args = captain.parse()
  try:
    return mass(*args)
  except KeyboardInterrupt:
    print()
    sys.exit(1)

if __name__ == '__main__':
  sys.exit(main())
```

Usage:
```sh
$ ./mass.py
./: 100.9 MB

$ ./mass.py downloads pictures videos
videos: 34.7 GB
downloads: 12.6 GB
pictures: 2.2 GB

$ ./mass.py -h
Synopsis:
  mass.py [OPTION]... [PATHS]...
Description:
  Prints human-readable size of files.
Options:
  -h, --help - Prints this page.
```

### Typewriter
Transforms text and prints to the terminal.

### Notebook
Allows reading and writing `.toml`, `.ini` and `.json` files and provides an application configuration management system with the `Notebook.Ledger` class.

#### Example of an app configured through Notebook.Ledger:
```py
# Imports
from libjam import notebook, drawer

# Defining default values
default_downloads_dir = drawer.absolute_path('~/Downloads')
if not drawer.is_folder(default_downloads_dir):
  default_downloads_dir = None
default_values = {
  'downloads-directory': default_downloads_dir,
}
# Config template
template = '''\
# An override for the default downloads directory
# downloads-directory = ''
'''

# Initialising config
ledger = notebook.Ledger('download-manager')
config_obj = ledger.init_config('config', default_values, template)
config_dict = config_obj.read()

# Checking values
downloads_dir = config_dict.get('downloads-directory')
if downloads_dir is None:
    config_obj.on_error(
      "Could not automatically find an existing Downloads directory. "
      "Please specify 'downloads-directory' in the configuration manually."
  )
if not drawer.exists(downloads_dir):
  config_obj.on_error("The specified 'downloads-directory' does not exist")
```

download_manager.py:
```py
#! /usr/bin/env python3

# Imports
import requests

# Getting downloads_dir from config
from config import downloads_dir

# The rest of the program...
```

Example output:
```sh
$ ./download_manager.py
Configuration error(s):
/home/philipp/.config/download-manager/config.toml:
  - Could not automatically find an existing Downloads directory. Please specify 'downloads-directory' in the configuration manually.
```

### Clipboard
Provides a few list operations such as `deduplicate`.

### Flashcard
Provides the `prompt_yn` function.

### Cloud
Provides the `download` function.