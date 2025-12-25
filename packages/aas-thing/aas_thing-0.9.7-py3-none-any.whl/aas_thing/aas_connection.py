from typing import Any, Dict, Iterable, Optional
from logging import Logger
import jsonschema

from basyx.aas.adapter.json import read_aas_json_file_into, write_aas_json_file
from basyx.aas.adapter.xml import read_aas_xml_file_into
from basyx.aas.adapter import aasx
from basyx.aas.model import DictObjectStore
from basyx.aas import model
from pathlib import Path
from aas_thing.util.open_config_yaml import get_abs_path


def _validate_config(obj: Any, schema: Dict[str, Any], name: str) -> None:
    """
    Validates the given configuration object against a JSON schema.

    :param obj: The configuration object to validate
    :param schema: The JSON schema to validate against
    :param name: The name of the configuration object (for error messages)
    :raises ConfigError: If the configuration is invalid
    """
    try:
        jsonschema.validate(instance=obj, schema=schema)
    except jsonschema.ValidationError as e:
        raise ConfigError(f"Invalid {name} configuration: {e.message}")


class ConfigError(Exception):
    """Configuration validation or initialization error."""
    pass


class AASAPI:
    """
    API exposing Type 2 operations for the Asset Administration Shell.
    """
    def __init__(self, shell: model.AssetAdministrationShell) -> None:
        """
        Initializes the AAS API with the given Asset Administration Shell.

        :param shell: The AAS shell instance to expose through this API
        :raises ConfigError: If the given shell instance is None
        """
        if shell is None:
            raise ConfigError("AAS shell instance cannot be None")
        self._shell = shell

    def get_aas(self) -> model.AssetAdministrationShell:
        """
        Returns the Asset Administration Shell instance.

        :return: The AAS instance
        """
        return self._shell

    def get_all_submodel_references(self) -> Iterable[model.ModelReference]:
        """
        Returns all submodel references of the Asset Administration Shell.

        :return: A list of ModelReference objects
        """
        return list(self._shell.submodel)

    def add_submodel_reference(self, ref: model.ModelReference) -> None:
        """
        Adds a submodel reference to the Asset Administration Shell.

        :param ref: The ModelReference to add to the shell's submodel list
        """

        self._shell.submodel.add(ref)

    def remove_submodel_reference(self, ref_id: str) -> None:
        """
        Removes a submodel reference from the Asset Administration Shell based on the given identifier.

        :param ref_id: The identifier of the submodel reference to remove
        :raises ConfigError: If the submodel reference with the given identifier is not found
        """

        refs = {r.get_identifier(): r for r in self._shell.submodel}
        target = refs.get(ref_id)
        if not target:
            raise ConfigError(f"Submodel reference '{ref_id}' not found")
        self._shell.submodel.remove(target)


