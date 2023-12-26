import pytest

from borough_mapper import BoroughMapper, NotFoundError


def test_map_point_ok():
    mapper = BoroughMapper()

    borough = mapper.get_borough(51.4624171, -0.1054934)
    assert borough == "Lambeth"


def test_map_point_raise():
    mapper = BoroughMapper(True)

    with pytest.raises(NotFoundError):
        mapper.get_borough(1, 1)


def test_map_point_no_raise():
    mapper = BoroughMapper(False)

    borough = mapper.get_borough(1, 1)
    assert borough == "Outside London"
