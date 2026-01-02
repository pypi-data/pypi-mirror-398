class InvalidRegexError(ValueError):
    def __init__(self, detail: str) -> None:
        super().__init__(f"无效的正则表达式: {detail}")


class MissingRegexGroupError(ValueError):
    def __init__(self, group_name: str, available: set[str]) -> None:
        super().__init__(
            f"分组 '{group_name}' 不存在于 regex 中，可用分组: {available}"
        )

class InvalidArcadeSourceError(ValueError):
    def __init__(self, source: str) -> None:
        super().__init__(f"无效的机厅来源: {source}")

class ArcadeNotFoundError(ValueError):
    def __init__(self, name: str) -> None:
        super().__init__(f"未找到机厅: {name}")
