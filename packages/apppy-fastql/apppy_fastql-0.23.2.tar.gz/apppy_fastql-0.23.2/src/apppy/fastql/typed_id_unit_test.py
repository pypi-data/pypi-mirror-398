import pytest

from apppy.env import DictEnv, Env
from apppy.fastql.errors import TypedIdInvalidPrefixError
from apppy.fastql.typed_id import TypedId, TypedIdEncoder, TypedIdEncoderSettings

_typed_id_encoder_env_test: Env = DictEnv(
    prefix="APP",
    name="int_encoder_test",
    d={
        "APP_TYPED_ID_ENCODER_ALPHABET": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"  # noqa: E501
    },
)
_typed_id_encoder_settings_test: TypedIdEncoderSettings = TypedIdEncoderSettings(  # type: ignore[misc]
    _typed_id_encoder_env_test  # type: ignore[arg-type]
)
_typed_id_encoder_test: TypedIdEncoder = TypedIdEncoder(_typed_id_encoder_settings_test)
TypedIdEncoder.set_global(_typed_id_encoder_test)


def test_int_encoder():
    encoded_int = _typed_id_encoder_test.encode_int(5)
    assert encoded_int == "tGj3JHachG"

    decoded_int = _typed_id_encoder_test.decode_int("tGj3JHachG")
    assert decoded_int == 5

    encoded_int = _typed_id_encoder_test.encode_int(9_999_999_999)
    assert encoded_int == "Tnega83VLI"

    decoded_int = _typed_id_encoder_test.decode_int("Tnega83VLI")
    assert decoded_int == 9_999_999_999


class TypedTestId(TypedId):
    @property
    def prefix(self) -> str:
        return "test"


def test_id_from_number():
    id1 = TypedTestId.from_number(1)
    assert str(id1) == "test_FrwMELkAmX"
    assert id1.number == 1

    id2 = TypedTestId.from_number(2)
    assert str(id2) == "test_nLKnICbr1y"
    assert id2.number == 2


def test_id_from_str():
    id1 = TypedTestId.from_str("test_FrwMELkAmX")
    assert str(id1) == "test_FrwMELkAmX"
    assert id1.number == 1

    id2 = TypedTestId.from_str("test_nLKnICbr1y")
    assert str(id2) == "test_nLKnICbr1y"
    assert id2.number == 2


def test_id_is_valid():
    valid = TypedTestId.is_valid("test_FrwMELkAmX")
    assert valid is True

    invalid = TypedTestId.is_valid("invalid_FrwMELkAmX")
    assert invalid is False


def test_id_invalid_prefix():
    with pytest.raises(TypedIdInvalidPrefixError):
        TypedTestId.from_str("invalid_FrwMELkAmX")
