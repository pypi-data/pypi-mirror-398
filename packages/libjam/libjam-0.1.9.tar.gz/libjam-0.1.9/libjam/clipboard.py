# Deals with lists.
class Clipboard:
  # Returns items present in both given lists.
  def get_duplicates(self, input_list1: list, input_list2: list) -> list:
    result_list = []
    for item in input_list1:
      if item in input_list2:
        result_list.append(item)
    result_list = self.deduplicate(result_list)
    return result_list

  # Duplicates a list.
  def deduplicate(self, input_list: list) -> list:
    result_list = list(set(input_list))
    return result_list

  # Removes all items which have duplicates.
  def remove_duplicates(self, input_list1: list, input_list2: list) -> list:
    result_list = []
    duplicates = self.get_duplicates(input_list1, input_list2)
    for item in input_list1:
      if item not in duplicates:
        result_list.append(item)
    return result_list
