# Imports
import os
import io
import zipfile
import tarfile
import rarfile
import py7zr


# Internal classes
class JamTarFile:
  def __init__(self, tar: tarfile.TarFile):
    self.tar = tar
    self.members = self.tar.getmembers()
    self.n_members = len(self.members)
    self.extracted = 0
    self.archive_basename = None

  @classmethod
  def open(cls, *args, **kwargs):
    tar = tarfile.open(*args, **kwargs)
    return cls(tar)

  def extractall(self, path: str, progress_function: callable = None):
    self.extract_location = path
    self.progress_function = progress_function
    self.tar.extractall(path, filter=self.filter)

  def filter(
    self, member: tarfile.TarInfo, path: str, /
  ) -> tarfile.TarInfo | None:
    if self.progress_function:
      self.progress_function(self.extracted, self.n_members)
    self.extracted += 1
    member = tarfile.data_filter(member, path)
    if member:
      if not self.archive_basename:
        self.archive_basename = os.path.basename(member.name)
      member.name = member.name.removeprefix(self.archive_basename)
      member.name = self.extract_location + member.name
    return member


class SevenZipCallbacks(py7zr.callbacks.ExtractCallback):
  def __init__(self, to_extract: int, progress_function: callable):
    self.extracted = 0
    self.to_extract = to_extract
    self.progress_function = progress_function

  def report_start_preparation(self):
    self.progress_function(self.extracted, self.to_extract)

  def report_start(self, file, size):
    self.progress_function(self.extracted, self.to_extract)
    self.extracted += 1

  def report_end(self, file, size):
    pass

  def report_postprocess(self):
    pass

  def report_update(self, size):
    pass

  def report_warning(self, message):
    pass


# Extract functions
def generic_extract(
  archive_object: zipfile.ZipFile or rarfile.RarFile,
  extract_location: str,
  progress_function: callable = None,
):
  archived_files = archive_object.namelist()
  to_extract = len(archived_files)
  extracted = 0
  for archived_file in archived_files:
    if progress_function:
      progress_function(extracted, to_extract)
    extracted += 1
    archive_object.extract(archived_file, path=extract_location)


def extract_zip(
  archive: str or bytes,
  extract_location: str,
  progress_function: callable = None,
):
  if type(archive) is str:
    archive = open(archive, 'rb').read()
  archive_object = zipfile.ZipFile(io.BytesIO(archive))
  generic_extract(archive_object, extract_location, progress_function)


def extract_rar(
  archive: str or bytes,
  extract_location: str,
  progress_function: callable = None,
):
  if type(archive) is str:
    archive = open(archive, 'rb').read()
  archive_object = rarfile.RarFile(io.BytesIO(archive))
  generic_extract(archive_object, extract_location, progress_function)


def generic_tar_extract(
  archive: str or bytes,
  archive_type: str,  # 'gz', 'xz' or ''
  extract_location: str,
  progress_function: callable = None,
):
  if type(archive) is str:
    archive = open(archive, 'rb').read()
  if archive_type:
    archive_object = JamTarFile.open(
      mode=f'r:{archive_type}',
      fileobj=io.BytesIO(archive),
    )
  else:
    archive_object = JamTarFile.open(
      mode='r',
      fileobj=io.BytesIO(archive),
    )
  archive_object.extractall(extract_location, progress_function)


def extract_tar(
  archive: str or bytes,
  extract_location: str,
  progress_function: callable = None,
):
  generic_tar_extract(archive, '', extract_location, progress_function)


def extract_tar_gz(
  archive: str or bytes,
  extract_location: str,
  progress_function: callable = None,
):
  generic_tar_extract(archive, 'gz', extract_location, progress_function)


def extract_tar_xz(
  archive: str or bytes,
  extract_location: str,
  progress_function: callable = None,
):
  generic_tar_extract(archive, 'xz', extract_location, progress_function)


def extract_7z(
  archive: str or bytes,
  extract_location: str,
  progress_function: callable = None,
):
  if type(archive) is str:
    archive = open(archive, 'rb').read()
  archive_object = py7zr.SevenZipFile(io.BytesIO(archive))
  archived_files = archive_object.namelist()
  to_extract = len(archived_files)
  if progress_function:
    callback = SevenZipCallbacks(to_extract, progress_function)
  else:
    callback = None
  archive_object.extract(
    extract_location,
    recursive=True,
    callback=callback,
  )
