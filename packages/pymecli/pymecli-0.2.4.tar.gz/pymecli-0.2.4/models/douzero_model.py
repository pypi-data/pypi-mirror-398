from typing import Literal

from pydantic import BaseModel, Field, field_validator


class BidScoreRequest(BaseModel):
    cards: str = Field(..., min_length=17, max_length=17, description="cards str")


class PreGameScoreRequest(BaseModel):
    cards: str = Field(..., description="cards str")
    three: str = Field(..., min_length=3, max_length=3, description="三张底牌")
    position_code: Literal["0", "1", "2"] = Field(
        ...,
        description="0:我是地主上家,1:我是地主,2:我是地主下家",
    )

    @field_validator("cards")
    def validate_cards_length(cls, v):
        if len(v) not in [17, 20]:
            raise ValueError("cards length must be either 17 or 20")
        return v


class PlayRequest(BaseModel):
    cards: str = Field(..., description="开局前的手牌,17或20张")
    other_cards: str | None = Field("", description="开局前其他玩家手牌,34张或37张")
    played_list: list[str] = Field([], description="played list")
    three: str = Field(..., min_length=3, max_length=3, description="三张底牌")
    position_code: Literal[0, 1, 2] = Field(
        ...,
        description="0:地主在右边;1:我是地主;2:地主在左边",
    )

    @field_validator("cards")
    def validate_cards_length(cls, v):
        if len(v) not in [17, 20]:
            raise ValueError("cards length must be either 17 or 20")
        return v

    @field_validator("other_cards")
    def validate_other_cards_length(cls, v):
        if len(v) not in [37, 34, 0] and v is not None:
            raise ValueError("cards length must be either 37 or 34")
        return v
