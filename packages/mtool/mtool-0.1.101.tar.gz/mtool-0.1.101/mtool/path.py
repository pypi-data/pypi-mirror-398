import os
import sys
from pathlib import Path


def get_app_dir() -> str:
    """
    获取程序根目录
    - 源码运行：返回 main.py 所在目录
    - PyInstaller / Nuitka 打包：返回 exe 所在目录
    """
    if "__compiled__" in globals():
        # Nuitka：argv[0] 保存的是原始 exe 路径
        return os.path.dirname(os.path.abspath(sys.argv[0]))

    # PyInstaller / 普通 exe
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))

    # 源码运行
    return os.path.dirname(os.path.abspath(sys.modules["__main__"].__file__))


def get_resource_path(*paths) -> Path:
    """
    修复版资源路径获取函数，正确处理Nuitka onefile模式
    """
    # 检查是否在临时目录中运行（Nuitka onefile的特征）
    is_in_temp = (
        "TEMP" in os.path.abspath(__file__).upper()
        or "TMP" in os.path.abspath(__file__).upper()
    )

    # 检查是否为Nuitka onefile
    is_nuitka_onefile = getattr(sys, "frozen", False) or is_in_temp

    if is_nuitka_onefile:
        # 检查是否有_MEIPASS（PyInstaller）
        if hasattr(sys, "_MEIPASS"):
            base = Path(sys._MEIPASS)
        else:
            # Nuitka onefile模式下，当前工作目录可能就是程序启动目录
            cwd = Path(os.getcwd())

            # 检查当前工作目录下是否存在目标资源
            if cwd.joinpath(*paths).exists():
                base = cwd
            else:
                # 或者使用可执行文件所在目录
                exe_dir = Path(os.path.dirname(os.path.abspath(sys.argv[0])))

                # 检查可执行文件目录下是否存在目标资源
                if exe_dir.joinpath(*paths).exists():
                    base = exe_dir
                else:
                    # 检查当前文件所在目录（nuitka解压后的临时目录）
                    file_dir = Path(os.path.dirname(os.path.abspath(__file__)))

                    # 检查临时目录下是否有recs文件夹
                    if file_dir.joinpath("recs").exists():
                        base = file_dir
                    else:
                        # 尝试临时目录的上级目录
                        if file_dir.parent.joinpath("recs").exists():
                            base = file_dir.parent
                        else:
                            # 最后尝试当前文件所在目录
                            base = file_dir
    else:
        # 源码运行
        base = Path(sys.argv[0]).resolve().parent

    result = base.joinpath(*paths)

    # 测试直接使用相对路径
    if not result.exists():
        relative_path = Path(*paths)
        if relative_path.exists():
            return relative_path

    return result


def get_data_directory(sub_dir=""):
    """
    获取数据目录路径（如input、output目录），兼容所有运行环境
    :param sub_dir: 子目录名称，如'input'、'output'
    :return: 完整的数据目录路径
    """
    # 使用通用的程序目录获取函数
    root_dir = get_app_dir()

    # 构建完整的目录路径
    if sub_dir:
        # 规范化子目录路径，去除尾部斜杠以确保正确拼接
        normalized_sub_dir = sub_dir.rstrip("/").rstrip("\\")
        return os.path.join(root_dir, normalized_sub_dir)
    return root_dir
