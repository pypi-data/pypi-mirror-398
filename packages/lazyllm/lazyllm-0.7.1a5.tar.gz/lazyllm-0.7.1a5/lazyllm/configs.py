import os
from enum import Enum
import json
from typing import List, Union, Optional
from contextlib import contextmanager
import logging


class Mode(Enum):
    """An enumeration."""
    Display = 0,
    Normal = 1,
    Debug = 2,


class _MetaDoc(type):
    """<property object at 0x7fd673aeade0>"""
    _description = dict()
    _doc = ''

    @staticmethod
    def _get_description(name):
        desc = _MetaDoc._description[name]
        if not desc: raise ValueError(f'Description for {name} is not found')
        doc = (f'  - Description: {desc["description"]}, type: `{desc["type"]}`, default: `{desc["default"]}`<br>\n')
        if (options := desc.get('options')):
            doc += f'  - Options: {", ".join(options)}<br>\n'
        if (env := desc.get('env')):
            if isinstance(env, str):
                doc += f'  - Environment Variable: {("LAZYLLM_" + env).upper()}<br>\n'
            elif isinstance(env, dict):
                doc += '  - Environment Variable:<br>\n'
                for k, v in env.items():
                    doc += f'{("    - LAZYLLM_" + k).upper()}: {v}<br>\n'
        return doc

    @property
    def __doc__(self):
        doc = f'{self._doc}\n**LazyLLM Configurations:**\n\n'
        return doc + '<br>\n'.join([f'- **{name}**:<br>\n{self._get_description(name)}'
                                    for name in self._description.keys()])

    @__doc__.setter
    def __doc__(self, value):
        self._doc = value


