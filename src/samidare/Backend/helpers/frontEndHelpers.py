from pydantic import BaseModel
from typing import List

class Config(BaseModel):
    ip: int
    output: bool
    polarity: str
    trigger: str
    threshold: float
    gain: int
    samples: int
    pre_samples: int
    clock_type: int

# # New model to accept a list of Configs under 'channels'
# class ChannelConfigRequest(BaseModel):
#     channels: List[Config]