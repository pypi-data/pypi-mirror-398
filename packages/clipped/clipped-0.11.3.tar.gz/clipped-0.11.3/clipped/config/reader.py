from clipped.config.constants import NO_VALUE_FOUND
from clipped.config.parser import ConfigParser
from clipped.config.spec import ConfigSpec


class ConfigReader:
    _CONFIG_SPEC = ConfigSpec
    _CONFIG_PARSER = ConfigParser

    def __init__(self, **data):
        self._data = data
        self._requested_keys = set()
        self._secret_keys = set()
        self._local_keys = set()

    @classmethod
    def read_configs(cls, config_values):  # pylint:disable=redefined-outer-name
        config = cls._CONFIG_SPEC.read_from(config_values)  # pylint:disable=redefined-outer-name
        return cls(**config) if config else None

    def keys_startswith(self, term):
        return [k for k in self._data if k.startswith(term)]

    def keys_endswith(self, term):
        return [k for k in self._data if k.endswith(term)]

    def has_key(self, key):
        return key in self._data

    @property
    def data(self):
        return self._data

    @property
    def requested_keys(self):
        return self._requested_keys

    @property
    def secret_keys(self):
        return self._secret_keys

    @property
    def local_keys(self):
        return self._local_keys

    def get_requested_data(
        self, include_secrets=False, include_locals=False, to_str=False
    ):
        data = {}
        for key in self._requested_keys:
            if not include_secrets and key in self._secret_keys:
                continue
            if not include_locals and key in self._local_keys:
                continue
            value = self._data[key]
            data[key] = "{}".format(value) if to_str else value
        return data

    def get(
        self,
        key: str,
        key_type: str,
        is_list=False,
        is_optional=False,
        is_secret=False,
        is_local=False,
        default=None,
        options=None,
    ):
        """
        Get the value corresponding to the key and converts it to `key_type`/`list(key_type)`.

        Args:
            key: the dict key.
            key_type: one of the supported types.
            is_list: If this is one element or a list of elements.
            is_optional: To raise an error if key was not found.
            is_secret: If the key is a secret.
            is_local: If the key is a local to this service.
            default: default value if is_optional is True.
            options: list/tuple if provided, the value must be one of these values.

        Returns:
             `key_type`: value corresponding to the key parsed to key_type.
        """
        kwargs = {}
        return self._get(
            key=key,
            parser_fct=self._CONFIG_PARSER.parse(key_type),
            is_list=is_list,
            is_optional=is_optional,
            is_secret=is_secret,
            is_local=is_local,
            default=default,
            options=options,
            **kwargs,
        )

    def get_value(self, key):
        return self._data.get(key, NO_VALUE_FOUND)

    def _get(
        self,
        key,
        parser_fct,
        is_list,
        is_optional,
        is_secret,
        is_local,
        default,
        options,
        **kwargs,
    ):
        """
        Get key from the dictionary made out of the configs passed.

        Args:
            key: the dict key.

        Returns:
             The corresponding value of the key if found.

        Raises:
            KeyError
        """
        value = self.get_value(key)
        parsed_value = parser_fct(
            key=key,
            value=value,
            is_list=is_list,
            is_optional=is_optional,
            default=default,
            options=options,
            **kwargs,
        )
        self._add_key(key, is_secret=is_secret, is_local=is_local)
        return parsed_value

    def _add_key(self, key, is_secret=False, is_local=False):
        self._requested_keys.add(key)
        if is_secret:
            self._secret_keys.add(key)
        if is_local:
            self._local_keys.add(key)
