import pytest
from borough_mapper import BoroughMapper, NotFoundError


def test_map_point():
    mapper = BoroughMapper()

    borough = mapper.get_borough(51.4624171, -0.1054934)
    assert borough == "Lambeth"

    with pytest.raises(NotFoundError):
        mapper.get_borough(1, 1)
