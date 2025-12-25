from .testcase import TestCase
from heaserver.service.testcase.mixin import GetOneMixin, GetAllMixin, PostMixin, PutMixin, DeleteMixin
from heaserver.service.representor import cj
from aiohttp import hdrs


class TestGet(TestCase, GetOneMixin):
    async def test_get_status_opener_choices(self) -> None:
        """Checks if a GET request for the opener for a bucket succeeds with status 300."""
        obj = await self.client.request('GET',
                                        (self._href / self._id() / 'opener').path,
                                        headers=self._headers)
        self.assertEqual(300, obj.status)

    async def test_get_status_opener_hea_default_exists(self) -> None:
        """
        Checks if a GET request for the opener for a bucket succeeds and returns JSON that contains a
        Collection+JSON object with a rel property in its links that contains 'hea-default'.
        """
        obj = await self.client.request('GET',
                                        (self._href / self._id() / 'opener').path,
                                        headers={**self._headers, hdrs.ACCEPT: cj.MIME_TYPE})
        if not obj.ok:
            self.fail(f'GET request failed: {await obj.text()}')
        received_json = await obj.json()
        rel = received_json[0]['collection']['links'][0]['rel']
        self.assertIn('hea-default', rel)


class TestGetAll(TestCase, GetAllMixin):
    pass


class TestPost(TestCase, PostMixin):
    pass


class TestPut(TestCase, PutMixin):
    pass


class TestDelete(TestCase, DeleteMixin):
    pass
