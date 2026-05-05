"""
自动加入社区工作线程
"""
from PyQt6.QtCore import QObject, pyqtSignal
from modules.auto_join_community import XAutoJoinCommunity

class AutoJoinCommunityWorker(QObject):
    """自动加入社区工作线程"""
    progress = pyqtSignal(int, int, str)  # (当前, 总数, 消息)
    finished = pyqtSignal(bool, str, int)  # (成功, 消息, 数量)
    log = pyqtSignal(str)
    
    def __init__(self, auto_join, community_keywords):
        super().__init__()
        self.auto_join = auto_join
        self.community_keywords = community_keywords
    
    def start_join(self):
        try:
            def callback(current, total, message):
                self.progress.emit(current, total, message)
            
            def log_callback(msg):
                self.log.emit(msg)
            
            count = self.auto_join.start_join_groups(
                self.community_keywords, 
                callback, 
                log_callback
            )
            self.finished.emit(True, f"自动加入社区完成，共处理 {count} 个关键词", count)
        except Exception as e:
            self.finished.emit(False, str(e), 0)
