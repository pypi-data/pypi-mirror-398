# Imports
import sys
import os

# Internal imports
from .typewriter import Typewriter

typewriter = Typewriter()


# Exceptions
class ParsingError(Exception):
  pass


# Internal functions
def categorise_args(all_args: list) -> tuple:
  # Vars
  args = []
  long_opts = []
  short_opts = []
  # Categorising
  for arg in all_args:
    if arg.startswith('--'):
      long_opts.append(arg.removeprefix('--'))
    elif arg.startswith('-'):
      short_opts += list(arg.removeprefix('-'))
    else:
      args.append(arg)
  # Returning
  return args, long_opts, short_opts


def parse_options(
  self,
  long_opts: list,
  short_opts: list,
) -> dict:
  parsed_options = {}
  for option in self.options:
    parsed_options[option.get('key')] = False
  for prefix, key, given_opts in (
    ('--', 'long', long_opts),
    ('-', 'short', short_opts),
  ):
    for given_opt in given_opts:
      found = None
      for option in self.options:
        flags = option.get(key)
        if given_opt in flags:
          found = option
          break
      if found is None:
        self.on_usage_error(f"unrecognised option '{prefix}{given_opt}'")
      else:
        parsed_options[found.get('key')] = True
  return parsed_options


# Returns a list of function parameters.
def get_function_args(function: callable) -> list:
  code = function.__code__
  if code.co_kwonlyargcount:
    raise NotImplementedError(
      'Keyword-only function arguments are not supported.'
    )
  argcount = code.co_argcount
  varnames = list(code.co_varnames)
  args = varnames[:argcount]
  flags = code.co_flags
  if flags & 0x04:
    args.append(varnames[len(args)])
  if argcount < len(args):
    args[argcount] = '*' + args[argcount]
  return args


# Converts each string in a list to a posix-compliant representation of a
# command line argument.
def to_posix_args(args: list) -> list:
  output_args = []
  for arg in args:
    arg = arg.upper().replace('_', ' ')
    if arg.startswith('*'):
      arg = arg.removeprefix('*')
      arg = f'[{arg}]...'
    else:
      arg = f'<{arg}>'
    output_args.append(arg)
  return output_args


# Returns a list of functions a given object has. Ignores functions starting
# with an underscore.
def get_object_functions(obj: object) -> list:
  functions = []
  class_dict = obj.__class__.__dict__
  for key in class_dict:
    if key.startswith('_'):
      continue
    function = class_dict.get(key)
    functions.append(function)
  return functions


# Converts a python function name to a posix-like command name.
def function_name_to_command(name: str) -> str:
  return name.replace('_', '-')


# Returns a dictionary where the key is a posix-like name of the function and
# the value is the function.
def get_object_commands(obj: object) -> dict:
  commands = {}
  functions = get_object_functions(obj)
  for function in functions:
    name = function.__name__
    command = function_name_to_command(name)
    commands[command] = function
  return commands


# Creates a section of a help page with given title and body.
def make_help_section(title: str, body: str or list) -> str:
  if type(body) is str:
    body = '  ' + body.replace('\n', '\n  ')
  else:
    assert len(body) % 2 == 0
    for i in range(1, len(body), 2):
      string = body[i]
      if string:
        body[i] = f'- {string}.'
    body = typewriter.list_to_columns(body, n_columns=2)
  return f'{title}:\n{body}'


# Returns the 'Commands' section of a help page.
def get_commands_help_section(commands: dict) -> str:
  items = []
  for command, function in commands.items():
    items.append(command)
    items.append(function.__doc__)
  return make_help_section('Commands', items)


# Returns the 'Usage' section of a help page.
def get_usage_help_section(program: str, commands: dict) -> str:
  lines = []
  for command, function in commands.items():
    command_args = get_function_args(commands.get(command))[1:]
    if not command_args:
      continue
    command_args = ' '.join(to_posix_args(command_args))
    lines.append(f'{program} {command} {command_args}')
  if lines:
    text = '\n'.join(lines)
    return make_help_section('Usage', text)


# Returns the 'Options' section of a help page.
def get_options_help_section(options: dict) -> str:
  items = []
  for option in options:
    long = ['--' + string for string in option.get('long')]
    short = ['-' + string for string in option.get('short')]
    flags = ', '.join(short + long)
    items.append(flags)
    items.append(option.get('description'))
  return make_help_section('Options', items)


# Returns the help page sections for a ship of type callable.
def get_singlecommand_sections(self) -> list[str]:
  sections = []
  usage = f'{self.program} [OPTION]...'
  function_args = get_function_args(self.ship)
  if function_args:
    usage += ' ' + ' '.join(to_posix_args(function_args))
  sections.append(make_help_section('Usage', usage))
  doc = self.ship.__doc__
  if doc:
    sections.append(make_help_section('Description', doc + '.'))
  return sections


# Returns the help page sections for a ship of type object.
def get_multicommand_sections(self) -> list[str]:
  sections = []
  doc = self.ship.__doc__
  if doc:
    sections.append(doc + '.')
  synopsys = self.program + ' [OPTION]... COMMAND [ARGS]...'
  sections.append(make_help_section('Synopsis', synopsys))
  commands = get_object_commands(self.ship)
  sections.append(get_commands_help_section(commands))
  sections.append(get_usage_help_section(self.program, commands))
  return sections


