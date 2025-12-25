import whatap.net.async_sender as async_sender
import whatap.io as whatapio
from whatap.pack import tagCountPack
from whatap.pack.tagCountPack import TagCountPack
from whatap.util.hash_util import HashUtil
from whatap import DateUtil

import os
import time
from typing import List, Dict, Tuple
from collections import defaultdict

currentpid = os.getpid()


class LLMStatTask:
    def __init__(self):
        self.llm_stats = {
            'model_calls': defaultdict(int),
            'model_prompt_tokens': defaultdict(int),
            'model_completion_tokens': defaultdict(int)
        }

    def name(self):
        return "LLMStatTask"

    def interval(self):
        from whatap.conf.configure import Configure as conf
        return int(getattr(conf, 'llm_stat_interval', 5))

    def process(self):
        from whatap.conf.configure import Configure as conf
        enabled = getattr(conf, 'llm_stat_enabled', False)
        if not enabled:
            return

        stats = self.get_current_stats()

        if not stats['model_calls']:
            return

        try:
            p = TagCountPack()
            p.time = DateUtil.now() // 1000 * 1000
            p.Category = "llm_stat"
            p.tags.putAuto("pid", currentpid)
            p.tags.putAuto("!rectype", 2)

            model_id_list = p.fields.newList("@id")
            model_name_list = p.fields.newList("model_name")
            call_count_list = p.fields.newList("call_count")
            prompt_tokens_list = p.fields.newList("prompt_tokens")
            completion_tokens_list = p.fields.newList("completion_tokens")
            total_tokens_list = p.fields.newList("total_tokens")

            for model_name, count in stats['model_calls'].items():
                prompt_tokens = stats['model_prompt_tokens'][model_name]
                completion_tokens = stats['model_completion_tokens'][model_name]
                total_tokens = prompt_tokens + completion_tokens

                model_id_list.addLong(HashUtil.hashFromString(model_name))
                model_name_list.addString(model_name)
                call_count_list.addLong(count)
                prompt_tokens_list.addLong(prompt_tokens)
                completion_tokens_list.addLong(completion_tokens)
                total_tokens_list.addLong(total_tokens)


            p.pcode = getattr(conf, 'PCODE', 0)
            bout = whatapio.DataOutputX()
            bout.writePack(p, None)
            packbytes = bout.toByteArray()

            async_sender.send_relaypack(packbytes)
            self.reset_stats()

        except Exception as e:
            import traceback
            traceback.print_exc()


    def get_current_stats(self) -> Dict:
        return {
            'model_calls': dict(self.llm_stats['model_calls']),
            'model_prompt_tokens': dict(self.llm_stats['model_prompt_tokens']),
            'model_completion_tokens': dict(self.llm_stats['model_completion_tokens'])
        }

    def prepare_model_data(self, model_calls: Dict[str, int]) -> Tuple[List[str], List[int]]:
        if not model_calls:
            return [], []

        models = list(model_calls.keys())
        call_count = [model_calls[model] for model in models]

        return models, call_count

    def update_stats(self, prompt_tokens: int, completion_tokens: int,
                     model_name: str):
        self.llm_stats['model_calls'][model_name] += 1
        self.llm_stats['model_prompt_tokens'][model_name] += prompt_tokens
        self.llm_stats['model_completion_tokens'][model_name] += completion_tokens



    def reset_stats(self):
        self.llm_stats = {
            'model_calls': defaultdict(int),
            'model_prompt_tokens': defaultdict(int),
            'model_completion_tokens': defaultdict(int)
        }