from contextlib import suppress

from pydantic import BaseModel

from amsdal_utils.models.enums import Versions
from amsdal_utils.utils.singleton import Singleton


class ClassVersion(BaseModel):
    """
    Represents the version information of a class.

    Attributes:
        class_name (str): The name of the class.
        version (str): The version of the class.
        is_latest (bool): Indicates whether this version is the latest.
    """

    class_name: str
    version: str
    is_latest: bool


class ClassVersionManager(metaclass=Singleton):
    def __init__(self) -> None:
        self._class_versions_map: dict[str, dict[str, ClassVersion]] = {}

    def register_class_version(
        self,
        class_name: str,
        version: str,
        *,
        is_latest: bool,
        unregister_previous_versions: bool = True,
    ) -> None:
        """
        Registers a class version.

        Args:
            class_name (str): The name of the class.
            version (str): The version of the class.
            is_latest (bool): Indicates whether this version is the latest.
            unregister_previous_versions (bool, optional): Whether to unregister previous versions. Defaults to True.

        Returns:
            None
        """
        _registered_class_version = self._class_versions_map.get(class_name, {}).get(version)

        if _registered_class_version:
            return

        if unregister_previous_versions:
            with suppress(KeyError):
                del self._class_versions_map[class_name]

        class_version = ClassVersion(
            class_name=class_name,
            version=version,
            is_latest=is_latest,
        )
        _class_versions = self._class_versions_map.setdefault(class_name, {})

        if is_latest:
            for _class_version in _class_versions.values():
                _class_version.is_latest = False

            _class_versions[Versions.LATEST] = class_version

        _class_versions[version] = class_version

    def clear_versions(self) -> None:
        """
        Clears all registered class versions.

        Args:
            self: The instance of the class.

        Returns:
            None
        """
        self._class_versions_map.clear()

    def get_class_versions(self, class_name: str) -> list[ClassVersion]:
        """
        Retrieves all registered versions of a class.

        Args:
            class_name (str): The name of the class.

        Returns:
            list[ClassVersion]: A list of `ClassVersion` instances representing the registered versions of the class.
        """
        _class_versions = self._class_versions_map.setdefault(class_name, {})

        return [_class_versions[version] for version in _class_versions.keys() if version != Versions.LATEST]

    def get_latest_class_version(self, class_name: str) -> ClassVersion:
        """
        Retrieves the latest registered version of a class.

        Args:
            class_name (str): The name of the class.

        Returns:
            ClassVersion: An instance of `ClassVersion` representing the latest registered version of the class.

        Raises:
            Exception: If the latest version of the class is not registered.
        """
        try:
            return self._class_versions_map.setdefault(class_name, {})[Versions.LATEST]
        except KeyError as err:
            msg = f'The last version of class "{class_name}" is not registered'
            raise Exception(msg) from err
