from importlib.metadata import version


def get_version_helper(module:str) -> str:
    """
    Get the version of the specified module.
    
    Args:
        module (str): The name of the module to query.
    
    Returns:
        str: The version of the module, or an empty string if not found.
    """
    try:
        return version(module)
    except Exception:
        try:
            imported_module = __import__(module)
            return getattr(imported_module, "__version__", "")
        except Exception:
            return ""