from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class FindCardsRequest(BaseModel):
    img: str = Field(..., min_length=100, description="img base64 string")
    region: Optional[List[int]] = Field(
        None, min_length=4, max_length=4, description="识别区域[x,y,w,h]"
    )
    is_align_y: bool = Field(False, description="是否对齐Y轴")
    is_preprocess: bool = Field(
        True, description="是否预处理图片,如何识别效果不好,可以预处理"
    )


class FindOneRequest(BaseModel):
    img: str = Field(..., min_length=100, description="img base64 string")
    target: str | None = Field(None, description="需识别的目标文本")
    region: Optional[List[int]] = Field(
        None, min_length=4, max_length=4, description="识别区域[x,y,w,h]"
    )
    is_preprocess: bool = Field(
        True, description="是否预处理图片,如何识别效果不好,可以预处理"
    )


class FindNRequest(BaseModel):
    img: str = Field(..., min_length=100, description="img base64 string")
    target_list: List[str] = Field(..., description="需识别的N个目标列表")
    region: Optional[List[int]] = Field(
        None, min_length=4, max_length=4, description="识别区域[x,y,w,h]"
    )
    is_preprocess: bool = Field(
        True, description="是否预处理图片,如何识别效果不好,可以预处理"
    )


class Region(BaseModel):
    region: List[int] = Field(
        ..., min_length=4, max_length=4, description="识别区域[x,y,w,h]"
    )
    type: Literal["list", "text", "cards"] = Field(..., description="识别类型")
    is_align_y: bool = Field(False, description="是否对齐Y轴")
    target_list: List[str] = Field([], description="需识别的目标文本列表")
    target: str = Field("", description="需识别的目标文本")
    is_preprocess: bool = Field(
        False, description="是否预处理图片,如何识别效果不好,可以预处理"
    )


class FindRegionsRequest(BaseModel):
    img: str = Field(..., min_length=100, description="img base64 string")
    regions: List[Region] = Field(..., description="识别区域配置")
    is_preprocess: bool = Field(
        False, description="是否预处理图片,如何识别效果不好,可以预处理"
    )
