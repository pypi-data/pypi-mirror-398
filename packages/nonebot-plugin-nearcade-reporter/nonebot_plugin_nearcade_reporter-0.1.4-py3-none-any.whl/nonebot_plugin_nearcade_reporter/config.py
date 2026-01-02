import re

from pydantic import (
    BaseModel,
    field_validator,
    model_validator,
)
from typing_extensions import Self

from nonebot_plugin_nearcade_reporter.errors import (
    InvalidArcadeSourceError,
    InvalidRegexError,
    MissingRegexGroupError,
)

from pydantic import PrivateAttr


class QueryAttendanceRegexConfig(BaseModel):
    enable: bool = True
    pattern: str = r"^(?P<arcade>\S+)几人$"
    reply_message: str = "{arcade} 当前人数: {count}"

    @staticmethod
    def _extract_group_names(pattern: str) -> set[str]:
        try:
            regex = re.compile(pattern)
        except re.error as e:
            raise InvalidRegexError(str(e)) from e

        return set(regex.groupindex.keys())

    @model_validator(mode="after")
    def validate_group_names(self) -> Self:
        groups = self._extract_group_names(self.pattern)

        if "arcade" not in groups:
            raise MissingRegexGroupError("arcade", groups)

        return self


class UpdateAttendanceRegexConfig(BaseModel):
    enable: bool = True
    pattern: str = r"^机厅人数\s*(?P<arcade>\S+)\s*(?P<count>(?:100|[1-9]\d?|0))$"
    enable_reply: bool = True
    reply_message: str = "更新成功，{arcade} 当前人数: {count}"

    @staticmethod
    def _extract_group_names(pattern: str) -> set[str]:
        try:
            regex = re.compile(pattern)
        except re.error as e:
            raise InvalidRegexError(str(e)) from e

        return set(regex.groupindex.keys())

    @model_validator(mode="after")
    def validate_group_names(self) -> Self:
        groups = self._extract_group_names(self.pattern)

        if "arcade" not in groups:
            raise MissingRegexGroupError("arcade", groups)

        if "count" not in groups:
            raise MissingRegexGroupError("count", groups)
        return self


class ArcadeConfig(BaseModel):
    name: str
    arcade_source: str
    aliases: set[str]
    default_game_id: int

    @field_validator("arcade_source")
    @classmethod
    def validate_source_availability(cls, value: str) -> str:
        if value not in {"bemanicn", "ziv"}:
            raise InvalidArcadeSourceError(value)
        return value


class Config(BaseModel):
    api_token: str = ""
    query_attendance_match: QueryAttendanceRegexConfig = QueryAttendanceRegexConfig()
    update_attendance_match: UpdateAttendanceRegexConfig = UpdateAttendanceRegexConfig()
    arcades: dict[int, ArcadeConfig] = {}

    _alias_index: dict[str, set[int]] = PrivateAttr(default_factory=dict)

    @model_validator(mode="after")
    def build_alias_index(self) -> Self:
        index: dict[str, set[int]] = {}

        for arcade_id, arcade in self.arcades.items():
            name_list = arcade.aliases.union({arcade.name})
            for alias in name_list:
                key = alias.casefold()
                index.setdefault(key, set()).add(arcade_id)

        self._alias_index = index
        return self

    def find_arcade_by_alias(self, arcade_name: str) -> dict[int, ArcadeConfig]:
        key = arcade_name.casefold()

        arcade_ids = self._alias_index.get(key)
        if not arcade_ids:
            return {}

        return {arcade_id: self.arcades[arcade_id] for arcade_id in arcade_ids}
