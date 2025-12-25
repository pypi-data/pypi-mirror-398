from httpx import Request

from .base import BaseResource


class CompanyResource(BaseResource):
    def list_companies(self) -> Request:
        """Get all companies associated with the client."""
        endpoint = '/public/inventory/v1/companies'
        return self._build_request('GET', endpoint)

    def list_subdepartments(self, *, company_id, reference_company_id):
        """
        Provides a list of subdepartments for the specified company.
        Creation of subdepartments can only be performed in the application.
        """
        endpoint = f'/public/inventory/v1/companies/subdepartments'
        params = {'company_id': company_id, 'reference_company_id': reference_company_id}
        return self._build_request('GET', endpoint, params=params)

    def list_templates(self, *, company_id: int | None = None):
        """
        Get a list of all task templates associated with the company.
        Company ID is required for clients with multi-company access.
        """
        endpoint = '/public/inventory/v1/companies/templates'
        params = {'company_id': company_id}
        return self._build_request('GET', endpoint, params=params)