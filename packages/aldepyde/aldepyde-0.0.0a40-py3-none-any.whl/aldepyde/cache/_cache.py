# # Data cache handler
# import shutil
# import os
# import requests
# import re # We're getting spicy with this
# import gzip
# from io import BytesIO, TextIOWrapper
# import json
# from dataclasses import dataclass
# from aldepyde.env import ENV
#
#
# class _cache_handler():
#     class CachePointerException(Exception):
#         pass
#
#     @dataclass
#     class EvictionResult():
#         success: bool
#         deleted: list[str]
#         error: Exception | None = None
#
#         @property
#         def error_message(self) -> str | None:
#             return str(self.error) if self.error is not None else None
#
#     def __init__(self, enabled: bool=True, path: str=None, max_memory: str="2gib", null: bool=False):
#         self.null = null
#         if null:
#             self._enabled = False
#             return
#         self.cache_marker = ".aldepyde_cache"
#         self.version = "1.0.0"
#         if path is None:
#             self._path = ENV.get_default_path()
#         else:
#             self._path = path
#         if os.path.exists(os.path.join(self._path, self.cache_marker)):
#             marker_path = os.path.join(self._path, self.cache_marker)
#             try:
#                 self.load(marker_path)
#             except Exception as e:
#                 self._rectify_marker(marker_path)
#         else:
#             self._enabled = enabled
#             self._max_memory = self._parse_memory(max_memory) # Memory in MiB
#         self.designate_cache(self._path)
#
#     def _rectify_marker(self, marker_path): # Since settings have not been loaded, this MUST come from an environment variable
#         env = os.getenv(ENV.CACHE_REPAIR)
#         print(os.environ)
#         if env is None:
#             raise RuntimeError("No repair policy set. Please set environment variable 'ALDEPYDE_REPAIR_POLICY'"
#                                " to one of the following: ['fail', 'replace', 'backup']")
#         elif env.lower() == "replace": # Just overwrite the old file with defaults
#             self._set_defaults()
#         elif env.lower() == "backup": # Rename the old file to filename.bak
#             marker_path = os.path.join(self._path, self.cache_marker)
#             os.rename(marker_path, marker_path + ".bak")
#             self._set_defaults()
#         elif env.lower() == "fail": # Raise an exception
#             raise RuntimeError(f"The aldepyde module cache has been corrupted.\n"
#                                f"Rerun your program after setting {ENV.CACHE_REPAIR} to either 'replace' or 'backup'"
#                                f"to repair the cache.")
#         else: # Incorrect or unknown command
#             raise ValueError(f"Unkown value set to environment variable {ENV.CACHE_REPAIR}. Valid inputs are ['replace', 'backup', 'fail']\n"
#                              f"\t{ENV.CACHE_REPAIR}={env}")
#
#     def _set_defaults(self):
#         self._enabled = True
#         self._max_memory = self._parse_memory("2gib")
#
#     def load(self, path):
#         with open(path, "r") as fp:
#             settings = json.load(fp)
#         self._enabled = settings['enabled']
#         self._max_memory = settings['max_memory']
#
#     def _save_cache(self):
#         marker = os.path.join(self._path, self.cache_marker)
#         # with open(marker, "r") as fp:
#         #     settings = json.load(fp)
#         settings = {}
#         settings["version"] = self.version
#         settings["enabled"] = self._enabled
#         settings["path"] = self._path
#         settings["max_memory"] = self._max_memory
#         with open(marker, "w") as fp:
#             fp.write(json.dumps(settings, indent=2))
#
#     def designate_cache(self, path) -> None:
#         os.makedirs(self._path, exist_ok=True)
#         self._save_cache()
#         print(os.path.join(path, self.cache_marker))
#         with open(os.path.join(path, self.cache_marker), "w") as fp:
#             fp.write("{}")
#
#     def _verify_cache_directory(self, path: str) -> bool:
#         return os.path.exists(os.path.join(path))
#
#     def _is_safe_to_delete(self, path: str) -> bool:
#         marker_path = os.path.join(path, self.cache_marker)
#         return (
#             os.path.exists(marker_path) and
#             os.path.isdir(path) and
#             os.path.abspath(path) != "/" and
#             os.path.basename(path).startswith("aldepyde_cache")
#         )
#
#     def _get_default_cache_path(self) -> str:
#         return os.path.join(
#             os.getenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache")), "aldepyde")
#
#
#
#     def set_enabled(self, enabled:bool) -> None:
#         self._enabled = enabled
#         self._save_cache()
#
#     def set_path(self, path:str, cache_policy:str=None) -> None:
#         if cache_policy.lower() == "move":
#             shutil.move(self._path, path)
#         elif cache_policy.lower() == "copy":
#             shutil.copy(self._path, path)
#         self._path = path
#         self._save_cache()
#
#
#     def set_max_memory(self, memory: str) -> None:
#         self._max_memory = self._parse_memory(memory)
#         self._save_cache()
#
#     def _parse_memory(self, memory: str) -> int:
#         ALLOWED_PREFIX = "bkmgt" # No, you don't get to use petabytes
#         full_re = f"[0-9]+[{ALLOWED_PREFIX}]?i?b?"
#         numeric_re = "[0-9]+"
#
#         if memory.isnumeric():
#             memory += "mib"
#         if re.fullmatch(full_re, memory, flags=re.IGNORECASE) is None:
#             raise ValueError(f"Requested memory must be of the following form: {full_re}")
#
#         match = re.match(numeric_re, memory)
#         numeric = int(memory[:match.span()[1]])
#         unit = memory[match.span()[1]:]
#         base = 1024 if "i" in unit else 1000
#         multiple = base**(ALLOWED_PREFIX.index(unit[0].lower()))
#         return numeric * multiple
#
#     def grab_url(self, url: str, filename: str) -> BytesIO:
#         # Return a requested file as a BytesIO stream from a URL or the cache
#         if not self.in_cache(filename):
#             response = requests.get(url)
#             response.raise_for_status()
#             stream_io = BytesIO(response.content)
#             self.save_to_cache(stream_io, filename)
#             with gzip.open(stream_io, "r") as gz:
#                 return BytesIO(gz.read())
#         else:
#             return self.extract_from_cache(filename)
#
#     def clear_cache(self) -> None:
#         if self._is_safe_to_delete(self._path):
#             for p in os.listdir(self._path):
#                 path = os.path.join(self._path, p)
#                 if os.path.isdir(path):
#                     shutil.rmtree(path)
#                 else:
#                     os.remove(path)
#
#     # def SaveCache(self, destination, compress=False):
#     #     if not compress:
#
#
#     def delete_cache(self) -> None:
#         if self._is_safe_to_delete(self._path):
#             shutil.rmtree(self._path)
#
#     def cache_replace(self, nbytes) -> EvictionResult:
#         cache_list = self.list_cache()
#         cache_list.sort(key=os.path.getatime)
#         deleted = []
#         while nbytes + self.cache_usage() > self._max_memory:
#             if not cache_list:
#                 return self.EvictionResult(False, deleted)
#             file = cache_list.pop(0)
#             try:
#                 os.remove(file)
#                 deleted.append(file)
#             except FileNotFoundError as error:
#                 return self.EvictionResult(False, deleted, error)
#         return self.EvictionResult(True, deleted)
#
#
#     def _make_cache(self) -> None:
#         if not os.path.isdir(self._path):
#             os.mkdir(self._path)
#
#
#
#     # TODO This could maybe be expanded to look for compressed/decompressed versions of a file, but that may cause issues later
#     def in_cache(self, filename: str) -> bool:
#         if not self._enabled: # If the cache is disabled, we behave as if the file doesn't exist
#             return False
#         if os.path.exists(os.path.join(self._path, filename)):
#             return True
#         return False
#
#     def extract_from_cache(self, filename:str) -> BytesIO | None:
#         if self.in_cache(filename):
#             _, file_extension = os.path.splitext(filename)
#             if file_extension == ".gz":
#                 with gzip.open(os.path.join(self._path, filename), "rb") as gz:
#                     return BytesIO(gz.read())
#             else:
#                 with open(filename, "rb") as fp:
#                     stream = BytesIO()
#                     stream.write(fp.read())
#                     return stream
#         return None
#
#     def list_cache(self) -> list:
#         all_files = []
#         for base, _, paths in os.walk(self._path):
#             for path in paths:
#                 all_files.append(os.path.join(base, path))
#         return all_files
#
#     def cache_usage(self, percentage: bool=False) -> float | int:
#         total_size = 0
#         for filepath in self.list_cache(): # Yes this jumps from O(n^2) to O(n^3), but It's probably fine. Just don't use a petabyte-sized cache
#             total_size += os.path.getsize(filepath)
#         if percentage:
#             return total_size / self._max_memory
#         return total_size
#
#
#     def save_to_cache(self, stream, filename) -> bool:
#         filename = os.path.join(self._path, filename)
#         self._make_cache()
#         print(stream.getbuffer().nbytes)
#         if not self._enabled:
#             return False
#
#         # Clear entries in cache by age
#         cache_list = self.list_cache()
#         cache_list.sort(key=os.path.getctime)
#         while stream.getbuffer().nbytes + self.cache_usage() > self._max_memory:
#             # print(f"Removing {cache_list[0]}")
#             os.remove(cache_list[0])
#             cache_list.pop(0)
#         if stream.getbuffer().nbytes + self.cache_usage() < self._max_memory:
#             with open(filename, "wb") as fp:
#                 fp.write(stream.read())
#         stream.seek(0)
#         return True
#
