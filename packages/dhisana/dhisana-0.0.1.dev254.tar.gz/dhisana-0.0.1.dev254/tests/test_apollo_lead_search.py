import pytest
from unittest.mock import AsyncMock, patch

from src.dhisana.schemas.sales import LeadsQueryFilters
from src.dhisana.utils.apollo_tools import search_leads_with_apollo_page


@pytest.fixture
def apollo_people_response():
    return {
        "pagination": {
            "page": 1,
            "per_page": 25,
            "total_entries": 1,
            "total_pages": 1,
        },
        "people": [
            {
                "id": "person_1",
                "name": "Alex Example",
                "first_name": "Alex",
                "last_name": "Example",
                "title": "VP Sales",
                "headline": "Revenue leader",
                "email": "alex@example.com",
                "linkedin_url": "https://linkedin.com/in/alex-example",
                "city": "San Francisco",
                "state": "California",
                "organization": {
                    "name": "Example Inc",
                    "primary_domain": "example.com",
                    "linkedin_url": "https://linkedin.com/company/example",
                    "website_url": "https://example.com",
                    "keywords": ["SaaS", "Sales"],
                },
                "contact": {"sanitized_phone": "+1-555-0100"},
            }
        ],
        "contacts": [],
    }


@pytest.fixture
def tool_config():
    return [
        {
            "name": "apollo",
            "configuration": [
                {"name": "apiKey", "value": "test_api_key"},
            ],
        }
    ]


@pytest.mark.asyncio
async def test_search_leads_with_apollo_page_parses_url_filters(apollo_people_response, tool_config):
    example_url = (
        "https://app.apollo.io/#/people?page=1&personTitles[]=VP%20Sales&"
        "organizationLatestFundingStageCd[]=3&organizationLatestFundingStageCd[]=4&"
        "organizationLatestFundingStageCd[]=5&qOrganizationJobTitles[]=SDR&"
        "qOrganizationJobTitles[]=account%20executive&"
        "organizationIndustries[]=information%20technology%20%26%20services&"
        "organizationIndustryTagIds[]=5567cd4773696439b10b0000"
    )

    with patch(
        "src.dhisana.utils.apollo_tools.fetch_apollo_data",
        new=AsyncMock(return_value=apollo_people_response),
    ) as mock_fetch_data, patch(
        "src.dhisana.utils.apollo_tools.get_apollo_access_token",
        return_value=("test_api_key", False),
    ):
        result = await search_leads_with_apollo_page(
            query=LeadsQueryFilters(),
            page=1,
            per_page=25,
            example_url=example_url,
            tool_config=tool_config,
        )

    assert result["current_page"] == 1
    assert result["total_entries"] == 1
    assert len(result["results"]) == 1

    payload = mock_fetch_data.call_args[0][3]
    assert payload["q_organization_job_titles"] == ["SDR", "account executive"]
    assert payload["organization_latest_funding_stage_cd"] == ["3", "4", "5"]
    assert payload["organization_industries"] == ["information technology & services"]
    assert payload["organization_industry_tag_ids"] == ["5567cd4773696439b10b0000"]


@pytest.mark.asyncio
async def test_search_leads_with_apollo_page_uses_query_filters(apollo_people_response, tool_config):
    query = LeadsQueryFilters(
        person_current_titles=["Head of Sales"],
        job_openings_with_titles=["SDR", "Account Executive"],
        latest_funding_stages=["3", "4"],
        organization_num_employees_ranges=["201,500"],
        industries=["information technology & services"],
        company_industry_tag_ids=["5567cd4773696439b10b0000"],
    )

    with patch(
        "src.dhisana.utils.apollo_tools.fetch_apollo_data",
        new=AsyncMock(return_value=apollo_people_response),
    ) as mock_fetch_data, patch(
        "src.dhisana.utils.apollo_tools.get_apollo_access_token",
        return_value=("test_api_key", False),
    ):
        result = await search_leads_with_apollo_page(
            query=query,
            page=2,
            per_page=50,
            tool_config=tool_config,
        )

    assert result["current_page"] == 1
    assert len(result["results"]) == 1

    payload = mock_fetch_data.call_args[0][3]
    assert payload["page"] == 2
    assert payload["per_page"] == 50
    assert payload["person_titles"] == ["Head of Sales"]
    assert payload["q_organization_job_titles"] == ["SDR", "Account Executive"]
    assert payload["organization_latest_funding_stage_cd"] == ["3", "4"]
    assert payload["organization_industries"] == ["information technology & services"]
    assert payload["organization_industry_tag_ids"] == ["5567cd4773696439b10b0000"]
