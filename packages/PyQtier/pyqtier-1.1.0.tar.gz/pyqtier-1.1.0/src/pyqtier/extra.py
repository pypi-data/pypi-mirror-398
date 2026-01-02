from typing import Optional


class Singleton:
    _instance: Optional['Singleton'] = None

    def __new__(cls) -> 'Singleton':
        """
        Create new object If it does not exist.
        :return: Singleton object
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'Singleton':
        """
        Getting existing object or create new one.
        :return: Singleton object
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
