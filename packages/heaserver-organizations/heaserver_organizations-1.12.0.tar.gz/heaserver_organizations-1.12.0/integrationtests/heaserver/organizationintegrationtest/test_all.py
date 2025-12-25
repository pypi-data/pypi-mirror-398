from .testcase import TestCase
from heaserver.service.testcase.mixin import PostMixin, PutMixin
from unittest.mock import patch


# class TestPost(TestCase, PostMixin):
#     # We should test POSTing with group membership, volumes, and credentials.
#     pass

# async def _mock_update_group_membership(request, user, added_groups, deleted_groups, group_url_getter):
#     pass

# async def _mock_update_volumes_and_credentials(app, changed):
#     pass

# @patch('heaserver.organization.service._update_group_membership', _mock_update_group_membership)
# @patch('heaserver.organization.service._update_volumes_and_credentials', _mock_update_volumes_and_credentials)
# class TestPut(TestCase, PutMixin):
#     pass

