"""
FlaxKV2 守护进程运行器

被 DaemonServerManager 调用来启动服务器守护进程。
不应该直接运行此模块。
"""

import os
import sys
import signal
import argparse


def main():
    """守护进程入口"""
    parser = argparse.ArgumentParser(description="FlaxKV2 Server Daemon Runner")
    parser.add_argument("--socket-path", help="Unix Socket path")
    parser.add_argument("--host", default="127.0.0.1", help="TCP host")
    parser.add_argument("--port", type=int, default=5555, help="TCP port")
    parser.add_argument("--data-dir", required=True, help="Data directory")
    parser.add_argument("--pid-file", required=True, help="PID file path")
    parser.add_argument("--log-file", help="Log file path")
    parser.add_argument("--enable-encryption", action="store_true", help="Enable encryption")
    parser.add_argument("--password", help="Encryption password")
    parser.add_argument("--workers", type=int, default=4, help="Number of workers")

    args = parser.parse_args()

    # 写入 PID 文件
    with open(args.pid_file, 'w') as f:
        f.write(str(os.getpid()))

    # 设置信号处理
    def cleanup_and_exit(signum, frame):
        # 清理 PID 文件
        try:
            if os.path.exists(args.pid_file):
                os.unlink(args.pid_file)
        except OSError:
            pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, cleanup_and_exit)
    signal.signal(signal.SIGINT, cleanup_and_exit)

    # 导入并启动服务器
    from flaxkv2.server.zmq_server import FlaxKVServer

    server_kwargs = {
        'data_dir': args.data_dir,
        'max_workers': args.workers,
    }

    if args.socket_path:
        server_kwargs['socket_path'] = args.socket_path
    else:
        server_kwargs['host'] = args.host
        server_kwargs['port'] = args.port

    if args.enable_encryption:
        server_kwargs['enable_encryption'] = True
        if args.password:
            server_kwargs['password'] = args.password

    server = FlaxKVServer(**server_kwargs)

    try:
        server.run()
    finally:
        # 确保清理 PID 文件
        try:
            if os.path.exists(args.pid_file):
                os.unlink(args.pid_file)
        except OSError:
            pass


if __name__ == "__main__":
    main()
