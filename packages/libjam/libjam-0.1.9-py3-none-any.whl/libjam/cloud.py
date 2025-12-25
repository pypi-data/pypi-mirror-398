# Deals with network downloads.
class Cloud:
  # Downloads content from given link and returns it as bytes.
  def download(self, link: str, progress_function: callable = None) -> bytes:
    import requests

    if progress_function:
      response = requests.get(link, stream=True)
      total_size = int(response.headers.get('content-length', default=0))
      block_size = 1024
      steps = int(total_size / block_size) + 1
      for step in range(steps):
        progress_function(step * block_size, total_size)
        response.iter_content(block_size)
    else:
      response = requests.get(link)
    code = response.status_code
    if code != 200:
      raise ConnectionError(f"Error downloading '{link}'. Status code: {code}")
    return response.content
