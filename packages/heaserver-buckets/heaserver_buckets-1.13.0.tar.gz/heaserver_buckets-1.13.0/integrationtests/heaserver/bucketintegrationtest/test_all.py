from .testcase import TestCase
from heaserver.service.testcase.mixin import GetOneMixin, GetAllMixin, PostMixin, PutMixin, DeleteMixin
from aiohttp import hdrs


class TestGet(TestCase, GetOneMixin):
    async def test_options_status_bucket(self):
        """Checks if an OPTIONS request for a single bucket succeeds with status 200."""
        obj = await self.client.request('OPTIONS',
                                        (self._href / self._id()).path,
                                        headers=self._headers)
        self.assertEqual(200, obj.status)

    async def test_options_bucket(self):
        """
        Checks if the "Allow" header in a response to an OPTIONS request for a single bucket contains GET, POST, HEAD,
        and OPTIONS and contains neither PUT nor DELETE.
        """
        obj = await self.client.request('OPTIONS',
                                        (self._href / self._id()).path,
                                        headers=self._headers)
        if not obj.ok:
            self.fail(f'OPTIONS request failed: {await obj.text()}')
        allow = {method.strip() for method in obj.headers.get(hdrs.ALLOW).split(',')}
        self.assertEqual({'GET', 'DELETE', 'HEAD', 'OPTIONS', 'PUT'}, allow)

    async def test_methods_not_allowed(self) -> None:
        """
        Checks if all the methods not in the "Allow" header in a response to an OPTIONS request for a single bucket
        fail with status 405.
        """
        obj = await self.client.request('OPTIONS',
                                        (self._href / self._id()).path,
                                        headers=self._headers)
        if not obj.ok:
            self.fail(f'OPTIONS request failed: {await obj.text()}')
        allowed_methods = {method.strip() for method in obj.headers.get(hdrs.ALLOW).split(',')}
        all_methods = {'HEAD', 'OPTIONS', 'PUT', 'GET', 'DELETE'}
        prohibited_methods = all_methods - allowed_methods
        resps = {}
        for prohibited in prohibited_methods:
            obj = await self.client.request(prohibited,
                                            (self._href / self._id()).path,
                                            headers=self._headers)
            resps |= {prohibited: obj.status}
        self.assertEqual(dict(zip(prohibited_methods, [405] * len(prohibited_methods))), resps)


class TestGetAll(TestCase, GetAllMixin):
    async def test_options_status_buckets(self):
        """Checks if an OPTIONS request for all the buckets succeeds with status 200."""
        obj = await self.client.request('OPTIONS',
                                        (self._href / '').path,
                                        headers=self._headers)
        self.assertEqual(200, obj.status)

    async def test_options_buckets(self):
        """
        Checks if the "Allow" header in a response to an OPTIONS request for all the buckets contains GET, HEAD,
        and OPTIONS and contains neither POST, PUT nor DELETE.
        """
        obj = await self.client.request('OPTIONS',
                                        (self._href / '').path,
                                        headers=self._headers)
        if not obj.ok:
            self.fail(f'OPTIONS request failed: {await obj.text()}')
        allow = {method.strip() for method in obj.headers.get(hdrs.ALLOW).split(',')}
        self.assertEqual({'GET', 'HEAD', 'POST', 'OPTIONS'}, allow)

    async def test_methods_not_allowed(self) -> None:
        """
        Checks if all the methods (except POST) not in the "Allow" header in a response to an OPTIONS request for all
        the buckets fail with status 405.
        """
        obj = await self.client.request('OPTIONS',
                                        (self._href / '').path,
                                        headers=self._headers)
        if not obj.ok:
            self.fail(f'OPTIONS request failed: {await obj.text()}')
        allowed_methods = {method.strip() for method in obj.headers[hdrs.ALLOW].split(',')}
        all_methods = {'HEAD', 'OPTIONS', 'PUT', 'GET', 'DELETE'}
        prohibited_methods = all_methods - allowed_methods
        resps = {}
        for prohibited in prohibited_methods:
            obj = await self.client.request(prohibited,
                                            (self._href / '').path,
                                            headers=self._headers)
            resps |= {prohibited: obj.status}
        self.assertEqual(dict(zip(prohibited_methods, [405] * len(prohibited_methods))), resps)
