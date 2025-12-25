from pydantic import BaseModel, ConfigDict, Field


class SelectModelRequest(BaseModel):
    prompt: str
    cost_bias: float | None = None
    models: list[str] | None = None
    semantic_cache_threshold: float | None = None


class SelectModelResponse(BaseModel):
    selected_model: str | None = None
    cache_tier: str | None = None
    alternatives: list[str] | None = None


class RegistryArchitectureModality(BaseModel):
    modality_type: str | None = None
    modality_value: str | None = None


class RegistryDefaultParametersValues(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    frequency_penalty: float | None = None
    logprobs: bool | None = None
    max_completion_tokens: float | None = None
    max_tokens: float | None = None
    min_p: float | None = None
    n: float | None = Field(default=None, alias="n")
    parallel_tool_calls: bool | None = None
    seed: float | None = None
    stop_sequences: list[str] | None = None
    store: bool | None = None
    temperature: float | None = None
    top_a: float | None = None
    top_k: float | None = None
    top_logprobs: float | None = None
    top_p: float | None = None


class RegistryModelDefaultParameters(BaseModel):
    parameters: RegistryDefaultParametersValues | None = None


class RegistryProviderPricing(BaseModel):
    audio_cost: str | None = None
    completion_cost: str | None = None
    discount: str | None = None
    image_cost: str | None = None
    image_output_cost: str | None = None
    input_audio_cache_cost: str | None = None
    input_cache_read_cost: str | None = None
    input_cache_write_cost: str | None = None
    prompt_cost: str | None = None
    request_cost: str | None = None


class RegistryModelProvider(BaseModel):
    context_length: int | None = None
    is_zdr: str | None = None
    max_completion_tokens: int | None = None
    max_prompt_tokens: int | None = None
    name: str | None = None
    pricing: RegistryProviderPricing | None = None
    provider_model_name: str | None = None
    provider_name: str | None = None
    quantization: str | None = None
    status: int | None = None
    supports_implicit_caching: str | None = None
    tag: str | None = None
    uptime_last_30m: str | None = None


class RegistryModelSupportedParameter(BaseModel):
    parameter_name: str | None = None


class RegistryModelTopProvider(BaseModel):
    context_length: int | None = None
    is_moderated: str | None = None
    max_completion_tokens: int | None = None


class RegistryModelPricingEntity(BaseModel):
    completion_cost: str | None = None
    image_cost: str | None = None
    internal_reasoning_cost: str | None = None
    prompt_cost: str | None = None
    request_cost: str | None = None
    web_search_cost: str | None = None


class RegistryModelArchitecture(BaseModel):
    instruct_type: str | None = None
    modalities: list[RegistryArchitectureModality] | None = None
    modality: str | None = None
    tokenizer: str | None = None


class RegistryModel(BaseModel):
    architecture: RegistryModelArchitecture | None = None
    author: str | None = None
    context_length: int | None = None
    created_at: str | None = None
    default_parameters: RegistryModelDefaultParameters | None = None
    description: str | None = None
    display_name: str | None = None
    id: int | None = None
    last_updated: str | None = None
    model_name: str | None = None
    pricing: RegistryModelPricingEntity | None = None
    providers: list[RegistryModelProvider] | None = None
    supported_parameters: list[RegistryModelSupportedParameter] | None = None
    top_provider: RegistryModelTopProvider | None = None


class RegistryProvider(BaseModel):
    active_count: int | None = None
    endpoint_count: int | None = None
    model_count: int | None = None
    name: str | None = None
    quantizations: list[str] | None = None
    tags: list[str] | None = None


class RegistryModelsQuery(BaseModel):
    author: str | None = None
    model_name: str | None = None
    endpoint_tag: str | None = None
    provider: str | None = None
    input_modality: str | None = None
    output_modality: str | None = None
    min_context_length: int | None = None
    max_prompt_cost: str | None = None
    max_completion_cost: str | None = None
    supported_param: str | None = None
    status: int | None = None
    quantization: str | None = None


class RegistryProvidersQuery(BaseModel):
    tag: str | None = None
    status: int | None = None
    input_modality: str | None = None
    output_modality: str | None = None
    min_context_length: int | None = None
    has_pricing: bool | None = None
    quantization: str | None = None
