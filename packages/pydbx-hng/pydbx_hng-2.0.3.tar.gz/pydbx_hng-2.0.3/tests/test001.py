from pydbx_hng.models.base.base_model import BaseModel
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID

class TestModel(BaseModel):
    
    __tablename__ = "user_test"
    __table_args__ = {"schema": "test_schema"}
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default="gen_random_uuid()"
    )
    
tm = TestModel()
tm.id = 'AAA'
print(tm.id)