class Config(metaclass=_MetaDoc):
    """Config is a configuration class provided by LazyLLM, which loads configurations of LazyLLM framework from config files,
environment variables, or specify them explicitly. it can export all configuration items as well.
The Config module automatically generates an object named 'config' containing all configurations.

Args:
    prefix (str, optional): Environment variable prefix. Defaults to 'LAZYLLM'
    home (str, optional): Configuration file directory path. Defaults to '~/.lazyllm'

**LazyLLM Configurations:**

- **home**:<br>
  - Description: The default home directory for LazyLLM., type: `str`, default: `/home/runner/.lazyllm`<br>
  - Environment Variable: LAZYLLM_HOME<br>
<br>
- **mode**:<br>
  - Description: The default mode for LazyLLM., type: `Mode`, default: `Mode.Normal`<br>
  - Environment Variable:<br>
    - LAZYLLM_DISPLAY: Mode.Display<br>
    - LAZYLLM_DEBUG: Mode.Debug<br>
<br>
- **repr_ml**:<br>
  - Description: Whether to use Markup Language for repr., type: `bool`, default: `False`<br>
  - Environment Variable: LAZYLLM_REPR_USE_ML<br>
<br>
- **repr_show_child**:<br>
  - Description: Whether to show child modules in repr., type: `bool`, default: `False`<br>
  - Environment Variable: LAZYLLM_REPR_SHOW_CHILD<br>
<br>
- **rag_store**:<br>
  - Description: The default store for RAG., type: `str`, default: `none`<br>
  - Environment Variable: LAZYLLM_RAG_STORE<br>
<br>
- **gpu_type**:<br>
  - Description: The default GPU type for LazyLLM., type: `str`, default: `A100`<br>
  - Environment Variable: LAZYLLM_GPU_TYPE<br>
<br>
- **train_target_root**:<br>
  - Description: The default target root for training., type: `str`, default: `/home/runner/work/LazyLLM/LazyLLM/save_ckpt`<br>
  - Environment Variable: LAZYLLM_TRAIN_TARGET_ROOT<br>
<br>
- **infer_log_root**:<br>
  - Description: The default log root for inference., type: `str`, default: `/home/runner/work/LazyLLM/LazyLLM/infer_log`<br>
  - Environment Variable: LAZYLLM_INFER_LOG_ROOT<br>
<br>
- **temp_dir**:<br>
  - Description: The default temp directory for LazyLLM., type: `str`, default: `/home/runner/work/LazyLLM/LazyLLM/.temp`<br>
  - Environment Variable: LAZYLLM_TEMP_DIR<br>
<br>
- **thread_pool_worker_num**:<br>
  - Description: The default number of workers for thread pool., type: `int`, default: `16`<br>
  - Environment Variable: LAZYLLM_THREAD_POOL_WORKER_NUM<br>
<br>
- **deploy_skip_check_kw**:<br>
  - Description: Whether to skip check keywords for deployment., type: `bool`, default: `False`<br>
  - Environment Variable: LAZYLLM_DEPLOY_SKIP_CHECK_KW<br>
<br>
- **debug**:<br>
  - Description: Whether to enable debug mode., type: `bool`, default: `False`<br>
  - Environment Variable: LAZYLLM_DEBUG<br>
<br>
- **log_name**:<br>
  - Description: The name of the log file., type: `str`, default: `lazyllm`<br>
  - Environment Variable: LAZYLLM_LOG_NAME<br>
<br>
- **expected_log_modules**:<br>
  - Description: The expected log modules, separated by comma., type: `str`, default: `lazyllm`<br>
  - Environment Variable: LAZYLLM_EXPECTED_LOG_MODULES<br>
<br>
- **log_level**:<br>
  - Description: The level of the log., type: `str`, default: `INFO`<br>
  - Environment Variable: LAZYLLM_LOG_LEVEL<br>
<br>
- **log_format**:<br>
  - Description: The format of the log., type: `str`, default: `long`<br>
  - Environment Variable: LAZYLLM_LOG_FORMAT<br>
<br>
- **log_dir**:<br>
  - Description: The directory of the log file., type: `str`, default: `/home/runner/.lazyllm/logs`<br>
  - Environment Variable: LAZYLLM_LOG_DIR<br>
<br>
- **log_file_level**:<br>
  - Description: The level of the log file., type: `str`, default: `ERROR`<br>
  - Environment Variable: LAZYLLM_LOG_FILE_LEVEL<br>
<br>
- **log_file_size**:<br>
  - Description: The size of the log file., type: `str`, default: `4 MB`<br>
  - Environment Variable: LAZYLLM_LOG_FILE_SIZE<br>
<br>
- **log_file_retention**:<br>
  - Description: The retention of the log file., type: `str`, default: `7 days`<br>
  - Environment Variable: LAZYLLM_LOG_FILE_RETENTION<br>
<br>
- **log_file_mode**:<br>
  - Description: The mode of the log file., type: `str`, default: `merge`<br>
  - Environment Variable: LAZYLLM_LOG_FILE_MODE<br>
<br>
- **redis_url**:<br>
  - Description: The URL of the Redis server., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_REDIS_URL<br>
<br>
- **redis_recheck_delay**:<br>
  - Description: The delay of the Redis server check., type: `int`, default: `5`<br>
  - Environment Variable: LAZYLLM_REDIS_RECHECK_DELAY<br>
<br>
- **use_builtin**:<br>
  - Description: Whether to use registry modules in python builtin., type: `bool`, default: `False`<br>
  - Environment Variable: LAZYLLM_USE_BUILTIN<br>
<br>
- **default_fsqueue**:<br>
  - Description: The default file system queue to use., type: `str`, default: `sqlite`<br>
  - Environment Variable: LAZYLLM_DEFAULT_FSQUEUE<br>
<br>
- **fsqredis_url**:<br>
  - Description: The URL of the Redis server for the file system queue., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_FSQREDIS_URL<br>
<br>
- **default_recent_k**:<br>
  - Description: The number of recent inputs that RecentQueue keeps track of., type: `int`, default: `0`<br>
  - Environment Variable: LAZYLLM_DEFAULT_RECENT_K<br>
<br>
- **launcher**:<br>
  - Description: The default remote launcher to use if no launcher is specified., type: `str`, default: `empty`<br>
  - Environment Variable: LAZYLLM_DEFAULT_LAUNCHER<br>
<br>
- **cuda_visible**:<br>
  - Description: Whether to set the CUDA_VISIBLE_DEVICES environment variable., type: `bool`, default: `False`<br>
  - Environment Variable: LAZYLLM_CUDA_VISIBLE<br>
<br>
- **partition**:<br>
  - Description: The default Slurm partition to use if no partition is specified., type: `str`, default: `your_part`<br>
  - Environment Variable: LAZYLLM_SLURM_PART<br>
<br>
- **sco.workspace**:<br>
  - Description: The default SCO workspace to use if no workspace is specified., type: `str`, default: `your_workspace`<br>
  - Environment Variable: LAZYLLM_SCO_WORKSPACE<br>
<br>
- **sco_env_name**:<br>
  - Description: The default SCO environment name to use if no environment name is specified., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_SCO_ENV_NAME<br>
<br>
- **sco_keep_record**:<br>
  - Description: Whether to keep the record of the Sensecore job., type: `bool`, default: `False`<br>
  - Environment Variable: LAZYLLM_SCO_KEEP_RECORD<br>
<br>
- **sco_resource_type**:<br>
  - Description: The default SCO resource type to use if no resource type is specified., type: `str`, default: `N3lS.Ii.I60`<br>
  - Environment Variable: LAZYLLM_SCO_RESOURCE_TYPE<br>
<br>
- **k8s_env_name**:<br>
  - Description: The default k8s environment name to use if no environment name is specified., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_K8S_ENV_NAME<br>
<br>
- **k8s_config_path**:<br>
  - Description: The default k8s configuration path to use if no configuration path is specified., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_K8S_CONFIG_PATH<br>
<br>
- **k8s_device_type**:<br>
  - Description: The default k8s device type to use if no device type is specified., type: `str`, default: `nvidia.com/gpu`<br>
  - Environment Variable: LAZYLLM_K8S_DEVICE_TYPE<br>
<br>
- **save_flow_result**:<br>
  - Description: Whether to save the intermediate result of the pipeline., type: `bool`, default: `False`<br>
  - Environment Variable: LAZYLLM_SAVE_FLOW_RESULT<br>
<br>
- **parallel_multiprocessing**:<br>
  - Description: Whether to use multiprocessing for parallel execution, if not, default to use threading., type: `bool`, default: `False`<br>
  - Environment Variable: LAZYLLM_PARALLEL_MULTIPROCESSING<br>
<br>
- **model_source**:<br>
  - Description: The default model source to use., type: `str`, default: `modelscope`<br>
  - Environment Variable: LAZYLLM_MODEL_SOURCE<br>
<br>
- **model_cache_dir**:<br>
  - Description: The default model cache directory to use(Read and Write)., type: `str`, default: `/home/runner/.lazyllm/model`<br>
  - Environment Variable: LAZYLLM_MODEL_CACHE_DIR<br>
<br>
- **model_path**:<br>
  - Description: The default model path to use(ReadOnly)., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_MODEL_PATH<br>
<br>
- **model_source_token**:<br>
  - Description: The default token for configed model source(hf or ms) to use., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_MODEL_SOURCE_TOKEN<br>
<br>
- **data_path**:<br>
  - Description: The default data path to use., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_DATA_PATH<br>
<br>
- **openai_api**:<br>
  - Description: Whether to use OpenAI API for vllm deployer., type: `bool`, default: `False`<br>
  - Environment Variable: LAZYLLM_OPENAI_API<br>
<br>
- **use_ray**:<br>
  - Description: Whether to use Ray for ServerModule(relay server)., type: `bool`, default: `False`<br>
  - Environment Variable: LAZYLLM_USE_RAY<br>
<br>
- **num_gpus_per_node**:<br>
  - Description: The number of GPUs per node for Ray launcher when deploy models., type: `int`, default: `8`<br>
  - Environment Variable: LAZYLLM_NUM_GPUS_PER_NODE<br>
<br>
- **lmdeploy_eager_mode**:<br>
  - Description: Whether to use eager mode for lmdeploy., type: `bool`, default: `False`<br>
  - Environment Variable: LAZYLLM_LMDEPLOY_EAGER_MODE<br>
<br>
- **default_embedding_engine**:<br>
  - Description: The default embedding engine to use., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_DEFAULT_EMBEDDING_ENGINE<br>
<br>
- **mindie_home**:<br>
  - Description: The home directory of MindIE., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_MINDIE_HOME<br>
<br>
- **gpu_memory**:<br>
  - Description: The memory of the GPU., type: `int`, default: `80`<br>
  - Environment Variable: LAZYLLM_GPU_MEMORY<br>
<br>
- **cache_dir**:<br>
  - Description: The default result cache directory for module to use(Read and Write)., type: `str`, default: `/home/runner/.lazyllm/cache`<br>
  - Environment Variable: LAZYLLM_CACHE_DIR<br>
<br>
- **cache_strategy**:<br>
  - Description: The default cache strategy to use(memory, file, sqlite, redis)., type: `str`, default: `memory`<br>
  - Environment Variable: LAZYLLM_CACHE_STRATEGY<br>
<br>
- **cache_mode**:<br>
  - Description: The default cache mode to use(Read and Write, Read Only, Write Only, None)., type: `str`, default: `RW`<br>
  - Options: RW, RO, WO, NONE<br>
  - Environment Variable: LAZYLLM_CACHE_MODE<br>
<br>
- **trainable_module_config_map_path**:<br>
  - Description: The default path for trainable module config map., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_TRAINABLE_MODULE_CONFIG_MAP_PATH<br>
<br>
- **trainable_magic_mock**:<br>
  - Description: Whether to use magic mock for trainable module(used for unit test)., type: `bool`, default: `False`<br>
  - Environment Variable: LAZYLLM_TRAINABLE_MAGIC_MOCK<br>
<br>
- **cache_local_module**:<br>
  - Description: Whether to cache the local module result. Use for unit test., type: `bool`, default: `False`<br>
  - Environment Variable: LAZYLLM_CACHE_LOCAL_MODULE<br>
<br>
- **cache_online_module**:<br>
  - Description: Whether to cache the online module result. Use for unit test., type: `bool`, default: `False`<br>
  - Environment Variable: LAZYLLM_CACHE_ONLINE_MODULE<br>
<br>
- **openai_api_key**:<br>
  - Description: The API key for openai., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_OPENAI_API_KEY<br>
<br>
- **openai_model_name**:<br>
  - Description: The default model name for openai., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_OPENAI_MODEL_NAME<br>
<br>
- **openai_text2image_model_name**:<br>
  - Description: The default text2image model name for openai., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_OPENAI_TEXT2IMAGE_MODEL_NAME<br>
<br>
- **openai_tts_model_name**:<br>
  - Description: The default tts model name for openai., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_OPENAI_TTS_MODEL_NAME<br>
<br>
- **openai_stt_model_name**:<br>
  - Description: The default stt model name for openai., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_OPENAI_STT_MODEL_NAME<br>
<br>
- **sensenova_api_key**:<br>
  - Description: The API key for sensenova., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_SENSENOVA_API_KEY<br>
<br>
- **sensenova_model_name**:<br>
  - Description: The default model name for sensenova., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_SENSENOVA_MODEL_NAME<br>
<br>
- **sensenova_text2image_model_name**:<br>
  - Description: The default text2image model name for sensenova., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_SENSENOVA_TEXT2IMAGE_MODEL_NAME<br>
<br>
- **sensenova_tts_model_name**:<br>
  - Description: The default tts model name for sensenova., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_SENSENOVA_TTS_MODEL_NAME<br>
<br>
- **sensenova_stt_model_name**:<br>
  - Description: The default stt model name for sensenova., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_SENSENOVA_STT_MODEL_NAME<br>
<br>
- **glm_api_key**:<br>
  - Description: The API key for glm., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_GLM_API_KEY<br>
<br>
- **glm_model_name**:<br>
  - Description: The default model name for glm., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_GLM_MODEL_NAME<br>
<br>
- **glm_text2image_model_name**:<br>
  - Description: The default text2image model name for glm., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_GLM_TEXT2IMAGE_MODEL_NAME<br>
<br>
- **glm_tts_model_name**:<br>
  - Description: The default tts model name for glm., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_GLM_TTS_MODEL_NAME<br>
<br>
- **glm_stt_model_name**:<br>
  - Description: The default stt model name for glm., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_GLM_STT_MODEL_NAME<br>
<br>
- **kimi_api_key**:<br>
  - Description: The API key for kimi., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_KIMI_API_KEY<br>
<br>
- **kimi_model_name**:<br>
  - Description: The default model name for kimi., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_KIMI_MODEL_NAME<br>
<br>
- **kimi_text2image_model_name**:<br>
  - Description: The default text2image model name for kimi., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_KIMI_TEXT2IMAGE_MODEL_NAME<br>
<br>
- **kimi_tts_model_name**:<br>
  - Description: The default tts model name for kimi., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_KIMI_TTS_MODEL_NAME<br>
<br>
- **kimi_stt_model_name**:<br>
  - Description: The default stt model name for kimi., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_KIMI_STT_MODEL_NAME<br>
<br>
- **qwen_api_key**:<br>
  - Description: The API key for qwen., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_QWEN_API_KEY<br>
<br>
- **qwen_model_name**:<br>
  - Description: The default model name for qwen., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_QWEN_MODEL_NAME<br>
<br>
- **qwen_text2image_model_name**:<br>
  - Description: The default text2image model name for qwen., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_QWEN_TEXT2IMAGE_MODEL_NAME<br>
<br>
- **qwen_tts_model_name**:<br>
  - Description: The default tts model name for qwen., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_QWEN_TTS_MODEL_NAME<br>
<br>
- **qwen_stt_model_name**:<br>
  - Description: The default stt model name for qwen., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_QWEN_STT_MODEL_NAME<br>
<br>
- **doubao_api_key**:<br>
  - Description: The API key for doubao., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_DOUBAO_API_KEY<br>
<br>
- **doubao_model_name**:<br>
  - Description: The default model name for doubao., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_DOUBAO_MODEL_NAME<br>
<br>
- **doubao_text2image_model_name**:<br>
  - Description: The default text2image model name for doubao., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_DOUBAO_TEXT2IMAGE_MODEL_NAME<br>
<br>
- **doubao_tts_model_name**:<br>
  - Description: The default tts model name for doubao., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_DOUBAO_TTS_MODEL_NAME<br>
<br>
- **doubao_stt_model_name**:<br>
  - Description: The default stt model name for doubao., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_DOUBAO_STT_MODEL_NAME<br>
<br>
- **deepseek_api_key**:<br>
  - Description: The API key for deepseek., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_DEEPSEEK_API_KEY<br>
<br>
- **deepseek_model_name**:<br>
  - Description: The default model name for deepseek., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_DEEPSEEK_MODEL_NAME<br>
<br>
- **deepseek_text2image_model_name**:<br>
  - Description: The default text2image model name for deepseek., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_DEEPSEEK_TEXT2IMAGE_MODEL_NAME<br>
<br>
- **deepseek_tts_model_name**:<br>
  - Description: The default tts model name for deepseek., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_DEEPSEEK_TTS_MODEL_NAME<br>
<br>
- **deepseek_stt_model_name**:<br>
  - Description: The default stt model name for deepseek., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_DEEPSEEK_STT_MODEL_NAME<br>
<br>
- **siliconflow_api_key**:<br>
  - Description: The API key for siliconflow., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_SILICONFLOW_API_KEY<br>
<br>
- **siliconflow_model_name**:<br>
  - Description: The default model name for siliconflow., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_SILICONFLOW_MODEL_NAME<br>
<br>
- **siliconflow_text2image_model_name**:<br>
  - Description: The default text2image model name for siliconflow., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_SILICONFLOW_TEXT2IMAGE_MODEL_NAME<br>
<br>
- **siliconflow_tts_model_name**:<br>
  - Description: The default tts model name for siliconflow., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_SILICONFLOW_TTS_MODEL_NAME<br>
<br>
- **siliconflow_stt_model_name**:<br>
  - Description: The default stt model name for siliconflow., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_SILICONFLOW_STT_MODEL_NAME<br>
<br>
- **minimax_api_key**:<br>
  - Description: The API key for minimax., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_MINIMAX_API_KEY<br>
<br>
- **minimax_model_name**:<br>
  - Description: The default model name for minimax., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_MINIMAX_MODEL_NAME<br>
<br>
- **minimax_text2image_model_name**:<br>
  - Description: The default text2image model name for minimax., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_MINIMAX_TEXT2IMAGE_MODEL_NAME<br>
<br>
- **minimax_tts_model_name**:<br>
  - Description: The default tts model name for minimax., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_MINIMAX_TTS_MODEL_NAME<br>
<br>
- **minimax_stt_model_name**:<br>
  - Description: The default stt model name for minimax., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_MINIMAX_STT_MODEL_NAME<br>
<br>
- **sensenova_secret_key**:<br>
  - Description: The secret key for SenseNova., type: `str`, default: ``<br>
  - Environment Variable: LAZYLLM_SENSENOVA_SECRET_KEY<br>
<br>
- **max_embedding_workers**:<br>
  - Description: The default number of workers for embedding in RAG., type: `int`, default: `8`<br>
  - Environment Variable: LAZYLLM_MAX_EMBEDDING_WORKERS<br>
<br>
- **default_dlmanager**:<br>
  - Description: The default document list manager for RAG., type: `str`, default: `sqlite`<br>
  - Environment Variable: LAZYLLM_DEFAULT_DOCLIST_MANAGER<br>
<br>
- **paddleocr_api_key**:<br>
  - Description: The API key for PaddleOCR, type: `str`, default: `None`<br>
  - Environment Variable: LAZYLLM_PADDLEOCR_API_KEY<br>
<br>
- **rag_filename_as_id**:<br>
  - Description: Whether to use filename as id for RAG., type: `bool`, default: `False`<br>
  - Environment Variable: LAZYLLM_RAG_FILENAME_AS_ID<br>
<br>
- **use_fallback_reader**:<br>
  - Description: Whether to use fallback reader for RAG., type: `bool`, default: `True`<br>
  - Environment Variable: LAZYLLM_USE_FALLBACK_READER<br>
<br>
- **eval_result_dir**:<br>
  - Description: The default result directory for eval., type: `str`, default: `/home/runner/.lazyllm/eval_res`<br>
  - Environment Variable: LAZYLLM_EVAL_RESULT_DIR<br>
<br>
- **raise_on_add_doc_error**:<br>
  - Description: Whether to raise an error when adding doc failed., type: `bool`, default: `False`<br>
  - Environment Variable: LAZYLLM_RAISE_ON_ADD_DOC_ERROR<br>
<br>
- **language**:<br>
  - Description: The language of the documentation., type: `str`, default: `ENGLISH`<br>
  - Environment Variable: LAZYLLM_LANGUAGE<br>
"""
    def __init__(self, prefix='LAZYLLM', home=os.path.join(os.path.expanduser('~'), '.lazyllm')):  # noqa B008
        self._config_params = dict()
        self._env_map_name = dict()
        self.prefix = prefix
        self.impl, self.cfgs = dict(), dict()
        self.add('home', str, os.path.expanduser(home), 'HOME', description='The default home directory for LazyLLM.')
        os.makedirs(home, exist_ok=True)
        self.cgf_path = os.path.join(self['home'], 'config.json')
        if os.path.exists(self.cgf_path):
            with open(self.cgf_path, 'r+') as f:
                self.cfgs = Config.get_config(json.loads(f))

    def done(self):
        """Check if any configuration items in the config.json file that is not loaded by the add method.

Args:
    None.
"""
        assert len(self.cfgs) == 0, f'Invalid cfgs ({"".join(self.cfgs.keys())}) are given in {self.cgf_path}'
        return self

    def getenv(self, name, type, default=None):
        """Get value of LazyLLM-related environment variables.

Args:
    name (str): The name of the environment variable （without the prefix）, case-insensitive. The function obtains value
    from environment variable by concatenating the prefix and this name, with all uppercase letters.
    type (type): Specifies the type of the configuration, for example, str. For boolean types, the function will
    convert inputs ‘TRUE’, ‘True’, 1, ‘ON’, and ‘1’ to True.
    default (optional): If the value of the environment variable cannot be obtained, this value is returned.
"""
        r = os.getenv(f'{self.prefix}_{name.upper()}', default)
        if type == bool:
            return r in (True, 'TRUE', 'True', 1, 'ON', '1')
        return type(r) if r is not None else r

    @staticmethod
    def get_config(cfg):
        """
Static method: Get configuration from config dictionary.
This is a simple configuration retrieval method mainly used to extract configuration information from already loaded configuration dictionaries.

Args:
    cfg (dict): The configuration dictionary read from the config file.
"""
        return cfg

    def get_all_configs(self):
        """Get all configurations from the config.

Args:
    None.


Examples:
    >>> import lazyllm
    >>> from lazyllm.configs import config
    >>> config['launcher']
    'empty'
    >>> config.get_all_configs()
    {'home': '~/.lazyllm/', 'mode': <Mode.Normal: (1,)>, 'repr_ml': False, 'rag_store': 'None', 'redis_url': 'None', ...}
    """
        return self.impl

    @contextmanager
    def temp(self, name, value):
        """
Context manager for temporary configuration modification.

Temporarily modifies the value of the specified configuration item within the with statement block, and automatically restores the original value when exiting the block.

Args:
    name (str): The name of the configuration item to temporarily change.
    value (Any): The temporary value to set.
"""
        old_value = self[name]
        self.impl[name] = value
        yield
        self.impl[name] = old_value

    def add(self, name: str, type: type, default: Optional[Union[int, str, bool]] = None, env: Union[str, dict] = None,
            *, options: Optional[List] = None, description: Optional[str] = None):
        """Loads value into LazyLLM configuration item. The function first attempts to find the value with the given name from the
dict loaded from config.json. If found, it removes the key from the dict and saves the value to the config.
If 'env' is a string, the function calls getenv to look for the corresponding LazyLLM environment variable, and if
it's found, writes it to the config. If 'env' is a dictionary, the function attempts to call getenv to find the
environment variables corresponding to the keys in the dict and convert them to boolean type.
If the converted boolean value is True, the value corresponding to the current key in the dict is written to the config.

Args:
    name (str): The name of the configuration item
    type (type): The type of the configuration
    default (optional): The default value of the configuration if no value can be obtained
    env (optional): The name of the environment variable without the prefix, or a dictionary where the keys are the
    names of the environment variables(without the prefix), and the values are what to be added to the configuration.
"""
        update_params = (type, default, env)
        if name not in self._config_params or self._config_params[name] != update_params:
            if name in self._config_params:
                logging.warning(f'The default configuration parameter {name}({self._config_params[name]}) '
                                f'has been added, but a new {name}({update_params}) has been added repeatedly.')
            self._config_params.update({name: update_params})
            if isinstance(env, str):
                self._env_map_name[('lazyllm_' + env).upper()] = name
            elif isinstance(env, dict):
                for k in env.keys():
                    self._env_map_name[('lazyllm_' + k).upper()] = name
        self._update_impl(name, type, default, env)
        _MetaDoc._description[name] = dict(type=type.__name__, default=default,
                                           env=env, options=options, description=description)
        return self

    def _update_impl(self, name: str, type: type, default: Optional[Union[int, str, bool]] = None,
                     env: Union[str, dict] = None):
        self.impl[name] = self.cfgs.pop(name) if name in self.cfgs else default
        if isinstance(env, dict):
            for k, v in env.items():
                if self.getenv(k, bool):
                    self.impl[name] = v
                    break
        elif env:
            self.impl[name] = self.getenv(env, type, self.impl[name])
        if not isinstance(self.impl[name], type) and self.impl[name] is not None: raise TypeError(
            f'Invalid config type for {name}, type is {type}')

    def __getitem__(self, name):
        try:
            if isinstance(name, bytes): name = name.decode('utf-8')
            return self.impl[name]
        except KeyError:
            raise RuntimeError(f'Key `{name}` is not in lazyllm global config')

    def __str__(self):
        return str(self.impl)

    def refresh(self, targets: Union[bytes, str, List[str]] = None) -> None:
        """
Refresh configuration items based on the latest environment variable values.  
If `targets` is a string, updates the single corresponding configuration item;  
if it's a list, updates multiple;  
if None, scans all environment-variable-mapped configuration items and updates them.

Args:
    targets (str | list[str] | None): Name of the config key or list of keys to refresh, or None to refresh all environment-backed keys.
"""
        names = targets
        if isinstance(targets, bytes): targets = targets.decode('utf-8')
        if isinstance(targets, str):
            names = targets.lower()
            if names.startswith('lazyllm_'):
                names = names[8:]
            names = [names]
        elif targets is None:
            curr_envs = [key for key in os.environ.keys() if key.startswith('LAZYLLM_')]
            names = list(set([self._env_map_name[key] for key in curr_envs if key in self._env_map_name]))
        assert isinstance(names, list)
        for name in names:
            if name in self.impl: self._update_impl(name, *self._config_params[name])

