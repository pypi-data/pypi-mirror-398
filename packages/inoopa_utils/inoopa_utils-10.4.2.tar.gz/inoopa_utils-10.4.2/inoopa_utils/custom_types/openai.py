from enum import StrEnum


class OpenAIModels(StrEnum):
    GPT3_TURBO = "gpt-3.5-turbo-0125"
    GPT4 = "gpt-4-0613"
    GPT4_TURBO = "gpt-4-turbo-2024-04-09"
    GPT4_TURBO_PREVIEW = "gpt-4-1106-preview"
    GPT4_O = "gpt-4o"
    GPT4_O_MINI = "gpt-4o-mini"


MODEL_TOKEN_LIMITS = {
    OpenAIModels.GPT3_TURBO: 16_385,
    OpenAIModels.GPT4: 8192,
    OpenAIModels.GPT4_TURBO: 128_000,
    OpenAIModels.GPT4_TURBO_PREVIEW: 128_000,
    OpenAIModels.GPT4_O: 128_000,
    OpenAIModels.GPT4_O_MINI: 128_000,
}
