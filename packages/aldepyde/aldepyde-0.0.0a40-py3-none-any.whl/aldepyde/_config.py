import re
import sys
import os
import json
# TODO Consider version information in config
# from aldepyde import __version__

class _configuration():

    class VERSION_SETTINGS():  # There's probably a better way to do this, but it feels neat so I'm keeping it for now
        def __init__(self):
            self.settings = {
                "verbose": False,
                "angle_mode": "degrees",
                "enable_cache": True,
                "cache_path": os.path.join(os.getcwd(), "aldepyde_cache"),
                "cache_max_memory": "500mib"
            }
    def __init__(self):
        s = self.VERSION_SETTINGS()
        self._settings = s.settings
        self._setters = { # TODO Finish fixing this
                "verbose": self.SetVerbose,
                "angle_mode": self.SetAngleMode,
                "enable_cache": self.SetEnableCache,
                "cache_path": self.SetCachePath,
                "cache_max_memory": self.SetCacheMaxMemory
            }

    # def _Verify(self, key, value) -> None:
    #     if value not in self._setters[key][1]:
    #         print(f"Incorrect value for ({key} <-- {value})\n\tAllowed values: {self._setters[key][1]}", file=sys.stderr)
    #         raise ValueError("See above")

    def _Verify(self, key: str, accepted: list, value: object) -> None:
        if True not in [True for x in accepted if value == x or (isinstance(x, type) and isinstance(value, x))]:
            raise ValueError
        # if value not in accepted:
        #     # print(f"Incorrect value for ({key} <-- {value})\n\tAllowed values: {accepted}", file=sys.stderr)
        #     raise ValueError(f"Incorrect value for ({key} <-- {value})\n\tAllowed values: {accepted}")

    def __getitem__(self, item):
        return self._settings[item]

    def GetVerbose(self) -> bool:
        return self._settings['verbose']

    def SetVerbose(self, enabled: bool) -> None:
        # I'm choosing to not be defensive here.
        # Ima be honest, if you break the module with a verbosity boolean, that's on you
        self._settings['verbose'] = enabled

    def GetAngleMode(self) -> str:
        return self._settings['angle_mode']

    def SetAngleMode(self, a_type: str) -> None:
        self._Verify('angle_mode', a_type)
        self._settings['angle_mode'] = a_type

    def SetEnableCache(self, enabled:bool) -> None:
        self._Verify('enable_cache', [bool], enabled)
        self._settings['enable_cache'] = enabled

    def SetCachePath(self, path: str) -> None:
        # TODO Consider making the new cache directory immediately
        self._settings['cache_path'] = path

    def GetCachePath(self) -> str:
        return self._settings['cache_path']

    def GetEnabledCache(self) -> bool:
        return self._settings['enable_cache']

    def SetCacheMaxMemory(self, max_memory: str|int) -> None:
        max_memory = str(max_memory)
        if re.fullmatch("[0-9]*[kmg]i?b", max_memory) is None:
            raise ValueError
        self._settings['cache_max_memory'] = max_memory

    def GetCacheMaxMemory(self) -> str:
        return self._settings['cache_max_memory']

    ####################
    def Load(self, s: dict | str, ignore_missing=False) -> None:
        if isinstance(s, str):
            if os.path.exists(s):  # Try and read as a json file
                with open(s, "r") as jp:
                    s = json.load(jp)
            else:  # Try and read as a json string
                s = json.loads(s)
        extra_settings = "".join([f"\t-{k}\n" for k in s.keys() if k not in self._setters.keys()])
        if len(extra_settings) != 0:
            print(f"Please remove the following config settings:\n{extra_settings}", file=sys.stderr)
            raise KeyError("Input config does not match expectations")
        missing_settings = "".join([f"\t-{k} : {v[1]}\n" for k, v in self._setters.items() if k not in s.keys()])
        if len(missing_settings) != 0 and not ignore_missing:
            print(f"Please include the following config settings:\n{missing_settings}", end="", file=sys.stderr)
            raise KeyError("Input config does not match expectations")
        if ignore_missing:
            vs = self.VERSION_SETTINGS()
            self._settings = vs.settings
        for key in s.keys():
            self._setters[key][0](s[key])

    def GetConfig(self, as_string=False, indent="") -> dict | str:
        if as_string:
            return json.dumps(self._settings, indent=indent)
        return self._settings

    def Save(self, path: str="config.json", indent: str=""):
        with open(path, "w") as jp:
            json.dump(self._settings, jp, indent=indent)

