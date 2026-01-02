import os
import sys

class ENV():
    CACHE_PATH = "ALDEPYDE_CACHE_DIRECTORY"
    CACHE_REPAIR = "ALDEPYDE_REPAIR_POLICY"
    VERBOSE = "ALDEPYDE_VERBOSE_POLICY"
    APP = "aldepyde"

    @staticmethod
    def set_default_env_vars():
        ENV.set_env(ENV.CACHE_PATH, ENV.get_default_path())
        ENV.set_env(ENV.CACHE_REPAIR, "fail")
        ENV.set_env(ENV.VERBOSE, "false")

    @staticmethod
    def set_env(var, val, force=True):
        if not hasattr(ENV, var):
            raise ValueError(f"{var} is not a valid aldepyde.ENV key")
        env_var = getattr(ENV, var)

        if not force and env_var in os.environ:
            print(f"Aldepyde variable {env_var} is already set. Use force=True to override")
            return

        os.environ[env_var] = str(val)
        print(f"Set {env_var} = {val}")
        return

    # TODO Test all this somehow
    @staticmethod
    def get_default_path():
        platform = sys.platform
        xdg = os.getenv('XDG_CACHE_HOME')
        if xdg:
            return os.path.join(os.path.expanduser(xdg), ENV.APP)
        if platform == "win32": # Windows
            base = os.getenv("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
            return os.path.join(base, ENV.APP, "Cache")
        elif sys.platform == "darwin": # MacOS
            return os.path.join(os.path.expanduser("~/Library/Caches"), ENV.APP)
        else: # Linux without XDG set
            return os.path.join(os.path.expanduser("~/.cache"), ENV.APP)
