import os
import shutil


class Cleaner:
    def cleanup(clean_up: list):
        print(f"  (1/1) Cleaner.cleanup: 正在清理")
        for file in clean_up:
            if file.exists():
                if os.path.isfile(str(file)):
                    os.remove(str(file))
                    print(f"    已删除文件: {file}")
                else:
                    shutil.rmtree(str(file))
                    print(f"    已删除目录: {file}")
