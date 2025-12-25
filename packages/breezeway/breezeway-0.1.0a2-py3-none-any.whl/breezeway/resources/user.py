from httpx import Request

from .base import BaseResource
from ..models.user import UserStatus


class UserResource(BaseResource):
    def list_users(self, *, status: UserStatus = UserStatus.ACTIVE) -> Request:
        """List users with the specified status"""
        endpoint = '/public/inventory/v1/people'
        params = {'status': status}
        return self._build_request('GET', endpoint, params=params)

    def retrieve_user(self, user_id):
        """
        Retrieve a user by their ID.
        """
        endpoint = f'/public/inventory/v1/people/{user_id}'
        return self._build_request('GET', endpoint)