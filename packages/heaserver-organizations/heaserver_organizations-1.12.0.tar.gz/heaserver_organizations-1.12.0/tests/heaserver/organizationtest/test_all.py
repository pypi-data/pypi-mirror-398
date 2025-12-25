from heaserver.service import heaobjectsupport
from typing import Union, Type, Optional
from collections.abc import Mapping, Sequence
from heaobject.root import DesktopObject
from heaobject.person import Person
from aiohttp import web
async def _mock_type_to_resource_url(request: web.Request, type_or_type_name: Union[str, Type[DesktopObject]],
                                     parameters: Optional[Mapping[str, Union[Sequence[Union[int, float, complex, str]], Mapping[str, Union[int, float, complex, str]], tuple[str, Union[int, float, complex, str]], int, float, complex, str]]] = None,
                                     **kwargs: Union[Sequence[Union[int, float, complex, str]], Mapping[str, Union[int, float, complex, str]], tuple[str, Union[int, float, complex, str]], int, float, complex, str]) -> str:
    if type_or_type_name in (Person, Person.get_type_name()):
        return 'http://localhost:8080/people'
    else:
        raise ValueError(f'Unexpected type {type_or_type_name}')
heaobjectsupport.type_to_resource_url = _mock_type_to_resource_url
from heaserver.service import client
from heaobject.person import Group
async def _mock_get_all(app, url, type_or_type_name, headers=None):
    yield []
client.get_all = _mock_get_all
from .testcase import TestCase
from heaserver.service.testcase.mixin import GetOneMixin, GetAllMixin, PostMixin, PutMixin, DeleteMixin
from aiohttp import hdrs
from heaserver.service.representor import cj
from unittest.mock import patch

class TestGet(TestCase, GetOneMixin):
    """Test case for GET requests specific to organizations."""
    async def test_get_status_opener_choices(self) -> None:
        """Checks if a GET request for the opener for an organization succeeds with status 300."""
        obj = await self.client.request('GET',
                                        (self._href / self._id() / 'opener').path,
                                        headers=self._headers)
        self.assertEqual(300, obj.status)

    async def test_get_status_opener_hea_default_exists(self) -> None:
        """
        Checks if a GET request for the opener for an organization succeeds and returns JSON that contains a
        Collection+JSON object with a rel property in its links that contains 'hea-default'.
        """
        obj = await self.client.request('GET',
                                        (self._href / self._id() / 'opener').path,
                                        headers={**self._headers, hdrs.ACCEPT: cj.MIME_TYPE})
        if not obj.ok:
            self.fail(f'GET request failed: {await obj.text()}')
        received_json = await obj.json()
        rel = received_json[0]['collection']['items'][0]['links'][0]['rel']
        self.assertIn('hea-default', rel)


class TestGetAll(TestCase, GetAllMixin):
    """Test case for GET all requests specific to organizations."""
    pass


class TestPost(TestCase, PostMixin):
    pass

async def _mock_update_group_membership(request, user, added_groups, deleted_groups, group_url_getter):
    pass

async def _mock_update_volumes_and_credentials(app, changed):
    pass

@patch('heaserver.organization.service._update_group_membership', _mock_update_group_membership)
@patch('heaserver.organization.service._update_volumes_and_credentials', _mock_update_volumes_and_credentials)
class TestPut(TestCase, PutMixin):
    pass


class TestDelete(TestCase, DeleteMixin):
    pass
