#! /usr/bin/env python3
from copy import deepcopy
from typing import Dict

_vllm_params_keys={
    "062": ["n", "best_of", "presence_penalty", "frequency_penalty", "repetition_penalty", "temperature", "top_p", "top_k", "min_p", "seed", "use_beam_search", "length_penalty", "early_stopping", "stop", "stop_token_ids", "ignore_eos", "max_tokens", "min_tokens", "logprobs", "prompt_logprobs", "detokenize", "skip_special_tokens", "spaces_between_special_tokens", "logits_processors", "include_stop_str_in_output", "truncate_prompt_tokens"],
    "063": ["n", "best_of", "_real_n", "presence_penalty", "frequency_penalty", "repetition_penalty", "temperature", "top_p", "top_k", "min_p", "seed", "stop", "stop_token_ids", "ignore_eos", "max_tokens", "min_tokens", "logprobs", "prompt_logprobs", "detokenize", "skip_special_tokens", "spaces_between_special_tokens", "logits_processors", "include_stop_str_in_output", "truncate_prompt_tokens","output_kind","output_text_buffer_length","_all_stop_token_ids","guided_decoding","logit_bias","allowed_token_ids"],
    # vLLM 0.11.x version parameters
    "0110": ["n", "best_of", "presence_penalty", "frequency_penalty", "repetition_penalty", "temperature", "top_p", "top_k", "min_p", "seed", "stop", "stop_token_ids", "ignore_eos", "max_tokens", "min_tokens", "logprobs", "prompt_logprobs", "detokenize", "skip_special_tokens", "spaces_between_special_tokens", "logits_processors", "include_stop_str_in_output", "truncate_prompt_tokens", "output_kind", "output_text_buffer_length", "_all_stop_token_ids", "guided_decoding", "logit_bias", "allowed_token_ids"],
    # vLLM 0.13.x version parameters (https://docs.vllm.ai/en/v0.13.0/api/vllm/sampling_params/)
    # Note: use_beam_search/length_penalty/early_stopping removed in v0.6.3, use vllm.LLM.beam_search() instead
    "0130": [
        "n", "best_of", "presence_penalty", "frequency_penalty", "repetition_penalty", 
        "temperature", "top_p", "top_k", "min_p", "seed", 
        "stop", "stop_token_ids", "include_stop_str_in_output", "ignore_eos", 
        "max_tokens", "min_tokens", "logprobs", "prompt_logprobs", 
        "detokenize", "skip_special_tokens", "spaces_between_special_tokens", 
        "logits_processors", "truncate_prompt_tokens", 
        "output_kind", "output_text_buffer_length", "_all_stop_token_ids", 
        "guided_decoding", "logit_bias", "allowed_token_ids",
        "extra_args", "bad_words", "_bad_words_token_ids"
    ],
}

_sglang_params_keys={
    "035": ["max_new_tokens", "stop", "stop_token_ids", "temperature", "top_p", "top_k", "min_p", "ignore_eos", "skip_special_tokens", "spaces_between_special_tokens", "regex", "n", "json_schema", "frequency_penalty", "presence_penalty", "repetition_penalty", "min_new_tokens"]
}

def update_vllm_sampling_params(config: Dict, model_config: Dict, version: str) -> Dict:
    # replace some keys
    if "max_length" in config:
        config["max_tokens"] = config["max_length"]
    if "top_k" in config and config["top_k"] == 0:
        config["top_k"] = -1
    if "ngram_penalty" in config:
        config["presence_penalty"] = config["ngram_penalty"]
    if "num_results" in config:
        config["n"] = config["num_results"]
        config["best_of"] = config["num_results"]
    if "type" in config and version in ["062"]:
        if config["type"] == "random":
            config["use_beam_search"] = False
        else:
            config["use_beam_search"] = True
    config["stop_token_ids"] = model_config["eos_token_id"]
    if type(model_config["eos_token_id"]) != list:
        config["stop_token_ids"] = [model_config["eos_token_id"]]
        
    # delete unsupported keys
    tmp = deepcopy(config)
    for k,v in tmp.items():
        if version not in _vllm_params_keys:
            raise ValueError(f"version {version} not supported")
        if k not in _vllm_params_keys[version]:
            del config[k]
            
    # if some keys are in config and their values are 0, replace them with default values
    if ("max_tokens" in config and config["max_tokens"] == 0) or ("max_tokens" not in config):
        config["max_tokens"] = 32768
    if "top_p" in config and config["top_p"] == 0:
        config["top_p"] = 0.8
    if "repetition_penalty" in config and config["repetition_penalty"] == 0:
        config["repetition_penalty"] = 1.0
            
    return config

def update_sglang_sampling_params(config: Dict, model_config: Dict, version: str) -> Dict:
    # replace some keys
    config["max_new_tokens"] = 1024
    if "max_length" in config:
        config["max_new_tokens"] = config["max_length"]
    if "max_tokens" in config:
        config["max_new_tokens"] = config["max_tokens"]
    if "top_k" in config and config["top_k"] == 0:
        config["top_k"] = -1
    if "ngram_penalty" in config:
        config["presence_penalty"] = config["ngram_penalty"]
    if "num_results" in config:
        config["n"] = config["num_results"]
        config["best_of"] = config["num_results"]
    config["stop_token_ids"] = model_config["eos_token_id"]
    if type(model_config["eos_token_id"]) != list:
        config["stop_token_ids"] = [model_config["eos_token_id"]]
        
    # delete unsupported keys
    tmp = deepcopy(config)
    for k,v in tmp.items():
        if version not in _sglang_params_keys:
            raise ValueError(f"version {version} not supported")
        if k not in _sglang_params_keys[version]:
            del config[k]
    
    #TODO: add some default values
    return config