config = Config().add('mode', Mode, Mode.Normal, dict(DISPLAY=Mode.Display, DEBUG=Mode.Debug),
                      description='The default mode for LazyLLM.'
                ).add('repr_ml', bool, False, 'REPR_USE_ML', description='Whether to use Markup Language for repr.'
                ).add('repr_show_child', bool, False, 'REPR_SHOW_CHILD',
                      description='Whether to show child modules in repr.'
                ).add('rag_store', str, 'none', 'RAG_STORE', description='The default store for RAG.'
                ).add('gpu_type', str, 'A100', 'GPU_TYPE', description='The default GPU type for LazyLLM.'
                ).add('train_target_root', str, os.path.join(os.getcwd(), 'save_ckpt'), 'TRAIN_TARGET_ROOT',
                      description='The default target root for training.'
                ).add('infer_log_root', str, os.path.join(os.getcwd(), 'infer_log'), 'INFER_LOG_ROOT',
                      description='The default log root for inference.'
                ).add('temp_dir', str, os.path.join(os.getcwd(), '.temp'), 'TEMP_DIR',
                      description='The default temp directory for LazyLLM.'
                ).add('thread_pool_worker_num', int, 16, 'THREAD_POOL_WORKER_NUM',
                      description='The default number of workers for thread pool.'
                ).add('deploy_skip_check_kw', bool, False, 'DEPLOY_SKIP_CHECK_KW',
                      description='Whether to skip check keywords for deployment.'
                )
