import datetime as _dt


class TimestampMixin:
    created_at: _dt.datetime | None = None
    updated_at: _dt.datetime | None = None

    def pre_create(self) -> None:
        self.created_at = _dt.datetime.now(tz=_dt.UTC)
        super().pre_create()  # type: ignore[misc]

    async def apre_create(self) -> None:
        self.created_at = _dt.datetime.now(tz=_dt.UTC)
        await super().apre_create()  # type: ignore[misc]

    def pre_update(self) -> None:
        self.updated_at = _dt.datetime.now(tz=_dt.UTC)

        if not self.created_at:
            _metadata = self.get_metadata()  # type: ignore[attr-defined]
            self.created_at = _dt.datetime.fromtimestamp(_metadata.created_at / 1000, tz=_dt.UTC)

        super().pre_update()  # type: ignore[misc]

    async def apre_update(self) -> None:
        self.updated_at = _dt.datetime.now(tz=_dt.UTC)
        if not self.created_at:
            _metadata = await self.aget_metadata()  # type: ignore[attr-defined]
            self.created_at = _dt.datetime.fromtimestamp(_metadata.created_at / 1000, tz=_dt.UTC)

        await super().apre_update()  # type: ignore[misc]