class SubmodelAPI:
    """
    API exposing Type 2 operations for Submodels.
    """
    def __init__(self, submodel: model.Submodel) -> None:
        """
        Initialize the Submodel API with the given Submodel.

        :param submodel: The Submodel instance to be managed by this API.
        :raises ConfigError: If the given Submodel instance is None.
        """

        if submodel is None:
            raise ConfigError("Submodel instance cannot be None")
        self._submodel = submodel

    def get_submodel(self) -> model.Submodel:
        """
        Returns the Submodel instance associated with this API.

        :return: The Submodel instance
        """
        return self._submodel

    def update_submodel(self, new: model.Submodel) -> None:
        """
        Updates the Submodel instance associated with this API with the given new Submodel instance.

        :param new: The new Submodel instance to update from
        """
        self._submodel.update_from(new)

    def list_elements(self) -> Iterable[model.SubmodelElement]:
        """
        Returns an iterable of SubmodelElements in the Submodel.

        :return: An iterable of SubmodelElements
        """
        return list(self._submodel.submodel_element)

    def get_submodel_element_by_path(self, path: str) -> Optional[model.SubmodelElement]:
        """
        Retrieve the SubmodelElement identified by the specified path.

        The path is a dotted string, where each part is either a name of a
        referable or a referable with an index, e.g., "mySubmodelElement[0]".

        :param path: The path to the SubmodelElement to retrieve.
        :return: The SubmodelElement at the given path or None if not found.
        """
        # Split the path into individual parts
        parts = path.split('.')
        current: Any = self._submodel

        # Traverse the path to locate the desired SubmodelElement
        for part in parts:
            if '[' in part and part.endswith(']'):
                # Handle indexed elements, e.g., "element[0]"
                name, idx = part[:-1].split('[')
                if name:
                    current = current.get_referable(name)
                # Convert index to integer and retrieve the element
                current = list(current.submodel_element)[int(idx)]
            else:
                # Retrieve the referable element by name
                current = current.get_referable(part)
        
        # Return the located SubmodelElement or None if not found
        return current

    def set_element_value(self, path: str, value: Any) -> None:
        """
        Sets the value of the SubmodelElement at the given path to the given value.

        The path is a dotted string, where each part is either a name of a
        referable or a referable with an index, e.g. "mySubmodelElement[0]".

        :param path: The path to the SubmodelElement to set
        :param value: The value to set
        :raises ConfigError: If the path is not found
        """
        elem = self.get_submodel_element_by_path(path)
        if elem is None:
            raise ConfigError(f"Path '{path}' not found")
        setattr(elem, 'value', value)

    def delete_element_by_path(self, path: str) -> None:
        """
        Deletes the SubmodelElement at the given path.

        The path is a dotted string, where each part is either a name of a
        referable or a referable with an index, e.g. "mySubmodelElement[0]".

        :param path: The path to the SubmodelElement to delete
        :raises ConfigError: If the path is not found or if the parent at the path
            is not a container that can remove referables
        """
        parts = path.split('.')
        parent = self.get_submodel_element_by_path('.'.join(parts[:-1])) if len(parts) > 1 else self._submodel
        name = parts[-1]
        if hasattr(parent, 'remove_referable'):
            parent.remove_referable(name)
        else:
            raise ConfigError(f"Cannot remove element at '{path}'")

    def add_element(self, elem: model.SubmodelElement) -> None:
        """
        Adds the given SubmodelElement to the top-level of the Submodel.

        :param elem: The SubmodelElement to add
        :raises ConfigError: If the SubmodelElement already exists in the Submodel
        """
        self._submodel.submodel_element.add(elem)

    def add_element_to(self, path: str, elem: model.SubmodelElement) -> None:
        """
        Adds the given SubmodelElement to the SubmodelElement at the given path.

        The path is a dotted string, where each part is either a name of a
        referable or a referable with an index, e.g. "mySubmodelElement[0]". The
        target at the path must be a collection.

        :param path: The path to the target SubmodelElement
        :param elem: The SubmodelElement to add
        :raises ConfigError: If the target at the path is not a collection
        """

        container = self.get_element_by_path(path)
        if hasattr(container, 'value') and isinstance(container.value, (list, set)):
            container.value.add(elem)  # type: ignore
        else:
            raise ConfigError(f"Target '{path}' is not a collection")


