from abc import ABC, abstractmethod
from typing import Optional

from pydantic import Field
from sqids import Sqids

from apppy.env import Env, EnvSettings
from apppy.fastql.annotation.interface import fastql_type_interface
from apppy.fastql.errors import TypedIdInvalidPrefixError


class TypedIdEncoderSettings(EnvSettings):
    # TYPED_ID_ENCODER_ALPHABET
    alphabet: str = Field(exclude=True)
    # TYPED_ID_ENCODER_MIN_LENGTH
    min_length: int = Field(default=10)

    def __init__(self, env: Env) -> None:
        super().__init__(env=env, domain_prefix="TYPED_ID_ENCODER")


class TypedIdEncoder:
    """
    Service to encode ids into strings based on a static
    alphabet. This allows the system to ofuscate the integer
    values to outside parties (e.g. database primary keys)
    """

    # NOTE: We use a global instance (i.e. static singleton) for
    # TypedIdEncoder because we would like it to be used by all TypedId
    # instances which will not be instantiated via the app container. So
    # instead we'll have this static reference that they are able to use.
    _global_instance: Optional["TypedIdEncoder"] = None

    def __init__(self, settings: TypedIdEncoderSettings) -> None:
        self._settings = settings
        self._encoder = Sqids(alphabet=settings.alphabet, min_length=settings.min_length)

    ##### ##### ##### Integers ##### ##### #####
    # Used to encode and decode integers. Which is
    # useful for items like database primary keys

    def encode_int(self, value: int) -> str:
        return self._encoder.encode([value])

    def decode_int(self, value: str) -> int:
        return self._encoder.decode(value)[0]

    @classmethod
    def get_global(cls) -> "TypedIdEncoder":
        if cls._global_instance is None:
            raise RuntimeError("TypedIdEncoder has not been initialized.")
        return cls._global_instance

    @classmethod
    def set_global(cls, instance: "TypedIdEncoder") -> None:
        if cls._global_instance is None:
            cls._global_instance = instance


@fastql_type_interface
class TypedId(ABC):
    """
    Base class for all typed ids. A typed id has a prefix
    which signals it's type and an encoded value which
    can be shared externally (i.e. without security concerns).
    """

    def __init__(self, encoded_int: str) -> None:
        super().__init__()
        self._encoded_int = encoded_int

    @property
    @abstractmethod
    def prefix(self) -> str:
        pass

    @property
    def number(self) -> int:
        return TypedIdEncoder.get_global().decode_int(self._encoded_int)

    def __str__(self) -> str:
        return f"{self.prefix}_{self._encoded_int}"

    @classmethod
    def from_number(cls, id: int):
        return cls(TypedIdEncoder.get_global().encode_int(id))

    @classmethod
    def from_str(cls, id: str):
        prefix = cls._get_prefix()
        if not id.startswith(f"{prefix}_"):
            raise TypedIdInvalidPrefixError(id=id, id_type=cls.__name__)

        encoded_int = id[len(f"{prefix}_") :]
        return cls(encoded_int)

    @classmethod
    def is_valid(cls, id: str):
        prefix = cls._get_prefix()
        return id.startswith(f"{prefix}_")

    @classmethod
    def _get_prefix(cls):
        instance = cls.__new__(cls)
        return instance.prefix
