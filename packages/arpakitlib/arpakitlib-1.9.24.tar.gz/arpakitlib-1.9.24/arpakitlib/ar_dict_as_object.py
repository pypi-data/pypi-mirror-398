from arpakitlib.ar_json_util import transfer_data_to_json_str


class DictAsObject:
    def __init__(self, data: dict | list):
        self._real_data = data

    def __getattr__(self, item):
        if isinstance(self._real_data, dict):
            try:
                return self.wrap(self._real_data[item])
            except KeyError:
                raise AttributeError(item)

        raise AttributeError(item)

    def __getitem__(self, key):
        if isinstance(self._real_data, (list, dict)):
            return self.wrap(self._real_data[key])
        raise TypeError(f"{type(self._real_data)} is not subscriptable")

    def __len__(self):
        return len(self._real_data)

    def __repr__(self):
        return transfer_data_to_json_str(self._real_data, beautify=True)

    @staticmethod
    def wrap(value):
        if isinstance(value, (dict, list)):
            return DictAsObject(value)
        return value

    def get_raw_from_dict(self, *, key: str, allow_non_exist: bool = True):
        """
        Возвращает значение напрямую из _real_data, без wrap
        """

        if not isinstance(self._real_data, dict):
            raise TypeError("not isinstance(self._real_data, dict)")

        if key not in self._real_data:
            if allow_non_exist is True:
                return None

        return self._real_data[key]