class AASConnector:
    """
    Loads and saves AAS and Submodels from/to files based on configuration.
    """
    FILE_SCHEMA = {
        "type": "object",
        "properties": {
            "import_file_path": {"type": "string"},
            "export_file_path": {"type": "string"},
        },
        "required": ["import_file_path", "export_file_path"],
    }
    EXTENSIONS = {'.json', '.xml', '.aasx'}

    def __init__(
        self,
        config: Dict[str, Any],
        logger: Logger,
        object_store: Optional[DictObjectStore] = None,
    ) -> None:
        """
        Initializes the AASConnector instance.

        :param config: The configuration dictionary, containing an "aas_connector" entry
            with "import_file_path" and "export_file_path" properties
        :param logger: The logger instance
        :param object_store: Optional object store to use for the SubmodelElement's
            values, defaults to a new DictObjectStore
        """
        self._logger = logger
        self._config = config
        self._store = object_store or DictObjectStore()
        self._aas: Optional[model.AssetAdministrationShell] = None
        self._submodels: Dict[str, model.Submodel] = {}
        self._load()

    def _load(self) -> None:
        """
        Loads the Asset Administration Shell (AAS) and Submodels from a configured file.

        This method retrieves the file path from the configuration, validates the
        file format, and reads the content into the object store. Supported file
        formats include JSON, XML, and AASX. It identifies and stores the AAS and
        Submodels found in the file.

        :raises ConfigError: If the file does not exist, has an unsupported extension,
                            or if no AAS shell is found in the import file.
        """

        # Get the file path from the configuration
        cfg = self._config.get('file_storage')
        _validate_config(cfg, self.FILE_SCHEMA, 'AAS file storage')
        imp = Path(get_abs_path(cfg['import_file_path']))

        # Check if the file exists
        if not imp.exists():
            raise ConfigError(f"File not found: {imp}")

        # Validate the file extension
        ext = imp.suffix.lower()
        if ext not in self.EXTENSIONS:
            raise ConfigError(f"Unsupported extension: {ext}")

        # Log and read the file
        self._logger.info(f"Loading AAS from {imp}")
        if ext == '.json':
            with imp.open('r', encoding='utf-8-sig') as f:
                read_aas_json_file_into(self._store, f)
        elif ext == '.xml':
            with imp.open('r', encoding='utf-8-sig') as f:
                read_aas_xml_file_into(self._store, f)
        else:
            with aasx.AASXReader(str(imp)) as r:
                r.read_into(self._store, aasx.DictSupplementaryFileContainer())

        # Identify and store the AAS and Submodels
        for obj in self._store:
            if isinstance(obj, model.AssetAdministrationShell):
                self._aas = obj
                self._logger.info(f"Parsed AAS id={obj.id}")
            elif isinstance(obj, model.Submodel):
                self._submodels[obj.id] = obj
                self._logger.info(f"Parsed Submodel id={obj.id}")

        # Check if an AAS shell was found
        if not self._aas:
            raise ConfigError("No AAS shell found in import file")

    @property
    def aas(self) -> model.AssetAdministrationShell:
        """
        Returns the Asset Administration Shell (AAS) instance.

        :return: The AAS instance
        :raises ConfigError: If the AAS has not been initialized
        """
        if not self._aas:
            raise ConfigError("AAS not initialized")
        return self._aas

    @property
    def submodels(self) -> Iterable[model.Submodel]:
        """
        Returns an iterable of all the Submodels stored in the connector.

        :return: An iterable containing all the Submodel instances.
        """

        return list(self._submodels.values())

    def write_to_file(self) -> None:
        """
        Writes the AAS and Submodels to the configured output file.

        :raises ConfigError: If the file extension is not supported
        """
        cfg = self._config.get('file_storage')
        _validate_config(cfg, self.FILE_SCHEMA, 'AAS file storage')
        out = Path(get_abs_path(cfg['export_file_path']))
        out.parent.mkdir(parents=True, exist_ok=True)
        ext = out.suffix.lower()

        # Determine the writer based on the file extension
        if ext == '.json':
            with out.open('w', encoding='utf-8') as f:
                # Write the AAS and Submodels as a JSON file
                write_aas_json_file(f, self._store)
        elif ext == '.xml':
            with out.open('w', encoding='utf-8') as f:
                # Write the AAS and Submodels as an XML file
                read_aas_xml_file_into(self._store, f, replace_existing=True)
        elif ext == '.aasx':
            with aasx.AASXWriter(str(out)) as w:
                # Write the AAS and Submodels as an AASX package
                w.write_aas(
                    aas_ids=[self._aas.id],
                    object_store=self._store,
                    file_store=aasx.DictSupplementaryFileContainer(),
                )
        else:
            raise ConfigError(f"Unsupported extension: {ext}")
