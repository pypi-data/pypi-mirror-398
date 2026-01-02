from clipped.utils.enums import PEnum


class PatchStrategy(str, PEnum):
    REPLACE = "replace"
    ISNULL = "isnull"
    POST_MERGE = "post_merge"
    PRE_MERGE = "pre_merge"

    @classmethod
    def is_replace(cls, value):
        return value == cls.REPLACE

    @classmethod
    def is_null(cls, value):
        return value == cls.ISNULL

    @classmethod
    def is_post_merge(cls, value):
        return value == cls.POST_MERGE

    @classmethod
    def is_pre_merge(cls, value):
        return value == cls.PRE_MERGE
