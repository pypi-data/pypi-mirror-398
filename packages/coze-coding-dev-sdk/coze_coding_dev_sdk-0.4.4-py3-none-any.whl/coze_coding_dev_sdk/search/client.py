from typing import Dict, List, Optional

from coze_coding_utils.runtime_ctx.context import Context
from cozeloop.decorator import observe

from ..core.client import BaseClient
from ..core.config import Config
from ..core.exceptions import APIError
from .models import ImageItem, SearchFilter, SearchRequest, SearchResponse, WebItem


def _convert_to_api_format(data: dict) -> dict:
    result = {}
    for key, value in data.items():
        if value is None:
            continue
        if key == "query":
            result["Query"] = value
        elif key == "search_type":
            result["SearchType"] = value
        elif key == "count":
            result["Count"] = value
        elif key == "need_summary":
            result["NeedSummary"] = value
        elif key == "time_range":
            result["TimeRange"] = value
        elif key == "filter" and value:
            result["Filter"] = {
                "NeedContent": value.get("need_content", False),
                "NeedUrl": value.get("need_url", False),
                "Sites": value.get("sites"),
                "BlockHosts": value.get("block_hosts"),
            }
    return result


def _convert_from_api_format(item: dict) -> dict:
    result = {}
    for key, value in item.items():
        if key == "Id":
            result["id"] = value
        elif key == "SortId":
            result["sort_id"] = value
        elif key == "Title":
            result["title"] = value
        elif key == "SiteName":
            result["site_name"] = value
        elif key == "Url":
            result["url"] = value
        elif key == "Snippet":
            result["snippet"] = value
        elif key == "Summary":
            result["summary"] = value
        elif key == "Content":
            result["content"] = value
        elif key == "PublishTime":
            result["publish_time"] = value
        elif key == "LogoUrl":
            result["logo_url"] = value
        elif key == "RankScore":
            result["rank_score"] = value
        elif key == "AuthInfoDes":
            result["auth_info_des"] = value
        elif key == "AuthInfoLevel":
            result["auth_info_level"] = value
        elif key == "Image":
            result["image"] = {
                "url": value.get("Url"),
                "width": value.get("Width"),
                "height": value.get("Height"),
                "shape": value.get("Shape"),
            }
    return result


class SearchClient(BaseClient):
    def __init__(
        self,
        config: Optional[Config] = None,
        ctx: Optional[Context] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        verbose: bool = False,
    ):
        super().__init__(config, ctx, custom_headers, verbose)
        self.base_url = self.config.base_url

    @observe(name="web_search")
    def search(
        self,
        query: str,
        search_type: str = "web",
        count: Optional[int] = 10,
        need_content: Optional[bool] = False,
        need_url: Optional[bool] = False,
        sites: Optional[str] = None,
        block_hosts: Optional[str] = None,
        need_summary: Optional[bool] = True,
        time_range: Optional[str] = None,
    ) -> SearchResponse:
        search_filter = SearchFilter(
            need_content=need_content,
            need_url=need_url,
            sites=sites,
            block_hosts=block_hosts,
        )

        request = SearchRequest(
            query=query,
            search_type=search_type,
            count=count,
            filter=search_filter,
            need_summary=need_summary,
            time_range=time_range,
        )

        api_request = _convert_to_api_format(request.model_dump(exclude_none=True))

        response = self._request(
            method="POST",
            url=f"{self.base_url}/api/search_api/web_search",
            json=api_request,
        )

        response_metadata = response.get("ResponseMetadata", {})
        if response_metadata.get("Error"):
            raise APIError(f"Search failed: {response_metadata.get('Error')}")

        result = response.get("Result", {})

        web_items = []
        if result.get("WebResults"):
            web_items = [
                WebItem(**_convert_from_api_format(item))
                for item in result.get("WebResults", [])
            ]

        image_items = []
        if result.get("ImageResults"):
            image_items = [
                ImageItem(**_convert_from_api_format(item))
                for item in result.get("ImageResults", [])
            ]

        summary = None
        if result.get("Choices"):
            summary = (
                result.get("Choices", [{}])[0].get("Message", {}).get("Content", "")
            )

        return SearchResponse(
            web_items=web_items, image_items=image_items, summary=summary
        )

    @observe(name="web_search_simple")
    def web_search(
        self,
        query: str,
        count: Optional[int] = 10,
        need_summary: Optional[bool] = True,
    ) -> SearchResponse:
        return self.search(
            query=query, search_type="web", count=count, need_summary=need_summary
        )

    @observe(name="web_search_with_summary")
    def web_search_with_summary(
        self,
        query: str,
        count: Optional[int] = 10,
    ) -> SearchResponse:
        return self.search(
            query=query, search_type="web_summary", count=count, need_summary=True
        )

    @observe(name="image_search")
    def image_search(
        self,
        query: str,
        count: Optional[int] = 10,
    ) -> SearchResponse:
        return self.search(
            query=query, search_type="image", count=count, need_summary=False
        )
