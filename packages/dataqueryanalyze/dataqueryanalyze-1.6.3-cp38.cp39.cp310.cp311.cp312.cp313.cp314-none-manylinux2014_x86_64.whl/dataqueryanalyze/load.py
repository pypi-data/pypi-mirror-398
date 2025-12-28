#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import platform
import threading
# 确保当前目录在Python路径中，以便导入app模块
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入app模块
import app
# 导入add_tok函数
from core.llm import add_tok
# 导入更新检查函数
from dataqueryanalyze import check_for_updates

def main():
    # 检查并创建tok.xml文件
    add_tok()
    
    # 在后台线程中检查更新，不阻塞主程序启动
    update_thread = threading.Thread(target=check_for_updates, daemon=True)
    update_thread.start()
    
    # 调用app.py中的main()函数
    app.main()

if __name__ == '__main__':
    main()
