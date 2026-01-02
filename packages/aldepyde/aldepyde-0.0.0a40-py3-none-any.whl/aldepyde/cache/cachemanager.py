import os
import sys
import json
from dataclasses import dataclass
from io import BytesIO

from aldepyde.env import ENV
from .utils import _parse_memory, _convert_memory_bytes, _convert_memory_bits


def requires_enabled(func):
    def wrapper(cls, *args, **kwargs):
        if hasattr(cls, "enabled") and cls.enabled and cls._initialized:
            return func(cls, *args, **kwargs)
        else:
            return None
    return wrapper


class CacheManager():
    def __init__(self, path=None, initialize=False):
        if not initialize:
            self._initialized = False
            return
        self._initialized = True
        self.enable()
        self._cache_marker = ".aldepyde_cache"
        self.fingerprint = "adpy."
        if path is None:
            self._path = ENV.get_default_path()
        else:
            self._path = path
        if os.path.exists(self.marker_location()):
            try:
                self.load_manager()
            except json.decoder.JSONDecodeError:
                self.load_defaults()
                self.save_settings()
        else:
            self.load_defaults()
            self.save_settings()

    @requires_enabled
    def set_cache_location(self, directory):
        try:
            os.makedirs(directory, exist_ok=True)
            if not os.path.isfile(os.path.join(directory, self._cache_marker)):
                self.save_settings(os.path.join(directory, self._cache_marker))
        except OSError:
            print(f"Error establishing cache directory at : {directory}", file=sys.stderr)

    @requires_enabled
    def set_max_memory(self, memory: str) -> None:
        self.max_memory = _parse_memory(memory)
        self.save_settings()

    @requires_enabled
    def cache_location(self):
        return self._path

    @requires_enabled
    def _dump_settings(self):
        return f"{self.__dict__}"

    @requires_enabled
    def marker_location(self) -> str:
        return os.path.join(self._path, self._cache_marker)

    # Saves settings to a location. If a path is specified, the results are saved to that location
    # but the cache location is NOT changed. Use self.set_cache_location() instead for this
    @requires_enabled
    def save_settings(self, path=None):
        if path is None:
            path = self.marker_location()
        elif os.path.isdir(path):
            path = os.path.join(path, self._cache_marker)
        with open(path, 'w') as fp:
            # for v in vars(self):
            #     print(v)
            fp.write(json.dumps(vars(self), indent=2))

    @requires_enabled
    def load_manager(self, path=None):
        if path is None:
            path = self.marker_location()
        elif os.path.isdir(path):
            path = os.path.join(path, self._cache_marker)
        with open(path, 'r') as fp:
            settings = json.load(fp)
            for setting in settings:
                self.__dict__[setting] = settings[setting]
        self._path = os.path.dirname(path)

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def _enabled_and_initialized(self):
        return self.enabled and self._initialized

    def is_enabled(self):
        return self.enabled

    @requires_enabled
    def load_defaults(self):
        self._cache_marker = ".aldepyde_cache"
        self.version = "1.0.0"
        self.max_memory = _parse_memory('2gib')
        self.enabled = True

    @requires_enabled
    def _inside(self, f) -> str:
        return os.path.join(self._path, f)

    @requires_enabled
    def peek(self, name):
        files = []
        for file in self.list_cache():
            if name.lower() in file.lower():
                files.append(file)
        return files

    # Requires a filename, not a path. The path will be self._path
    @requires_enabled
    def _is_safe_to_delete(self, filename):
        return (os.path.exists(self.marker_location())
                and (filename in os.listdir(self._path) or filename.startswith(self._path))
                and self.exists(filename)
                and (filename.startswith(self.fingerprint)) or os.path.basename(filename).startswith(self.fingerprint))

    @requires_enabled
    def delete_from_cache(self, filename) -> bool | None:
        if not self._enabled_and_initialized():
            return None
        if self._is_safe_to_delete(filename):
            os.remove(self._inside(filename))
            return True
        return False

    @requires_enabled
    def clear_cache(self) -> None:
        if not self._enabled_and_initialized():
            return None
        for file in os.listdir(self._path):
            if self._is_safe_to_delete(file):
                os.remove(self._inside(file))
                print(f"Deleting {file}")

    # @requires_enabled
    # def get(self, file) -> str | None:
    #     if not self._enabled_and_initialized():
    #         return None
    #     return self._inside(file) if self.exists(file) else None

    # TODO Create a with cache_manager.open(...) setup here
    # def open(self, filename):
    #     pass

    @requires_enabled
    def retrieve(self, filename:str) -> str|None:
        if self.exists(filename):
            return self._inside(filename)
        else:
            return None

    @requires_enabled
    def exists(self, filename):
        return os.path.isfile(self._inside(filename))

    @requires_enabled
    def list_cache(self) -> list:
        all_files = []
        for base, _, paths in os.walk(self._path):
            for path in paths:
                all_files.append(os.path.join(base, path))
        return all_files

    @requires_enabled
    def cache_usage(self, output=None):
        total_size = 0
        for filepath in self.list_cache():  # Yes this jumps from O(n^2) to O(n^3), but It's probably fine. Just don't use a petabyte-sized cache
            total_size += os.path.getsize(filepath)
        if output == 'percentage':
            return total_size / self.max_memory
        elif output == 'bytes':
            return _convert_memory_bytes(total_size)
        elif output == 'bits':
            return _convert_memory_bits(total_size)
        return total_size

    @dataclass
    class EvictionResult():
        success: bool
        deleted: list[str]
        error: Exception | None = None

        @property
        def error_message(self) -> str | None:
            return str(self.error) if self.error is not None else None

    @requires_enabled
    def evict(self, nbytes) -> EvictionResult | None:
        if not self._enabled_and_initialized():
            return None
        cache_list = self.list_cache()
        # Clear entries in cache by age
        cache_list.sort(key=os.path.getatime)
        deleted = []
        while nbytes + self.cache_usage() > self.max_memory:
            if not cache_list:
                return self.EvictionResult(False, deleted)
            file = cache_list.pop(0)
            try:
                if self.delete_from_cache(file):
                    deleted.append(file)
            except FileNotFoundError as error:
                return self.EvictionResult(False, deleted, error)
        return self.EvictionResult(True, deleted)

    @requires_enabled
    def clean(self) -> EvictionResult:
        return self.evict(0)

    @requires_enabled
    def save_to_cache(self, stream, filename) -> bool | None:
        filename = os.path.join(self._path, filename)
        if not self._enabled_and_initialized():
            return None
        self.evict(stream.getbuffer().nbytes)
        with open(filename, "wb") as fp:
            fp.write(stream.read())
        stream.seek(0)
        return True
