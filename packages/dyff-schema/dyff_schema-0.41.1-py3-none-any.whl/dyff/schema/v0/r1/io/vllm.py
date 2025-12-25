# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

from typing import Optional, Union

import pydantic

from ..base import DyffSchemaBaseModel


class InferenceParameters(DyffSchemaBaseModel):
    n: int = pydantic.Field(
        default=1,
        description="Number of output sequences to return for the given prompt.",
    )
    best_of: Optional[int] = pydantic.Field(
        default=None,
        description="""Number of output sequences that are generated from the prompt.
            From these `best_of` sequences, the top `n` sequences are returned.
            `best_of` must be greater than or equal to `n`. This is treated as
            the beam width when `use_beam_search` is True. By default, `best_of`
            is set to `n`.""",
    )
    presence_penalty: float = pydantic.Field(
        default=0.0,
        description="""Float that penalizes new tokens based on whether they
            appear in the generated text so far. Values > 0 encourage the model
            to use new tokens, while values < 0 encourage the model to repeat
            tokens.""",
    )
    frequency_penalty: float = pydantic.Field(
        default=0.0,
        description="""Float that penalizes new tokens based on their
            frequency in the generated text so far. Values > 0 encourage the
            model to use new tokens, while values < 0 encourage the model to
            repeat tokens.""",
    )
    temperature: float = pydantic.Field(
        default=1.0,
        description="""Float that controls the randomness of the sampling. Lower
            values make the model more deterministic, while higher values make
            the model more random. Zero means greedy sampling.""",
    )
    top_p: float = pydantic.Field(
        default=1.0,
        description="""Float that controls the cumulative probability of the top tokens
            to consider. Must be in (0, 1]. Set to 1 to consider all tokens.""",
    )
    top_k: int = pydantic.Field(
        default=-1,
        description="""Integer that controls the number of top tokens to consider. Set
            to -1 to consider all tokens.""",
    )
    use_beam_search: bool = pydantic.Field(
        default=False, description="""Whether to use beam search instead of sampling."""
    )
    length_penalty: float = pydantic.Field(
        default=1.0,
        description="""Float that penalizes sequences based on their length.
            Used in beam search.""",
    )
    early_stopping: Union[bool, str] = pydantic.Field(
        default=False,
        description="""Controls the stopping condition for beam search. It
            accepts the following values: `True`, where the generation stops as
            soon as there are `best_of` complete candidates; `False`, where an
            heuristic is applied and the generation stops when is it very
            unlikely to find better candidates; `"never"`, where the beam search
            procedure only stops when there cannot be better candidates
            (canonical beam search algorithm).""",
    )
    stop: list[str] = pydantic.Field(
        default_factory=list,
        description="""List of strings that stop the generation when they are generated.
            The returned output will not contain the stop strings.""",
    )
    stop_token_ids: list[int] = pydantic.Field(
        default_factory=list,
        description="""List of tokens that stop the generation when they are
            generated. The returned output will contain the stop tokens unless
            the stop tokens are sepcial tokens.""",
    )
    ignore_eos: bool = pydantic.Field(
        default=False,
        description="""Whether to ignore the EOS token and continue generating
            tokens after the EOS token is generated.""",
    )
    max_tokens: int = pydantic.Field(
        default=16,
        description="""Maximum number of tokens to generate per output sequence.""",
    )
    logprobs: Optional[int] = pydantic.Field(
        default=None,
        description="""Number of log probabilities to return per output token.
            Note that the implementation follows the OpenAI API: The return
            result includes the log probabilities on the `logprobs` most likely
            tokens, as well the chosen tokens. The API will always return the
            log probability of the sampled token, so there  may be up to
            `logprobs+1` elements in the response.""",
    )
    prompt_logprobs: Optional[int] = pydantic.Field(
        default=None,
        description="""Number of log probabilities to return per prompt token.""",
    )
    skip_special_tokens: bool = pydantic.Field(
        default=True, description="""Whether to skip special tokens in the output."""
    )


class Prompt(DyffSchemaBaseModel):
    prompt: str = pydantic.Field(description="The text prompt for the LLM")


class GenerateEndpointInput(Prompt, InferenceParameters):
    pass


class GenerateEndpointOutput(DyffSchemaBaseModel):
    text: list[str] = pydantic.Field(
        # TODO: hypothesis plugin doesn't respect constraints
        # See: https://github.com/pydantic/pydantic/issues/2875
        # min_length=1,
        description="List of generated responses. The prompt is prepended to each response.",
    )
