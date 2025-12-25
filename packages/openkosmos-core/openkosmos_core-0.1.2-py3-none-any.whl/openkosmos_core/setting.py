from openkosmos_core import arguments


class Setting(arguments.Argument):
    def __init__(self, params=None):
        super().__init__(instance=self)
        if params is not None:
            for name, value in params.items():
                self.param(name, default=value.get("default"), help=value.get("help"),
                           action=value.get("action"))
        self.parse()
        Setting.logger("setting").info(str(self))

    def get_param(self, name):
        return self.get(name)

    def get_str_param(self, name, default_value=None):
        value = self.get(name)
        if value is not None:
            return str(value)
        else:
            return default_value

    def get_int_param(self, name, default_value=None):
        value = self.get(name)
        if value is not None:
            return int(value)
        else:
            return default_value

    def get_float_param(self, name, default_value=None):
        value = self.get(name)
        if value is not None:
            return float(value)
        else:
            return default_value

    def get_bool_param(self, name, default_value=None):
        value = self.get(name)
        if value is not None:
            return bool(value)
        else:
            return default_value
