import re
import math
from typing import Optional

from lazyllm import launchers, finetune, LazyLLMLaunchersBase, LOG, config

from ..finetune.base import LazyLLMFinetuneBase
from .dependencies.requirements import requirements
from .auto_helper import get_model_name, check_requirements
from ..utils.downloader import ModelManager


def estimate_finetune_plan(gpu_mem_gb: float = 80.0, model_size_b: float = 30.0,
                           batch_size: int = 32, lora_r: int = 8):
    model_mem_gb = model_size_b * 2.0 * (1 + 0.2)  # model + lora + modules_to_save
    overhead_gb = gpu_mem_gb * 0.1

    gpus_for_weights = max(1, math.ceil(model_mem_gb / max(1e-6, (gpu_mem_gb - overhead_gb))))
    activ_per_gpu = max(0.5, gpu_mem_gb - overhead_gb - model_mem_gb / gpus_for_weights)
    activ_per_sample = max(0.5, model_size_b * 0.03) * (1.0 + (lora_r - 8) * 0.01)

    micro_batch_per_gpu = min(max(1, int(activ_per_gpu // activ_per_sample)), batch_size)

    effective_batch = micro_batch_per_gpu * gpus_for_weights
    gradient_step = max(1, math.ceil(batch_size / max(1, effective_batch)))

    return gradient_step, micro_batch_per_gpu, gpus_for_weights


class AutoFinetune(LazyLLMFinetuneBase):
    """This class is a subclass of ``LazyLLMFinetuneBase`` and can automatically select the appropriate fine-tuning framework and parameters based on the input arguments to fine-tune large language models.

Specifically, based on the input model parameters of ``base_model``, ``ctx_len``, ``batch_size``, ``lora_r``, the type and number of GPUs in ``launcher``, this class can automatically select the appropriate fine-tuning framework (such as: ``AlpacaloraFinetune`` or ``CollieFinetune``) and the required parameters.

Args:
    base_model (str): The base model used for fine-tuning. It is required to be the path of the base model.
    source (lazyllm.config['model_source']): Specifies the model download source. This can be configured by setting the environment variable ``LAZYLLM_MODEL_SOURCE``.
    target_path (str): The path where the LoRA weights of the fine-tuned model are saved.
    merge_path (str): The path where the model merges the LoRA weights, default to ``None``. If not specified, "lazyllm_lora" and "lazyllm_merge" directories will be created under ``target_path`` as ``target_path`` and ``merge_path`` respectively.
    ctx_len (int): The maximum token length for input to the fine-tuned model, default to ``1024``.
    batch_size (int): Batch size, default to ``32``.
    lora_r (int): LoRA rank, default to ``8``; this value determines the amount of parameters added, the smaller the value, the fewer the parameters.
    launcher (lazyllm.launcher): The launcher for fine-tuning, default to ``launchers.remote(ngpus=1)``.
    kw: Keyword arguments, used to update the default training parameters. Note that additional keyword arguments cannot be arbitrarily specified, as they depend on the framework inferred by LazyLLM, so it is recommended to set them with caution.


Examples:
    >>> from lazyllm import finetune
    >>> finetune.auto("internlm2-chat-7b", 'path/to/target')
    <lazyllm.llm.finetune type=AlpacaloraFinetune>
    """

    def __new__(cls, base_model: str, target_path: str, source: Optional[str] = None,
                merge_path: Optional[str] = None, batch_size: int = 32, lora_r: int = 8,
                model_type: Optional[str] = None, launcher: Optional[LazyLLMLaunchersBase] = None, **kw):
        base_model = ModelManager(source).download(base_model) or ''
        LOG.info(f'[AutoFinetune] Using base model from: {base_model}')
        model_name = get_model_name(base_model)
        if not model_type:
            model_type = ModelManager.get_model_type(model_name)
            LOG.info(f'[AutoFinetune] Infer type of model {model_name} is {model_type}')
        if model_type in ['tts', 'stt', 'sd', 'ocr', 'cross_modal_embed']:
            raise RuntimeError(f'Fine-tuning of the {model_type} model is not currently supported.')

        if model_type in ['embed', 'rerank']:
            LOG.info(f'[AutoFinetune] Finetune {model_name} with FlagEmbedding.')
            return finetune.flagembedding(base_model, target_path, **kw)

        params = {'gradient_step': 1, 'micro_batch_size': 32}
        if not launcher:
            match = re.search(r'(\d+)[bB]', model_name)
            model_size = int(match.group(1)) if match else 0
            gs, mbs, ngpus = estimate_finetune_plan(
                gpu_mem_gb=config['gpu_memory'], model_size_b=model_size, batch_size=batch_size, lora_r=lora_r)
            params.update({'gradient_step': gs, 'micro_batch_size': mbs})
            LOG.info(f'[AutoFinetune] Infer model_size: {model_size} B, '
                     f'gradient_step: {gs}, micro_batch_size: {mbs}, ngpus: {ngpus}')
            launcher = launchers.remote(ngpus=ngpus, sync=True)

        candidates = ['llamafactory', 'alpacalora']
        candidates = dict(llm=['llamafactory', 'alpacalora'], vlm=['llamafactory'])
        for finetune_cls_name in candidates[model_type]:
            if check_requirements(requirements[finetune_cls_name]):
                finetune_cls = getattr(finetune, finetune_cls_name)
                for key, value in finetune_cls.auto_map.items():
                    if value:
                        kw[value] = params[key]
                LOG.info(f'[AutoFinetune] Use {finetune_cls_name} to finetune.')
                if finetune_cls_name == 'llamafactory':
                    return finetune_cls(base_model, target_path, lora_r=lora_r, launcher=launcher, **kw)
                return finetune_cls(base_model, target_path, merge_path, cp_files='tokeniz*',
                                    batch_size=batch_size, lora_r=lora_r, launcher=launcher, **kw)
        raise RuntimeError('No valid framework found, candidates are '
                           f'{[c.framework.lower() for c in candidates[model_type]]}.')
