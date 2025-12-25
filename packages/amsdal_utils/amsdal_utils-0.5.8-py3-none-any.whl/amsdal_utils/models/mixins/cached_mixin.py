import inspect


class CachedMixin:
    def invalidate_cache(self) -> None:
        self._invalidate_cached_properties()
        self._invalidate_lru_cache()

    def _invalidate_cached_properties(self) -> None:
        for name, member in inspect.getmembers(self.__class__):
            if inspect.isfunction(member) and hasattr(member, '__cached_property__'):
                delattr(self, name)

    def _invalidate_lru_cache(self) -> None:
        for _, member in inspect.getmembers(self.__class__):
            if inspect.isfunction(member) and hasattr(member, 'cache_info') and member.cache_info:
                member.cache_info.cache_clear()
