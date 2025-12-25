from pushikoo_interface import PusherConfig, PusherInstanceConfig
from pydantic import BaseModel, Field

# PusherConfig and PusherInstanceConfig inherit from pydantic.BaseModel,
# so when defining your own ClassConfig / InstanceConfig,
# you are essentially defining a BaseModel and can fully use all BaseModel features.


class AdapterConfig(PusherConfig):
    class Authentication(BaseModel):
        token: str = Field(default="7070707", description="Token for authentication")
        userid: str = Field(default="123456", description="My User ID")

    authentications: dict[str, Authentication] = Field(
        default_factory=lambda: {
            "my1": AdapterConfig.Authentication(),
            "my2": AdapterConfig.Authentication(),
        },
        description="Authentications",
    )


class InstanceConfig(PusherInstanceConfig):
    auth: str = Field(default="my1", description="Using Authentication")
    to_userid: str = Field(
        default="123456", description="User ID which is going to push to"
    )
