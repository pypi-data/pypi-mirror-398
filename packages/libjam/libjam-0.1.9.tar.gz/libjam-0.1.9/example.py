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