# Captain is a tool for making CLIs quickly. It works by constructing a CLI
# based on the specified `ship` which can be either an initialised object or
# a function. If the `ship` is an initialised object then it's functions
# will be mapped to the CLI's commands. The function's parameters will be
# mapped to command-line arguments.
class Captain:
  # If the `program` keyword is not specified, then it use the basename of
  # `sys.argv[0]`.
  def __init__(
    self,
    ship: object or callable,
    program: str = None,
    *,
    add_help: bool = True,
    compact_help: bool = None,
  ):
    if type(ship) is type:
      raise ParsingError(f"Specified ship '{ship.__name__}' is not initialised")
    self.ship = ship
    self.add_help = add_help
    self.compact_help = compact_help
    if program is None:
      program = os.path.basename(sys.argv[0])
    self.program = program
    self.options = []

  # Adds an option with given flags and description. After parsing you will get
  # an options dictionary where the provided `key` will lead to either True (if
  # one of the flags was provided by the user) or False (if the user did not
  # specify the option's flag).
  #
  # If the `flags` param is not specified then it will use the `key` as a flag.
  def add_option(
    self,
    key: str,
    flags: list = None,
    description: str = '',
  ):
    if flags is None:
      flags = [key]
    long_flags = []
    short_flags = []
    for flag in flags:
      if len(flag) == 1:
        short_flags.append(flag)
      else:
        long_flags.append(flag)
    option = {
      'key': key,
      'long': long_flags,
      'short': short_flags,
      'description': description,
    }
    self.options.append(option)

  # Parses `args`, or sys.argv if `args` is not specified.
  #
  # The function's return tuple dependends on the specified `ship` and whether
  # any options were added.
  #
  # If the specified `ship` was a function then the returned tuple will look
  # like `(funtion_args: list,)`. If, however, any options were added, then
  # return tuple will be `(funtion_args: list, options: dict)`.
  #
  # If the specified `ship` was an initialised object, then the output will
  # be `(function: callable, funtion_args: list)`. And, naturally, if any
  # options were added then the tuple will look like this
  # `(function: callable, funtion_args: list, options: dict)`.
  def parse(self, args: list = None) -> tuple:
    # Retrieving args
    if args is None:
      args = sys.argv[1:]
    # Categorising args
    args, long_opts, short_opts = categorise_args(args)
    # Parsing options and printing help if needed
    if self.add_help:
      self.add_option(
        'help',
        ['help', 'h'],
        'Prints this page',
      )
    parsed_options = parse_options(self, long_opts, short_opts)
    if self.add_help:
      if parsed_options.get('help'):
        self.print_help()
        sys.exit(os.EX_OK)
      parsed_options.pop('help')
    # Getting chosen function
    ship_callable = callable(self.ship)
    if ship_callable:
      function = self.ship
      command = None
    else:
      if not args:
        self.on_usage_error(
          'No command specified.\n'
          f"Try '{self.program} --help' for more information."
        )
      available_commands = get_object_commands(self.ship)
      command = args.pop(0)
      function = available_commands.get(command)
      available_commands = ', '.join(available_commands.keys())
      if function is None:
        self.on_usage_error(
          f"command '{command}' not recognised.\n"
          f'Available commands: {available_commands}'
        )
    # Checking arguments
    required_args = get_function_args(function)
    n_required_args = len(required_args)
    if not ship_callable:
      if n_required_args == 0:
        function_name = function.__name__
        class_name = self.ship.__class__.__name__
        raise ParsingError(
          f"Function '{function_name}' of '{class_name}' is missing the 'self' parameter"
        )
      args.insert(0, self.ship)
    n_args = len(args)
    if required_args[-1][0] == '*':
      if n_args < n_required_args - 1:
        self.on_missing_arguments(required_args[n_args : n_required_args - 1])
    else:
      if n_args < n_required_args:
        self.on_missing_arguments(required_args[n_args:])
      if n_args > n_required_args:
        self.on_usage_error('too many arguments.', command)
    # Returning
    return_list = []
    if not ship_callable:
      return_list += [function, args]
    else:
      return_list.append(args)
    if parsed_options:
      return_list.append(parsed_options)
    if len(return_list) == 1:
      return return_list[0]
    return tuple(return_list)

  # Prints the help page.
  def print_help(self):
    sections = []
    compact = self.compact_help
    if callable(self.ship):
      sections += get_singlecommand_sections(self)
      if compact is None:
        compact = True
    else:
      sections += get_multicommand_sections(self)
      if compact is None:
        compact = False
    sections.append(get_options_help_section(self.options))
    sections = [section for section in sections if section]
    if compact:
      separator = '\n'
    else:
      separator = '\n\n'
    print(separator.join(sections))

  def on_usage_error(self, text: str, command: str = None):
    prefix = self.program + ':'
    if command:
      prefix += ' ' + command + ':'
    print(prefix + ' ' + text, file=sys.stderr)
    if hasattr(os, 'EX_USAGE'):
      sys.exit(os.EX_USAGE)
    else:
      sys.exit(64)

  def on_missing_arguments(self, missing_args: str, command: str = None):
    missing_args = to_posix_args(missing_args)
    if len(missing_args) == 1:
      self.on_usage_error(f'missing argument {missing_args[0]}', command)
    else:
      missing_args = ' '.join(missing_args)
      self.on_usage_error(f'missing arguments {missing_args}', command)
