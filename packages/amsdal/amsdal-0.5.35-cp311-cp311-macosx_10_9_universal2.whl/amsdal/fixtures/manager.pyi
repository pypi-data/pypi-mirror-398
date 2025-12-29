from _typeshed import Incomplete
from amsdal.fixtures.utils import process_fixture_value as process_fixture_value
from amsdal_models.classes.model import Model
from collections.abc import Generator
from pathlib import Path
from pydantic import BaseModel
from pydantic.fields import FieldInfo as FieldInfo
from typing import Any

logger: Incomplete

class FixtureData(BaseModel):
    class_name: str
    external_id: str
    order: float
    data: dict[str, Any]

class BaseFixturesManager:
    ORDER_MULTIPLIER: int
    fixtures_paths: Incomplete
    fixtures: dict[str | int, list[tuple[float, FixtureData]]]
    _class_manager: Incomplete
    _config_manager: Incomplete
    def __init__(self, fixtures_paths: list[Path]) -> None: ...
    def load_fixtures(self) -> None:
        """
        Loads fixture data from the specified path.

        This method reads fixture data from a JSON file located at the `fixtures_path`.
        It populates the `fixtures` dictionary with the loaded data, where each fixture
        is indexed by its external ID.

        Returns:
            None
        """
    def _load_fixtures(self, fixtures_path: Path, order_shift: int = 0) -> None: ...
    def iter_fixtures(self) -> Generator[FixtureData, None, None]: ...
    def _process_object_data(self, data: dict[str, Any], model_fields: dict[str, FieldInfo], m2m_fields: dict[str, type[Model]]) -> dict[str, Any]: ...

class FixturesManager(BaseFixturesManager):
    """
    Manager class for handling fixture data.

    This class is responsible for loading, processing, and applying fixture data
    to the database. It supports nested object construction, data processing,
    and file fixture handling.
    """
    def apply_file_fixtures(self) -> None:
        """
        Applies file fixtures from the specified directory.

        This method processes file fixtures located in the 'files' directory adjacent to the
        `fixtures_path`. It iterates through each file, reads its content, and processes it
        as a fixture. If the file fixture already exists in the database, it updates the
        existing fixture; otherwise, it creates a new one.

        Returns:
            None
        """
    def _apply_file_fixtures(self, file_dir: Path) -> None: ...
    def _apply_file_fixtures_rec(self, nested_dir: Path, base_dir: Path) -> None: ...
    def apply_fixtures(self) -> None:
        """
        Applies all loaded fixtures to the database.

        This method processes each fixture in the `fixtures` dictionary in the order
        specified by their 'order' value. It calls the `process_fixture` method for
        each fixture and then processes the data in the processing queue.

        Returns:
            None
        """
    def _process_file_fixture(self, file_path: Path, file_key: str) -> None: ...
    def _process_fixture(self, fixture: FixtureData) -> FixtureData | None:
        """
        Processes a single fixture and adds it to the processing queue.

        This method takes a fixture dictionary, checks if the fixture already exists in the database,
        and either updates the existing fixture or creates a new one. It then adds the fixture data
        to the processing queue for further processing.

        Args:
            fixture (dict[str, Any]): The fixture dictionary containing the external ID, class name,
            and data of the fixture.

        Returns:
            None
        """
    def _process_fixture_object_data(self, class_name: str, external_id: str, data: dict[str, Any]) -> None:
        """
        Processes and saves fixture object data to the database.

        This method takes the class name, external ID, and data dictionary of a fixture object,
        processes the data according to the class schema, and saves the object to the database.
        If the object already exists, it updates the existing object with the new data.

        Args:
            class_name (str): The name of the class to which the fixture object belongs.
            external_id (str): The external ID of the fixture object.
            data (dict[str, Any]): The data dictionary of the fixture object.

        Returns:
            None
        """

class AsyncFixturesManager(BaseFixturesManager):
    """
    Manager class for handling fixture data asynchronously.

    This class is responsible for loading, processing, and applying fixture data
    to the database. It supports nested object construction, data processing,
    and file fixture handling.
    """
    async def apply_file_fixtures(self) -> None:
        """
        Applies file fixtures from the specified directory.

        This method processes file fixtures located in the 'files' directory adjacent to the
        `fixtures_path`. It iterates through each file, reads its content, and processes it
        as a fixture. If the file fixture already exists in the database, it updates the
        existing fixture; otherwise, it creates a new one.

        Returns:
            None
        """
    async def _apply_file_fixtures(self, file_dir: Path) -> None: ...
    async def _apply_file_fixtures_rec(self, nested_dir: Path, base_dir: Path) -> None: ...
    async def apply_fixtures(self) -> None:
        """
        Applies all loaded fixtures to the database.

        This method processes each fixture in the `fixtures` dictionary in the order
        specified by their 'order' value. It calls the `process_fixture` method for
        each fixture and then processes the data in the processing queue.

        Returns:
            None
        """
    async def _process_file_fixture(self, file_path: Path, file_key: str) -> None: ...
    async def _process_fixture(self, fixture: FixtureData) -> FixtureData | None:
        """
        Processes a single fixture and adds it to the processing queue.

        This method takes a fixture dictionary, checks if the fixture already exists in the database,
        and either updates the existing fixture or creates a new one. It then adds the fixture data
        to the processing queue for further processing.

        Args:
            fixture (dict[str, Any]): The fixture dictionary containing the external ID, class name,
            and data of the fixture.

        Returns:
            None
        """
    async def _process_fixture_object_data(self, class_name: str, external_id: str, data: dict[str, Any]) -> None:
        """
        Processes and saves fixture object data to the database.

        This method takes the class name, external ID, and data dictionary of a fixture object,
        processes the data according to the class schema, and saves the object to the database.
        If the object already exists, it updates the existing object with the new data.

        Args:
            class_name (str): The name of the class to which the fixture object belongs.
            external_id (str): The external ID of the fixture object.
            data (dict[str, Any]): The data dictionary of the fixture object.

        Returns:
            None
        """
