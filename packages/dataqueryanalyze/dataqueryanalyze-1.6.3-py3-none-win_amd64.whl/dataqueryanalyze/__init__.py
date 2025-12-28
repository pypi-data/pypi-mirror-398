# 数据查析 - DataQueryAnalyze
# 专有软件许可证，保留所有权利
# 未经许可，不得复制、修改、分发或售卖

__version__ = "1.6.3"
__author__ = "Randy"
__email__ = "411703730@qq.com"

# 导入必要的库
import os
import sys
import threading
import requests
from packaging import version

# 导出所有公开API
__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "check_for_updates"
]


def check_for_updates():
    """检查软件更新，从PyPI获取最新版本并自动下载安装"""
    print("检查软件更新中...")
    
    try:
        # 使用PyPI API检查最新版本
        pypi_url = f"https://pypi.org/pypi/dataqueryanalyze/json"
        response = requests.get(pypi_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            latest_version = data["info"]["version"]
            current_version = __version__
            
            print(f"当前版本: {current_version}")
            print(f"最新版本: {latest_version}")
            
            if version.parse(latest_version) > version.parse(current_version):
                print(f"发现新版本: {latest_version}")
                print("正在自动下载并安装最新版本...")
                
                # 使用subprocess调用pip更新
                import subprocess
                try:
                    # 调用pip安装最新版本
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "--upgrade", "dataqueryanalyze"],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if result.returncode == 0:
                        print("更新成功！请重启应用程序以应用更新。")
                    else:
                        print(f"更新失败: {result.stderr}")
                        print(f"请手动运行 'pip install --upgrade dataqueryanalyze' 进行更新")
                except subprocess.TimeoutExpired:
                    print("更新超时，请手动运行 'pip install --upgrade dataqueryanalyze' 进行更新")
                except Exception as e:
                    print(f"更新过程中发生错误: {str(e)}")
                    print(f"请手动运行 'pip install --upgrade dataqueryanalyze' 进行更新")
            else:
                print("当前已是最新版本")
        else:
            print(f"更新检查失败，服务器返回状态码: {response.status_code}")
    except requests.Timeout:
        print("更新检查超时，跳过更新")
    except requests.RequestException as e:
        print(f"更新检查失败: {str(e)}")
    except Exception as e:
        print(f"更新检查发生未知错误: {str(e)}")
