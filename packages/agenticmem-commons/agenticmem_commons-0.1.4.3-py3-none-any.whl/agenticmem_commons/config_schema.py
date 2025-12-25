from enum import IntEnum
from pydantic import BaseModel
from typing import Optional


class StorageConfigTest(IntEnum):
    UNKNOWN = 0
    INCOMPLETE = 1
    FAILED = 2
    SUCCEEDED = 3


class StorageConfigLocal(BaseModel):
    dir_path: str


class StorageConfigS3(BaseModel):
    s3_region: str
    s3_path: str
    s3_access_key: str
    s3_secret_key: str


class StorageConfigSupabase(BaseModel):
    url: str
    key: str
    db_url: str


StorageConfig = StorageConfigLocal | StorageConfigS3 | StorageConfigSupabase | None


class ProfileExtractorConfig(BaseModel):
    profile_content_definition_prompt: str
    context_prompt: Optional[str] = None
    metadata_definition_prompt: Optional[str] = None
    should_extract_profile_prompt_override: Optional[str] = None
    request_sources_enabled: Optional[
        list[str]
    ] = None  # default enabled for all sources, if set, only extract profiles from the enabled request sources


class FeedbackAggregatorConfig(BaseModel):
    min_feedback_threshold: int = 2
    refresh_count: int = 2


class AgentFeedbackConfig(BaseModel):
    feedback_name: str
    # define what success looks like
    feedback_definition_prompt: str
    metadata_definition_prompt: Optional[str] = None
    feedback_aggregator_config: Optional[FeedbackAggregatorConfig] = None


class ToolUseConfig(BaseModel):
    tool_name: str
    tool_description: str


# define what success looks like for agent
class AgentSuccessConfig(BaseModel):
    evaluation_name: str
    success_definition_prompt: str
    tool_can_use: Optional[list[ToolUseConfig]] = None
    # action agent can take
    action_space: Optional[list[str]] = None
    metadata_definition_prompt: Optional[str] = None
    sampling_rate: float = 1.0  # percentage of batch of interactions (defined by extraction_window_size and extraction_window_stride) to be sampled for success evaluation


class Config(BaseModel):
    # define where user configuration is stored at
    storage_config: StorageConfig
    storage_config_test: Optional[StorageConfigTest] = StorageConfigTest.UNKNOWN
    # define agent working environment, tool can use and action space
    agent_context_prompt: Optional[str] = None
    # user level memory
    profile_extractor_configs: Optional[list[ProfileExtractorConfig]] = None
    # agent level feedback
    agent_feedback_configs: Optional[list[AgentFeedbackConfig]] = None
    # agent level success
    agent_success_configs: Optional[list[AgentSuccessConfig]] = None
    # sliding window parameters for extraction
    extraction_window_size: Optional[int] = None
    extraction_window_stride: Optional[int] = None
