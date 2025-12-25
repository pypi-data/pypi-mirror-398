import tomlkit
import os


class ConfigSubCommand:
    def __init__(self, conan, config_filename):
        self._conan_config = conan.config
        self._config_filename = config_filename

    def _initialize_config(self):
        conex_config = {
            "user": None,
            "channel": None
        }

        self._save_config(conex_config)

    def _save_config(self, conex_config):
        for pair in conex_config.items():
            item = pair[0]
            value = pair[1]
            if value is None:
                conex_config[item] = ""

        conan_config_home = self._conan_config.home()
        conex_config_path = os.path.join(conan_config_home, self._config_filename)

        with open(conex_config_path, "w") as conex_config_file:
            tomlkit.dump(conex_config, conex_config_file)

    def _load_config(self):
        conan_config_home = self._conan_config.home()
        conex_config_path = os.path.join(conan_config_home, self._config_filename)

        if not os.path.exists(conex_config_path):
            self._initialize_config()

        with open(conex_config_path, "r") as conex_config_file:
            toml_doc = tomlkit.load(conex_config_file)

        return ConfigSubCommand._tomlkit_to_popo(toml_doc)

    @staticmethod
    def _tomlkit_to_popo(d):
        try:
            result = getattr(d, "value")
        except AttributeError:
            result = d

        if isinstance(result, list):
            result = [ConfigSubCommand._tomlkit_to_popo(x) for x in result]
        elif isinstance(result, dict):
            result = {
                ConfigSubCommand._tomlkit_to_popo(key): ConfigSubCommand._tomlkit_to_popo(val) for key, val in result.items()
            }
        elif isinstance(result, tomlkit.items.Integer):
            result = int(result)
        elif isinstance(result, tomlkit.items.Float):
            result = float(result)
        elif isinstance(result, tomlkit.items.String):
            result = str(result)
            if result == "":
                result = None
        elif isinstance(result, tomlkit.items.Bool):
            result = bool(result)

        return result

    def load(self):
        return self._load_config()

    def get(self, item):
        _conex_config = self._load_config()
        if item not in _conex_config:
            raise ValueError()

        return _conex_config[item]

    def set(self, item: str, value):
        _conex_config = self._load_config()
        _conex_config[item] = value
        self._save_config(_conex_config)

    def remove(self, item):
        _conex_config = self._load_config()
        if item not in _conex_config:
            return ValueError()

        _conex_config.pop(item)
        self._save_config(_conex_config)
