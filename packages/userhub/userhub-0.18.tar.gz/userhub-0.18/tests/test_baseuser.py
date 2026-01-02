from userhub.model import BaseUser


def test_baseuser_sets_id_before_login():
    user = BaseUser(token="token", login="id123", id=123)
    assert user.id == 123
    assert user.login == "id123"


def test_baseuser_skips_validation_for_api_payloads():
    user = BaseUser(token="token", login="a", id=1)
    assert user.login == "a"
