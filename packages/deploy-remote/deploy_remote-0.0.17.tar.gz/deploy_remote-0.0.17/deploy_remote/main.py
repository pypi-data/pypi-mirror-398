"""
Deploy Remote CLI - 跨平台自动化部署工具
"""
import logging
import os
import platform
import subprocess
import sys


def get_binary_name():
    """根据当前系统获取对应的二进制文件名"""
    system = platform.system().lower()
    arch = platform.machine().lower()

    # 标准化架构名称
    if arch in ("arm64", "aarch64"):
        arch = "arm64"
    else:
        arch = "amd64"

    if system == "windows":
        return f"deploy_windows_{arch}.exe"
    elif system == "darwin":
        return f"deploy_macos_{arch}"
    elif system == "linux":
        return f"deploy_linux_{arch}"
    else:
        return None


def run(args=None):
    """CLI 入口点"""
    cli_args = args if args is not None else sys.argv[1:]

    binary_name = get_binary_name()
    if not binary_name:
        logging.error(f"Unsupported operating system: {platform.system()}")
        return

    binary_path = os.path.join(os.path.dirname(__file__), binary_name)

    if not os.path.exists(binary_path):
        logging.error(f"Binary file not found: {binary_path}")
        return

    cmd_args, err = build_command_args(cli_args)
    if err:
        logging.error(err)
        return

    command = [binary_path] + cmd_args
    if cmd_args:
        print("Running:", " ".join(cmd_args))

    try:
        # 直接运行，让 Go 程序继承 stdin/stdout/stderr
        # 这样 Go 程序可以直接与用户交互（如输入版本号）
        process = subprocess.run(command)

        if process.returncode != 0:
            print(f"Command exited with code {process.returncode}")
            sys.exit(process.returncode)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
def build_command_args(cli_args):
    """
    解析传入的命令行参数，并构造传递给 Go 可执行文件的参数列表。
    """
    # 直接透传所有参数给 Go 可执行文件
    # Go 端会处理版本号的读取、验证和用户交互
    return list(cli_args), None
