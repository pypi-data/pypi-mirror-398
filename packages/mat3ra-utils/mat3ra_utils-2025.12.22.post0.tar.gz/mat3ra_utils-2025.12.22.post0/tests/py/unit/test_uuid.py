import re
import pytest
from mat3ra.utils.uuid import get_uuid, get_uuid_from_namespace

UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
TEST_SEED_1 = "test_seed_1"
TEST_SEED_2 = "test_seed_2"
TEST_NAMESPACE = "00000000-0000-4000-8000-000000000000"
EXPECTED_UUID_FROM_SEED_1 = "2b0e8b5e-6b4a-5d5e-b5e5-5e5e5e5e5e5e"


def test_get_uuid():
    uuid_1 = get_uuid()
    uuid_2 = get_uuid()
    assert UUID_PATTERN.match(uuid_1)
    assert UUID_PATTERN.match(uuid_2)
    assert uuid_1 != uuid_2


@pytest.mark.parametrize(
    "seed,namespace,expected_same",
    [
        (TEST_SEED_1, TEST_NAMESPACE, TEST_SEED_1),
        (TEST_SEED_2, TEST_NAMESPACE, TEST_SEED_2),
        ("", TEST_NAMESPACE, ""),
    ],
)
def test_get_uuid_from_namespace_deterministic(seed, namespace, expected_same):
    uuid_1 = get_uuid_from_namespace(seed, namespace)
    uuid_2 = get_uuid_from_namespace(expected_same, namespace)
    assert UUID_PATTERN.match(uuid_1)
    assert UUID_PATTERN.match(uuid_2)
    assert uuid_1 == uuid_2


@pytest.mark.parametrize(
    "seed_a,seed_b,namespace",
    [
        (TEST_SEED_1, TEST_SEED_2, TEST_NAMESPACE),
        ("seed_a", "seed_b", TEST_NAMESPACE),
        (TEST_SEED_1, "", TEST_NAMESPACE),
    ],
)
def test_get_uuid_from_namespace_different_seeds(seed_a, seed_b, namespace):
    uuid_a = get_uuid_from_namespace(seed_a, namespace)
    uuid_b = get_uuid_from_namespace(seed_b, namespace)
    assert UUID_PATTERN.match(uuid_a)
    assert UUID_PATTERN.match(uuid_b)
    assert uuid_a != uuid_b


def test_get_uuid_from_namespace_default_params():
    uuid_with_defaults = get_uuid_from_namespace()
    assert UUID_PATTERN.match(uuid_with_defaults)
