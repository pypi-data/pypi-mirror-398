def _version(package_name):
    try:  # assume python>=3.9
        from importlib.metadata import version

        return version(package_name)
    except ImportError:  # older python
        from pkg_resources import get_distribution

        return get_distribution(package_name).version


__version__ = _version("eyes-images")
