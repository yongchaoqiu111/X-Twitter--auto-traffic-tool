"""
国际化 (i18n) 翻译管理器
"""
import json
import os


class I18nManager:
    """翻译管理器"""
    
    _instance = None
    _translations = {}
    _current_lang = "zh"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.load_translations()
    
    def load_translations(self):
        """加载所有语言文件"""
        i18n_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'i18n')
        
        for lang_file in os.listdir(i18n_dir):
            if lang_file.endswith('.json'):
                lang_code = lang_file.replace('.json', '')
                with open(os.path.join(i18n_dir, lang_file), 'r', encoding='utf-8') as f:
                    self._translations[lang_code] = json.load(f)
    
    def set_language(self, lang_code):
        """设置当前语言"""
        if lang_code in self._translations:
            self._current_lang = lang_code
            return True
        return False
    
    def get_current_language(self):
        """获取当前语言"""
        return self._current_lang
    
    def t(self, key, default=None):
        """获取翻译文本"""
        if self._current_lang in self._translations:
            return self._translations[self._current_lang].get(key, default or key)
        return default or key
    
    def get_available_languages(self):
        """获取可用语言列表"""
        return list(self._translations.keys())
