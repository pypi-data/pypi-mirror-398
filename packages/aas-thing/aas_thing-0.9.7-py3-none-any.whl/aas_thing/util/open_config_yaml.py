import os 
import yaml 
import inspect 

def get_abs_path(config_file_path: str):
    """
    Takes a config file path as an argument and returns an absolute path to this file.

    If the config_file_path is an absolute path, it is returned directly.

    If the config_file_path is a relative path, it is resolved relative to the caller of this function.

    Raises a ValueError if the path is not a file or if the file does not exist.

    Args:
        config_file_path (str): Path to the config file (either absolute or relative)
    Returns: 
        str:The absolute path to the config file
    Raises:
        ValueError: If `config_file_path` is `None` or not a valid YAML file.
    """
    # Check if the config_file_path is None
    if config_file_path is None:
        raise ValueError("config_file_path cannot be null")

    # If the config_file_path is an absolute path, use it directly
    if os.path.isabs(config_file_path):
        return config_file_path
    else:
        # Get the file location who calls the function
        for i in range(len(inspect.stack())):
            caller_file = inspect.stack()[i].filename
            caller_dir = os.path.dirname(os.path.abspath(caller_file))
            # If the config_file_path is a relative path, convert it to an absolute path
            config_file_path_abs = os.path.abspath(os.path.join(caller_dir, config_file_path))
            if os.path.exists(config_file_path_abs) and os.path.isfile(config_file_path_abs):
                return config_file_path_abs 

        # Check if the file exists
        if not os.path.exists(config_file_path_abs):
            raise FileNotFoundError(f"config_file_path '{config_file_path_abs}' does not exist")
        # Check if the file is a file
        if not os.path.isfile(config_file_path_abs):
            raise ValueError(f"config_file_path '{config_file_path_abs}' is not a file")

    
def load_config_yaml_to_json(config_file_path: str):
    """
    Load a configuration YAML file and convert it to JSON in read-only mode. 

    Args:
        config_file_path (str): Path to the YAML configuration file.

    Returns:
        dict: The configuration file as JSON.

    Raises:
        ValueError: If `config_file_path` is `None` or not a valid YAML file.
        FileNotFoundError: If the configuration file does not exist.
    """
    config_file_path = get_abs_path(config_file_path)

    try:
        with open(config_file_path, "r") as yaml_config_file:
            # Load the YAML configuration file
            _config_json = yaml.safe_load(yaml_config_file)
    except yaml.YAMLError as e:
        # If the configuration file is not a valid YAML file, raise an exception
        raise ValueError(f"config_file_path {config_file_path} is not a valid yaml file: {e}")
    return _config_json
