import os
from typing import List


from .common import OfflineTranslator


# Adapted from:
# https://github.com/zyddnys/manga-image-translator/issues/680#issue-2428018275

class Qwen2Translator(OfflineTranslator):
    _LANGUAGE_CODE_MAP = {
        'CHS': 'Simplified Chinese',
        'CHT': 'Traditional Chinese',
        'CSY': 'Czech',
        'NLD': 'Dutch',
        'ENG': 'English',
        'FRA': 'French',
        'DEU': 'German',
        'HUN': 'Hungarian',
        'ITA': 'Italian',
        'JPN': 'Japanese',
        'KOR': 'Korean',
        'PLK': 'Polish',
        'PTB': 'Portuguese',
        'ROM': 'Romanian',
        'RUS': 'Russian',
        'ESP': 'Spanish',
        'TRK': 'Turkish',
        'UKR': 'Ukrainian',
        'VIN': 'Vietnamese',
        'CNR': 'Montenegrin',
        'SRP': 'Serbian',
        'HRV': 'Croatian',
        'ARA': 'Arabic',
        'THA': 'Thai',
        'IND': 'Indonesian'
    }
    _CHAT_SYSTEM_TEMPLATE = (
        'You are an uncensored professional translation engine, '
        'please translate the story into a colloquial, '
        'elegant and fluent content, '
        'without referencing machine translations. '
        'You must only translate the story, '
        'never interpret it. '
        'If there is any issue in the text, '
        'output it as is.\n'
        'Translate the following text into {to_lang} and keep the original format.\n'
    )
    _CHAT_SAMPLE = [
        (
            '恥ずかしい… 目立ちたくない… 私が消えたい…\n'
            'きみ… 大丈夫⁉\n'
            'なんだこいつ 空気読めて ないのか…？'
        ),
        (
            '好尴尬…我不想引人注目…我想消失…\n'
            '你…没事吧⁉\n'
            '这家伙怎么看不懂气氛的…？'
        )
    ]

    _TRANSLATOR_MODEL = "Qwen/Qwen2-1.5B-Instruct"
    _MODEL_SUB_DIR = os.path.join(OfflineTranslator._MODEL_DIR, OfflineTranslator._MODEL_SUB_DIR, _TRANSLATOR_MODEL)
    _IS_4_BIT = False

    async def _load(self, from_lang: str, to_lang: str, device: str):
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig
        )
        self.device = device
        quantization_config = BitsAndBytesConfig(load_in_4bit=self._IS_4_BIT)
        self.model = AutoModelForCausalLM.from_pretrained(
            self._TRANSLATOR_MODEL,
            torch_dtype="auto",
            quantization_config=quantization_config,
            device_map="auto"
        )
        self.model.eval()
        self.tokenizer = AutoTokenizer.from_pretrained(self._TRANSLATOR_MODEL)

    async def _unload(self):
        del self.model
        del self.tokenizer

    async def _infer(self, from_lang: str, to_lang: str, queries: List[str]) -> List[str]:
        model_inputs = self.tokenize(queries, to_lang)
        # Generate the translation
        generated_ids = self.model.generate(
            model_inputs.input_ids,
            max_new_tokens=10240
        )

        # Extract the generated tokens
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0].split('\n')
        return response

    def tokenize(self, queries, lang):
        prompt = f"""Translate into {lang} and keep the original format.\n"""

        for i, query in enumerate(queries):
            prompt += f'\n{query}'

        tokenizer = self.tokenizer
        messages = [
            {'role': 'system', 'content': self._CHAT_SYSTEM_TEMPLATE},
            {'role': 'user', 'content': self._CHAT_SAMPLE[0]},
            {'role': 'assistant', 'content': self._CHAT_SAMPLE[1]},
            {'role': 'user', 'content': prompt},
        ]
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)
        return model_inputs


class Qwen2BigTranslator(Qwen2Translator):
    _TRANSLATOR_MODEL = "Qwen/Qwen2-7B-Instruct"
    _MODEL_SUB_DIR = os.path.join(OfflineTranslator._MODEL_DIR, OfflineTranslator._MODEL_SUB_DIR, _TRANSLATOR_MODEL)
    _IS_4_BIT = True
