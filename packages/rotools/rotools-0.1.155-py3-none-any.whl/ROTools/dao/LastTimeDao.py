from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime

from ROTools.dao.BaseDao import get_rotools_base


class LastTimeDao(get_rotools_base()):
    __tablename__ = "last_time"

    key = Column(String, primary_key=True, autoincrement=False)
    value = Column(DateTime(timezone=True), nullable=False)

    def __init__(self, name):
        super().__init__()
        self.key = name
        self.value = datetime.now(timezone.utc)

    def get_delta(self):
        return datetime.now(timezone.utc) - self.value