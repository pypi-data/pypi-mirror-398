from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class ImageInfo(BaseModel):
    url: str = Field(..., description="图片链接")
    width: Optional[int] = Field(None, description="宽")
    height: Optional[int] = Field(None, description="高")
    shape: str = Field(..., description="横长方形/竖长方形/方形")


class WebItem(BaseModel):
    id: str = Field(..., description="结果Id")
    sort_id: int = Field(..., description="排序Id")
    title: str = Field(..., description="标题")
    site_name: Optional[str] = Field(None, description="站点名")
    url: Optional[str] = Field(None, description="落地页")
    snippet: str = Field(..., description="普通摘要")
    summary: Optional[str] = Field(None, description="精准摘要")
    content: Optional[str] = Field(None, description="正文")
    publish_time: Optional[str] = Field(None, description="发布时间")
    logo_url: Optional[str] = Field(None, description="落地页IconUrl链接")
    rank_score: Optional[float] = Field(None, description="得分")
    auth_info_des: str = Field(..., description="权威度描述")
    auth_info_level: int = Field(..., description="权威度评级")


class ImageItem(BaseModel):
    id: str = Field(..., description="结果Id")
    sort_id: int = Field(..., description="排序Id")
    title: Optional[str] = Field(None, description="标题")
    site_name: Optional[str] = Field(None, description="站点名")
    url: Optional[str] = Field(None, description="落地页")
    publish_time: Optional[str] = Field(None, description="发布时间")
    image: ImageInfo = Field(..., description="图片详情")


class SearchFilter(BaseModel):
    need_content: Optional[bool] = Field(False, description="是否仅返回有正文的结果")
    need_url: Optional[bool] = Field(False, description="是否仅返回原文链接的结果")
    sites: Optional[str] = Field(None, description="指定搜索的Site范围")
    block_hosts: Optional[str] = Field(None, description="指定屏蔽的搜索Site")


class SearchRequest(BaseModel):
    query: str = Field(..., description="用户搜索query")
    search_type: Literal["web", "web_summary", "image"] = Field("web", description="搜索类型")
    count: Optional[int] = Field(10, description="返回条数")
    filter: Optional[SearchFilter] = None
    need_summary: Optional[bool] = Field(True, description="是否需要精准摘要")
    time_range: Optional[str] = Field(None, description="指定搜索的发文时间")


class SearchResponse(BaseModel):
    web_items: List[WebItem] = Field(default_factory=list, description="Web搜索结果")
    image_items: List[ImageItem] = Field(default_factory=list, description="图片搜索结果")
    summary: Optional[str] = Field(None, description="搜索结果摘要")
