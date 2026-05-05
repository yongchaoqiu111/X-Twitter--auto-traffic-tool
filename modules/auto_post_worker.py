"""
X 自动发帖工作线程
"""
from PyQt6.QtCore import QObject, pyqtSignal
from modules.auto_post import XAutoPost

class AutoPostWorker(QObject):
    """自动发帖工作线程"""
    progress = pyqtSignal(int, int, str)  # (当前, 总数, 消息)
    finished = pyqtSignal(bool, str, int)  # (成功, 消息, 数量)
    log = pyqtSignal(str)
    
    def __init__(self, auto_post, images_dir, texts_dir, img_path=None, text_path=None):
        super().__init__()
        self.auto_post = auto_post
        self.images_dir = images_dir
        self.texts_dir = texts_dir
        self.img_path = img_path
        self.text_path = text_path
    
    def start_posting(self):
        try:
            def callback(current, total, message):
                self.progress.emit(current, total, message)
            
            def log_callback(msg):
                self.log.emit(msg)
            
            # 如果指定了单个文件，使用单帖模式
            if self.img_path and self.text_path:
                count = self.auto_post.start_posting_single(
                    self.img_path, 
                    self.text_path,
                    callback, 
                    log_callback
                )
            else:
                count = self.auto_post.start_posting(
                    self.images_dir, 
                    self.texts_dir, 
                    callback, 
                    log_callback
                )
            self.finished.emit(True, f"自动发帖完成，共发布 {count} 条", count)
        except Exception as e:
            self.finished.emit(False, str(e), 0)
