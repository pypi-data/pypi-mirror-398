from ._decorators import deprecated

class Store():
    def __init__(self, profile="main"):
        self._default = dict()
        self._storage = dict()
        self._profile = profile
        if self._profile:
            self._storage[self._profile] = dict()

    @property
    def profile(self):
        return self._profile

    @profile.setter
    def profile(self, value):
        self._profile = value

    @property
    def profiles(self):
        return list(self._storage.keys())

    @deprecated
    def globals(self, **kwargs):
        self.default(**kwargs)

    def default(self, **kwargs):
        self._default.update(**kwargs)

    def reset(self):
        self._storage = dict()
        if self._profile:
            self._storage[self._profile] = dict()

    def _get_storage_of_profile(self):
        if self._profile not in self._storage:
            self._storage[self._profile] = dict()
        return self._storage[self._profile]

    def update(self, *args, **kwargs):
        self._get_storage_of_profile().update(*args, **kwargs)

    def __contains__(self, item):
        return item in self._get_storage_of_profile()

    def __getitem__(self, key):
        return self._get_storage_of_profile().get(key, self._default.get(key, None))

    def __setitem__(self, key, value):
        _storage = self._get_storage_of_profile()
        _storage[key] = value

    def __delitem__(self, key):
        _storage = self._get_storage_of_profile()
        if key in _storage:
            del _storage[key]

    def __getattr__(self, name):
        """Intercepts attribute access and forwards it to the storage of current profile."""
        return getattr(self._get_storage_of_profile(), name)
