from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Integer, LargeBinary

from ROTools.dao.BaseDao import get_rotools_base


class TaskDao(get_rotools_base()):
    __tablename__ = "tasks_pending"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target = Column(String, nullable=False)
    name = Column(String, nullable=False)

    data = Column(LargeBinary, nullable=True)

    inserted_at = Column(DateTime(timezone=True), nullable=False,  default=lambda: datetime.now(timezone.utc))

    def __init__(self, target, name, data):
        super().__init__()
        self.target = target
        self.name = name
        self.data = data