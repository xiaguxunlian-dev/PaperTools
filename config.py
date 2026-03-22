"""
配置管理模块 — API Key 存储与读取（内存模式，沙盒兼容）
"""
import json

DEFAULT_KEYS = {
    'pubmed': None,
    'semanticscholar': None,
    'openalex': None,
    'crossref': None,
    'bgpt': None,
}


class Config:
    """科研套件配置管理（内存模式，不读写磁盘）"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = {
                'api_keys': DEFAULT_KEYS.copy(),
                'defaults': {
                    'max_results': 20,
                    'default_dbs': ['pubmed', 'arxiv', 'semantic'],
                    'language': 'zh-CN',
                },
                'preferences': {},
            }
        return cls._instance

    def get_api_keys(self) -> dict:
        return self._config.get('api_keys', DEFAULT_KEYS).copy()

    def get_api_key(self, name: str) -> str | None:
        return self._config.get('api_keys', {}).get(name)

    def set_api_key(self, name: str, value: str):
        if 'api_keys' not in self._config:
            self._config['api_keys'] = DEFAULT_KEYS.copy()
        self._config['api_keys'][name] = value

    def list_api_keys(self) -> dict:
        return {k: bool(v) for k, v in self._config.get('api_keys', DEFAULT_KEYS).items()}

    def get(self, key: str, default=None):
        return self._config.get(key, default)

    def set(self, key: str, value):
        self._config[key] = value

    @classmethod
    def get_defaults(cls) -> dict:
        return {
            'max_results': 20,
            'default_dbs': ['pubmed', 'arxiv', 'semantic'],
            'language': 'zh-CN',
        }
