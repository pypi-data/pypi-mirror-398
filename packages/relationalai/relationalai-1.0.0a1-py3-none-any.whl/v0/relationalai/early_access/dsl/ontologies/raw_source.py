class RawSource:
    """
    A class representing a raw source.
    """

    _name: str
    _language: str
    _raw_source: str

    def __init__(self, language: str, source_name: str, raw_source: str):
        self._name = f'{source_name}__raw'
        self._language = language
        self._raw_source = raw_source

    @property
    def name(self):
        return self._name

    @property
    def language(self):
        return self._language

    @property
    def raw_source(self):
        return self._raw_source