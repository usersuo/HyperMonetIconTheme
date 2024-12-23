import os
import shutil

# 清理器
class Cleaner:
    def cleanup(clean_up: list):
        """批量生成填充风格图标

        Args:
            clean_up: 可能需要清理的文件或目录列表
        """
        print(f"  (1/1) Cleaner.cleanup: 正在清理")
        for file in clean_up:
            if file.exists():
                if os.path.isfile(str(file)):
                    os.remove(str(file))
                    print(f"    已删除文件: {file}")
                else:
                    shutil.rmtree(str(file))
                    print(f"    已删除目录: {file}")