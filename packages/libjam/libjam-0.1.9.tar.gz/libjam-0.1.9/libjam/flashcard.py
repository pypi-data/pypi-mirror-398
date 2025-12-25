# Internal imports
from .typewriter import Typewriter

typewriter = Typewriter()


# Used for getting input from the user.
class Flashcard:
  def yn_prompt(self, question: str) -> bool:
    while True:
      user_input = input(f'{question} [y/n]: ')
      user_input = user_input.strip().lower()
      if user_input in ('y', 'yes'):
        return True
      elif user_input in ('n', 'no'):
        return False

  def choose(
    self,
    prompt: str,
    items: iter[str],
    *prompt_styles: Typewriter.Style
    or Typewriter.Colour
    or Typewriter.BackgroundColour,
  ) -> str:
    n_items = len(items)
    # Creating the prompt
    prompt = f'{prompt} (1-{n_items}, 0 to abort):'
    for style in prompt_styles:
      prompt = typewriter.stylise(style, prompt)
    prompt += ' '
    # Printing available items
    printable_items = []
    for i, item in enumerate(items, start=1):
      printable_items.append(f'{i}) {item}')
    printable_items = typewriter.list_to_columns(printable_items, spacing=2)
    print(printable_items + '\n')
    # Getting user input
    while True:
      choice = input(prompt).strip()
      if not choice:
        continue
      elif choice == '0':
        return None
      elif choice in [str(n) for n in range(1, n_items + 1)]:
        chosen_item = items[int(choice) - 1]
        break
      elif choice in items:
        chosen_item = choice
        break
      else:
        print('Invalid input.')
    # Returning
    return chosen_item
