from random import choices
from typing import Callable, Optional
from string import digits, ascii_uppercase

class IDGenerator:
    _characters: str = ascii_uppercase + digits
    _unavailable: list[str] = []

    @staticmethod
    def generate(length: int, *, prefix: Optional[str] = None) -> str:
        """
        Returns a random ID of a length.
        :param length: The length of the generated ID
        :param prefix: Optional prefix to prepend to generated IDs
        :return: The generated ID
        """
        if prefix is not None:
            prefix_upper = prefix.upper()
            prefix_and_separator_length = len(prefix_upper) + 1

            if prefix_and_separator_length >= length:
                random_part_length = 1
            else:
                random_part_length = length - prefix_and_separator_length

            id_ = ''.join(choices(IDGenerator._characters, k=random_part_length))
            id_ = f'{prefix_upper}-{id_}'
        else:
            id_ = ''.join(choices(IDGenerator._characters, k=length))

        return id_

    @staticmethod
    def generate_available(length: int, check_func: Callable[[str], bool], *, increment_on_unavailable=False, prefix: Optional[str] = None) -> str:
        """
        Generates random IDs until one is available based on the given check function.
        :param length: The length of the generated ID
        :param check_func: The function that is called that determines if the current generated ID is available
        :param increment_on_unavailable: Whether to increment the length by 1 whenever a generated ID is unavailable
        :param prefix: Optional prefix to prepend to generated IDs
        :return: The generated ID
        """
        id_ = IDGenerator.generate(length, prefix=prefix)
        while not check_func(id_) or not IDGenerator.is_id_available(id_):
            if increment_on_unavailable:
                length += 1

            id_ = IDGenerator.generate(length, prefix=prefix)

        IDGenerator._unavailable.append(id_)
        return id_

    @staticmethod
    def is_id_available(id_: str) -> bool:
        """
        Whether an ID is available.

        Note that unavailable IDs are only stored for the lifetime of the application and the cache is only populated
        when generating IDs via :meth:`IDGenerator.generate_available`.
        :param id_: The ID to check
        :return: `True` if the ID is available, `False` otherwise
        """
        return id_ not in IDGenerator._unavailable

    @staticmethod
    def clear_unavailable() -> None:
        IDGenerator._unavailable.clear()
