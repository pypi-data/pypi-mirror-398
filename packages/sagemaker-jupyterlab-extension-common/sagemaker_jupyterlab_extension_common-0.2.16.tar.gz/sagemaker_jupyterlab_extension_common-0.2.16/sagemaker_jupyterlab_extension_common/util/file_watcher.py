import copy
import json
import logging
import os


class WatchedFile:
    """This class tracks a file and updates the in-memory contents when the file is modified."""

    def __init__(self, file_path, log):
        self._cached_content = None
        self._last_mtime_ns = None
        self.file_path = file_path
        self._log = log

    def read(self):
        if self.requires_read():
            self._read_modified()
        else:
            self._log.info(
                f"Returning content of [{self.file_path}] updated at time {self._last_mtime_ns}"
            )

        # the file_content should have been read by this point
        assert self._cached_content is not None
        return copy.copy(self._cached_content)

    def _update_cache(self, updated_content):
        self._cached_content = updated_content
        self._last_mtime_ns = os.stat(self.file_path).st_mtime_ns
        self._log.info(f"Read [{self.file_path}] from disk at {self._last_mtime_ns}")

    def _read_modified(self):
        with open(self.file_path, "r") as f:
            self._update_cache(f.read())

    def requires_read(self):
        try:
            return (
                self._cached_content is None
                # this part is in the second branch of the `or` so that if
                # the file does not exist yet, there is still time to create it
                or (os.stat(self.file_path).st_mtime_ns != self._last_mtime_ns)
            )
        except:
            return False


class WatchedJsonFile(WatchedFile):
    def _read_modified(self):
        try:
            with open(self.file_path, "r") as f:
                self._update_cache(json.load(f))
        except:
            logging.error(f"Unable to read modified file. Returning empty value...")
            self._update_cache({})

    def get_key(self, key, default_value=None):
        """
        Tries to read and parse the json file and get the key from root.

        Provided default_value is used if key found is not found.
        """

        try:
            value = self.read().get(key, default_value)
            return value
        except FileNotFoundError as error:
            logging.error(
                f"The watched file({self.file_path}) does not exist to get key: {key}"
            )
            return default_value
