"""
工具函数模块
"""
import json
import os

def load_json(file_path, default=None):
    """加载JSON文件"""
    if default is None:
        default = {}
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"加载JSON失败 {file_path}: {e}")
    return default

def save_json(file_path, data):
    """保存JSON文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存JSON失败 {file_path}: {e}")
        return False

def get_next_resource_pair(images_dir, texts_dir, index_file):
    """
    获取下一对配对的图片和文案（支持轮询）
    :param images_dir: 图片文件夹路径
    :param texts_dir: 文案文件夹路径
    :param index_file: 索引记录文件路径
    :return: (image_path, text_content, next_id)
    """
    if not os.path.exists(images_dir) or not os.path.exists(texts_dir):
        return None, None, 0

    # 1. 扫描图片文件夹，获取所有数字命名的图片 ID
    image_ids = []
    for f in os.listdir(images_dir):
        name, ext = os.path.splitext(f)
        if name.isdigit() and ext.lower() in ['.png', '.jpg', '.jpeg']:
            image_ids.append(int(name))
    
    if not image_ids:
        return None, None, 0
    
    image_ids.sort()
    max_count = image_ids[-1]
    
    # 2. 读取当前索引
    current_idx = load_json(index_file, {}).get('last_index', 0)
    
    # 3. 计算下一个 ID（轮询逻辑）
    next_id = (current_idx % max_count) + 1
    
    # 4. 寻找存在的 ID（防止中间有缺号）
    attempts = 0
    while next_id not in image_ids and attempts < max_count:
        next_id = (next_id % max_count) + 1
        attempts += 1
        
    if next_id not in image_ids:
        return None, None, 0
        
    # 5. 保存新索引
    save_json(index_file, {'last_index': next_id})
    
    # 6. 拼接路径并读取文案
    image_path = None
    for f in os.listdir(images_dir):
        if f.startswith(str(next_id) + '.'):
            image_path = os.path.join(images_dir, f)
            break
            
    text_path = os.path.join(texts_dir, f"{next_id}.txt")
    text_content = ""
    if os.path.exists(text_path):
        with open(text_path, 'r', encoding='utf-8') as f:
            text_content = f.read().strip()
    else:
        text_content = "" # 或者返回错误提示
        
    return image_path, text_content, next_id
