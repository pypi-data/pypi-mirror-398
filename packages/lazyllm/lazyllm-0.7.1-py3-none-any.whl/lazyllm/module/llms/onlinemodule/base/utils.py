from ....module import ModuleBase
from lazyllm import config
from typing import Optional, Union, List
import random


config.add('cache_online_module', bool, False, 'CACHE_ONLINE_MODULE',
           description='Whether to cache the online module result. Use for unit test.')


class OnlineModuleBase(ModuleBase):
    """Base class for online modules, inheriting from ModuleBase, providing unified basic functionality for all online service modules.  
This class encapsulates common behaviors of online modules, including caching mechanisms and debug tracing functionality, serving as the foundation for building various online API service modules.

Key Features:
    - Inherits all basic functionality from ModuleBase, including submodule management, hook registration, etc.
    - Supports online module caching mechanism, controllable through configuration.
    - Provides debug tracing functionality for troubleshooting and performance analysis.
    - Serves as a common base class for all online service modules (chat, embedding, multimodal, etc.).

Args:
    return_trace (bool): Whether to write inference results into the trace queue for debugging and tracking. Default is ``False``.

Use Cases:
    1. As a base class for online chat modules (OnlineChatModuleBase).
    2. As a base class for online embedding modules (OnlineEmbeddingModuleBase).
    3. As a base class for online multimodal modules (OnlineMultiModalBase).
    4. Providing unified basic functionality for custom online service modules.
"""
    def __init__(self, api_key: Optional[Union[str, List[str]]],
                 skip_auth: Optional[bool] = False, return_trace: bool = False):
        super().__init__(return_trace=return_trace)
        if not skip_auth and not api_key: raise ValueError('api_key is required')
        self.__api_keys = '' if skip_auth else api_key
        self.__headers = [self._get_header(key) for key in (api_key if isinstance(api_key, list) else [api_key])]
        if config['cache_online_module']:
            self.use_cache()

    @property
    def _api_key(self):
        return random.choice(self.__api_keys) if isinstance(self.__api_keys, list) else self.__api_keys

    @staticmethod
    def _get_header(api_key: str) -> dict:
        return {'Content-Type': 'application/json', **({'Authorization': 'Bearer ' + api_key} if api_key else {})}

    def _get_empty_header(self, api_key: Optional[str] = None) -> dict:
        api_key = api_key or self._api_key
        return {'Authorization': f'Bearer {api_key}'} if api_key else None

    @property
    def _header(self):
        return random.choice(self.__headers)
