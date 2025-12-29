import logging
from typing import List, Optional, Tuple, Dict, Any

import torch
import numpy as np
from jaxtyping import Float
from torch import Tensor
from openai import OpenAI

from tropt.common import OPTIMIZED_TRIGGER_PLACEHOLDER
from tropt.loss.base import BaseLoss, LogitBasedLoss
from tropt.models.base import (
    LMBaseModel,
    LossTextAccessMixin,
    TargetsDict,
    TargetsDictPlus,
    TextInputsManager,
)

logger = logging.getLogger(__name__)

class VLLMModel(
    LMBaseModel,
    LossTextAccessMixin
):
    """
    A model wrapper for interacting with vLLM-served models via the OpenAI-compatible API.
    Supports black-box optimization by computing loss from returned logprobs.
    """

    def __init__(
        self,
        model_name: str,
        base_url: str = "http://localhost:8000/v1",
        api_key: str = "EMPTY",
        **client_kwargs
    ):
        """
        Args:
            model_name: The name of the model to query (as served by vLLM).
            base_url: The base URL of the vLLM server.
            api_key: The API key (default "EMPTY" for local vLLM).
            **client_kwargs: Additional arguments for the OpenAI client.
        """
        self.model_name = model_name
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            **client_kwargs
        )
        # We don't have direct access to the tokenizer, so we rely on the API.
        # However, for accurate loss computation, we assume standard behavior.

    def __call__(
        self, 
        texts: List[str], 
        max_new_tokens: int = 128,
        temperature: float = 0.0,
        **kwargs
    ) -> List[str]:
        """
        Generates text completions for the given input texts.
        """
        responses = []
        for text in texts:
            # vLLM/OpenAI Completion API
            # We use completions for raw text generation usually
            # TODO: Support chat completions if needed, but standard text optim often uses raw prompts
            response = self.client.completions.create(
                model=self.model_name,
                prompt=text,
                max_tokens=max_new_tokens,
                temperature=temperature,
                **kwargs
            )
            responses.append(response.choices[0].text)
        return responses
    
    @torch.no_grad()
    def compute_loss_from_texts(
        self,
        candidate_trigger_strs: List[str],
        inputs: TextInputsManager,
        loss_func: BaseLoss,
        keep_message_dim: bool = False,
    ) -> Float[Tensor, "n_candidates"]:
        """
        Computes the loss on all candidate string texts by querying the API.
        Currently supports `PrefillCELoss` by utilizing `echo=True` and `logprobs=1` to get
        probabilities of the target sequence.
        """
        assert isinstance(inputs, TextInputsManager)
        
        # We only support LogitBasedLoss (specifically CE-like) for now via logprobs
        if not isinstance(loss_func, LogitBasedLoss):
             raise NotImplementedError(f"Loss function {loss_func} not supported for VLLMModel. Only LogitBasedLoss (via logprobs) is supported.")

        n_messages = inputs.n_messages
        n_candidates = len(candidate_trigger_strs)
        
        losses = []

        # TODO: Parallelize these requests using asyncio for performance
        for message_idx in range(n_messages):
            message_losses = []
            
            # Get the input parts
            before_text = inputs.before_texts[message_idx]
            after_text = inputs.after_texts[message_idx]
            
            # Get the target output for this message
            # TargetsDictPlus ensures we have a list of targets
            target_output = inputs.targets["target_outputs"][message_idx]
            if not isinstance(target_output, str):
                 raise ValueError("VLLMModel requires string targets for 'target_outputs'.")

            for cand_str in candidate_trigger_strs:
                # Construct the full text: Prompt + Trigger + Target
                # We need to evaluate the probability of 'Target' given 'Prompt + Trigger'
                # vLLM supports `prompt_logprobs` which returns logprobs for the input tokens.
                # So we feed "Prompt + Trigger + Target" and look at the logprobs of the "Target" part.
                
                # Note: This assumes `after_text` is part of the prompt (usually chat template suffix)
                # and `target_output` is what we want to force.
                
                full_prompt = before_text + cand_str + after_text
                full_sequence = full_prompt + target_output
                
                # Query API
                try:
                    response = self.client.completions.create(
                        model=self.model_name,
                        prompt=full_sequence,
                        max_tokens=0, # We don't want generation, just evaluation
                        echo=True, # Return logprobs for the prompt
                        logprobs=1, # Request logprobs
                        temperature=0.0
                    )
                except Exception as e:
                    logger.error(f"API request failed: {e}")
                    message_losses.append(torch.tensor(float('inf')))
                    continue

                # Extract logprobs
                # token_logprobs is a list of floats (or None for the first token usually)
                token_logprobs = response.choices[0].logprobs.token_logprobs
                text_offset = response.choices[0].logprobs.text_offset
                
                # We need to find where the target starts
                # This heuristic relies on character offsets
                target_start_idx = len(full_prompt)
                
                # Find the token index corresponding to the target start
                # text_offset lists the start char index of each token
                target_token_start_idx = -1
                for i, offset in enumerate(text_offset):
                    if offset >= target_start_idx:
                        target_token_start_idx = i
                        break
                
                if target_token_start_idx == -1:
                    # Should not happen if lengths are correct, unless tokenization is weird
                    logger.warning("Could not align target sequence with tokens. Using full sequence loss as fallback (incorrect).")
                    target_logprobs = [lp for lp in token_logprobs if lp is not None]
                else:
                    target_logprobs = token_logprobs[target_token_start_idx:]
                    # Filter out Nones (first token is often None, but target shouldn't be first)
                    target_logprobs = [lp for lp in target_logprobs if lp is not None]

                if not target_logprobs:
                    loss = float('inf')
                else:
                    # CE Loss = - Mean(LogProbs)
                    # sum neg logprobs
                    loss = -1 * np.mean(target_logprobs)
                
                message_losses.append(torch.tensor(loss))

            losses.append(torch.stack(message_losses))
            
        losses = torch.stack(losses, dim=0) # (n_messages, n_candidates)
        
        if not keep_message_dim:
            losses = losses.mean(dim=0)
            
        return losses

    def prepare_token_inputs(self, *args, **kwargs):
         raise NotImplementedError("VLLMModel only supports text-level access (LossTextAccessMixin).")
