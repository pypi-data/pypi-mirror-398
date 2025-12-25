from importlib.metadata import version, PackageNotFoundError

__app_name__ = "agenticmem"

try:
    __version__ = version(__app_name__)
except PackageNotFoundError:
    # Package is not installed (e.g., running from source without installing)
    __version__ = "0.0.0-dev"


from .client import AgenticMemClient
from agenticmem_commons.api_schema.service_schemas import (
    UserActionType,
    ProfileTimeToLive,
    InteractionData,
    Interaction,
    UserProfile,
    PublishUserInteractionRequest,
    PublishUserInteractionResponse,
    DeleteUserProfileRequest,
    DeleteUserProfileResponse,
    DeleteUserInteractionRequest,
    DeleteUserInteractionResponse,
    RawFeedback,
    AddRawFeedbackRequest,
    AddRawFeedbackResponse,
    RerunProfileGenerationRequest,
    RerunProfileGenerationResponse,
    RerunFeedbackGenerationRequest,
    RerunFeedbackGenerationResponse,
    Status,
    FeedbackStatus,
)
from agenticmem_commons.api_schema.retriever_schema import (
    SearchInteractionRequest,
    SearchUserProfileRequest,
    SearchInteractionResponse,
    SearchUserProfileResponse,
)
from agenticmem_commons.config_schema import (
    StorageConfigTest,
    StorageConfigLocal,
    StorageConfigS3,
    StorageConfigSupabase,
    StorageConfig,
    ProfileExtractorConfig,
    FeedbackAggregatorConfig,
    AgentFeedbackConfig,
    AgentSuccessConfig,
    ToolUseConfig,
    Config,
)

debug = False
log = None  # Set to either 'debug' or 'info', controls console logging


__all__ = [
    "AgenticMemClient",
    "UserActionType",
    "ProfileTimeToLive",
    "InteractionData",
    "Interaction",
    "UserProfile",
    "PublishUserInteractionRequest",
    "PublishUserInteractionResponse",
    "DeleteUserProfileRequest",
    "DeleteUserProfileResponse",
    "DeleteUserInteractionRequest",
    "DeleteUserInteractionResponse",
    "RawFeedback",
    "AddRawFeedbackRequest",
    "AddRawFeedbackResponse",
    "RerunProfileGenerationRequest",
    "RerunProfileGenerationResponse",
    "RerunFeedbackGenerationRequest",
    "RerunFeedbackGenerationResponse",
    "SearchInteractionRequest",
    "SearchUserProfileRequest",
    "SearchInteractionResponse",
    "SearchUserProfileResponse",
    "StorageConfigTest",
    "StorageConfigLocal",
    "StorageConfigS3",
    "StorageConfigSupabase",
    "StorageConfig",
    "ProfileExtractorConfig",
    "FeedbackAggregatorConfig",
    "AgentFeedbackConfig",
    "AgentSuccessConfig",
    "ToolUseConfig",
    "Config",
    "Status",
    "FeedbackStatus"
]
