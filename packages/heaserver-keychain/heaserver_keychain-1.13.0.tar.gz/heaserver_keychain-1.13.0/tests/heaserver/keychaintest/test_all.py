from .testcase import CredentialsTestCase, AWSCredentialsTestCase
from heaserver.service.testcase.mixin import GetOneMixin, GetAllMixin, PostMixin, PutMixin, DeleteMixin


class TestGet(CredentialsTestCase, GetOneMixin):
    pass


class TestGetAll(CredentialsTestCase, GetAllMixin):
    pass


class TestPost(CredentialsTestCase, PostMixin):
    pass


class TestPut(CredentialsTestCase, PutMixin):
    pass


class TestDelete(CredentialsTestCase, DeleteMixin):
    pass


class AWSTestGet(AWSCredentialsTestCase, GetOneMixin):
    pass


class AWSTestGetAll(AWSCredentialsTestCase, GetAllMixin):
    pass


class AWSTestPost(AWSCredentialsTestCase, PostMixin):
    pass


class AWSTestPut(AWSCredentialsTestCase, PutMixin):
    pass


class AWSTestDelete(AWSCredentialsTestCase, DeleteMixin):
    pass
