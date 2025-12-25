#
# Pavlin Georgiev, Softel Labs
#
# This is a proprietary file and may not be copied,
# distributed, or modified without express permission
# from the owner. For licensing inquiries, please
# contact pavlin@softel.bg.
#
# 2023
#

def format_elapsed_time(seconds):
  time_units = [('d', 86400), ('h', 3600), ('m', 60), ('s', 1)]
  components = []
  for unit, factor in time_units:
    count = seconds // factor
    if count > 0:
      components.append(f"{int(count)}{unit}")
    seconds %= factor
  formatted_time = ' '.join(components)
  return formatted_time


def format_memory_size(size_in_bytes):
  if size_in_bytes < 1024:
    return f"{size_in_bytes} B"
  elif size_in_bytes < 1024 ** 2:
    return f"{size_in_bytes / 1024:.2f} KB"
  elif size_in_bytes < 1024 ** 3:
    return f"{size_in_bytes / (1024 ** 2):.2f} MB"
  elif size_in_bytes < 1024 ** 4:
    return f"{size_in_bytes / (1024 ** 3):.2f} GB"
  elif size_in_bytes < 1024 ** 5:
    return f"{size_in_bytes / (1024 ** 4):.2f} TB"
  else:
    return f"{size_in_bytes / (1024 ** 5):.2f} PB"