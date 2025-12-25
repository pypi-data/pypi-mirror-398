# Imports
from enum import Enum
import sys
import os
import io
import copy
import toml
import configparser
import json

# Internal imports
from .drawer import Drawer
from .typewriter import Typewriter

# Shorthand vars
drawer = Drawer()
typewriter = Typewriter()
config_folder = drawer.get_config()


# Internal functions
def merge(source: dict, destination: dict) -> dict:
  for key, value in source.items():
    if isinstance(value, dict):
      node = destination.setdefault(key, {})
      merge(value, node)
    else:
      destination[key] = value
  return destination


# Enums
class ConfigExtension(Enum):
  TOML = 'toml'
  INI = 'ini'
  JSON = 'json'


# Deals with configs and reading/writing files
class Notebook:
  # Returns a tuple of (read, write) functions for a given configuration file.
  def get_read_write_functions(self, file: str) -> tuple:
    functions_by_extension = {
      'toml': (self.read_toml, self.write_toml),
      'ini': (self.read_ini, self.write_ini),
      'json': (self.read_json, self.write_json),
    }
    extension = drawer.get_extension(file)
    function_pair = functions_by_extension.get(extension)
    if function_pair is None:
      raise NotImplementedError(
        f"Files with extension '{extension}' are not supported."
      )
    return function_pair

  # Returns a toml file parsed to a dict.
  def read_toml(self, file: str) -> dict:
    data = drawer.read_file(file)
    return toml.loads(data)

  # Writes a toml file parsed from a dict.
  def write_toml(self, path: str, contents: dict, overwrite: bool = False):
    data = toml.dumps(contents)
    drawer.write_file(path, data, overwrite)

  # Returns an ini file parsed to a dict.
  def read_ini(self, ini_file: str) -> dict:
    data = drawer.read_file(ini_file)
    parser = configparser.ConfigParser(
      inline_comment_prefixes=('#', ';'),
      strict=False,
    )
    parser.read_string(data)
    return parser._sections

  # Writes a ini file parsed from a dict.
  def write_ini(self, path: str, contents: dict, overwrite: bool = False):
    parser = configparser.ConfigParser(
      inline_comment_prefixes=('#', ';'),
      strict=False,
    )
    parser.read_dict(contents)
    string_io = io.StringIO()
    parser.write(string_io)
    drawer.write_file(path, string_io.getvalue(), overwrite)

  # Returns a json file parsed to a dict.
  def read_json(self, path: str) -> dict:
    data = drawer.read_file(path)
    return json.loads(data, strict=False)

  # Writes a json file parsed from a dict.
  def write_json(self, path: str, contents: dict, overwrite: bool = False):
    data = json.dumps(contents, indent=2)
    drawer.write_file(path, data, overwrite)


# Making the ConfigExtension enum available to the user
Notebook.ConfigExtension = ConfigExtension
notebook = Notebook()


# A config object, meant to be created by the Ledger, but can also be used by
# itself.
#
# On initialisation it checks if the 'file' exists, and if not, then
# it creates it and writes the contents of 'template' to it. Then it checks
# the config, using the check() method, for any errors with the config file,
# if it encounters an issue it prints what the issue is and then exits. In
# other words, if you have initialised the config object, you can be sure
# that it does not contain any errors.
class Config:
  def __init__(self, file: str, defaults: dict, template: str):
    # Ensuring file exists
    if not drawer.exists(file):
      drawer.write_file(file, template)
    # Setting vars to self
    self.readwrite_functions = notebook.get_read_write_functions(file)
    self.defaults = defaults
    self.file = file
    # Checking config contents
    self.check()

  # Checks the config file for any errors, if any are present then it prints
  # the error and exits using the appropriate exit code.
  def check(self):
    try:
      function = self.readwrite_functions[0]
      _ = function(self.file)
    except Exception as e:
      self.on_error(str(e))

  def on_error(self, error: str or list):
    error_type = type(error)
    if error_type is str:
      title = f"Configuration error in '{self.file}':"
      errors = [error]
    elif error_type is list:
      if len(error) == 1:
        self.on_error(error[0])
      else:
        title = f"Configuration errors in '{self.file}':"
      errors = error
    else:
      raise TypeError()
    title = typewriter.stylise(
      typewriter.Colour.BRIGHT_RED,
      'Configuration error(s):',
    )
    title = typewriter.bolden(title)
    formatted_errors = typewriter.list_to_columns(
      [f'- {error}' for error in errors],
      n_columns=1,
    )
    print(
      f'{title}\n{self.file}:\n{formatted_errors}',
      file=sys.stderr,
    )
    if hasattr(os, 'EX_CONFIG'):
      sys.exit(os.EX_CONFIG)
    else:
      sys.exit(78)

  # Reads the config and fills any missing values with the 'defaults' provided
  # during initialisation.
  def read(self) -> dict:
    function = self.readwrite_functions[0]
    file_values = function(self.file)
    default_values = copy.deepcopy(self.defaults)
    actual_values = merge(file_values, default_values)
    return actual_values

  # Writes the given dict to the config file.
  # Note that using this function will erase all the comments and custom
  # formatting from the file.
  def write(self, contents: dict):
    function = self.readwrite_functions[1]
    return function(self.file, contents, overwrite=True)


# Ensures that the program's configuration directory exists on initialisation
# and simplifies the creation of Config objects.
class Ledger:
  def __init__(self, program: str):
    self.program_dir = f'{config_folder}/{program}'
    # Making sure that required directories exist
    drawer.make_folder(config_folder)
    drawer.make_folder(self.program_dir)

  def init_config(
    self,
    name: str,
    defaults: dict,
    template: str,
    extension: Notebook.ConfigExtension = Notebook.ConfigExtension.TOML,
  ) -> Config:
    file = f'{self.program_dir}/{name}.{extension.value}'
    config = Config(file, defaults, template)
    return config


# Making the Ledger and Config classes available to the user
Notebook.Ledger = Ledger
Ledger.Config = Config
