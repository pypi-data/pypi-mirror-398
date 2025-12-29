from pydantic import BaseModel

from tamar_model_client.enums import ProviderType, InvokeType
from tamar_model_client.enums.channel import Channel


class UserContext(BaseModel):
    org_id: str  # 组织id
    user_id: str  # 用户id
    client_type: str  # 客户端类型，这里记录的是哪个服务请求过来的


class TamarFileIdInput(BaseModel):
    file_id: str


class BaseRequest(BaseModel):
    provider: ProviderType  # 供应商，如 "openai", "google" 等
    channel: Channel = Channel.NORMAL  # 渠道：不同服务商之前有不同的调用SDK，这里指定是调用哪个SDK
    invoke_type: InvokeType = InvokeType.GENERATION  # 模型调用类型：generation-生成模型调用
