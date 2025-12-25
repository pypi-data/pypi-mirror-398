import os
import yaml

class PathLoader(yaml.SafeLoader):
    """
    Custom YAML loader that resolves file paths relative to the configuration file location.

    This loader enables the use of the ``!path`` tag in YAML files. When this tag is encountered,
    the loader automatically resolves the specified path relative to the directory containing
    the YAML file, rather than the current working directory of the Python script.

    Parameters
    ----------
    stream : file object
        The file stream to load. It must have a ``name`` attribute containing
        the file path (e.g., a file object created via ``open()``).

    """

    def __init__(self, stream):
        # Determine the folder of the file being loaded
        self._root = os.path.split(stream.name)[0]
        super().__init__(stream)

    def construct_path(self, node):
        """
        Construct a path by joining the file root directory with the node value.

        Parameters
        ----------
        node : yaml.nodes.ScalarNode
            The YAML node containing the relative path string.

        Returns
        -------
        str
            The absolute or relative path resolved against the configuration file directory.
        """
        # This function runs whenever the loader sees '!path'
        value = self.construct_scalar(node)
        return os.path.normpath(os.path.join(self._root, value))

# Register the constructor
PathLoader.add_constructor('!path', PathLoader.construct_path)