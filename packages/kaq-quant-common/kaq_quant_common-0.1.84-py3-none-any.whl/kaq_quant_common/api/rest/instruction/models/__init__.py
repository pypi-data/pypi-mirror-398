# 定义model
from typing import Optional

from pydantic import BaseModel


#
class InstructionRequestBase(BaseModel):
    # 时间
    event_time: Optional[int] = None
    # 任务id
    task_id: Optional[str] = None


class InstructionResponseBase(BaseModel):
    # 时间
    event_time: Optional[int] = None
