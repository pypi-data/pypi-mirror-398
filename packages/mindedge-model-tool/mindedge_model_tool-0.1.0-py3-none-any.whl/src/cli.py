# src/minio_downloader/cli.py
import os
import sys
import json
import argparse
from minio import Minio
from minio.error import S3Error
from urllib.parse import urlparse


def load_node_config(config_path=None):
    if config_path:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {config_path} - {e}")
    else:
        node_config_str = os.getenv('NODE_CONFIG')
        if not node_config_str:
            raise ValueError("请通过 --config 指定配置文件，或设置 NODE_CONFIG 环境变量")
        try:
            return json.loads(node_config_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"环境变量 NODE_CONFIG 格式错误: {e}")


def parse_minio_url(endpoint):
    if not endpoint.startswith(('http://', 'https://')):
        endpoint = 'http://' + endpoint
    parsed = urlparse(endpoint)
    secure = parsed.scheme == 'https'
    host = parsed.hostname
    if not host:
        # 如果hostname为None，尝试从netloc中提取（不包含端口）
        host = parsed.netloc.split(':')[0] if parsed.netloc else None
    if not host:
        raise ValueError(f"无法从endpoint中解析主机名: {endpoint}")
    
    port = parsed.port
    
    if port:
        host = f"{host}:{port}"
    elif not port and parsed.scheme == 'https':
        host = f"{host}:443"
    elif not port:
        host = f"{host}:9000"  # MinIO默认端口是9000，不是80
        
    return host, secure


def download_file(file_key, output_path, config_path=None, bucket_name="suanpan"):
    """实际的下载函数，供命令行工具调用"""
    try:
        config = load_node_config(config_path)
        oss = config.get('oss', {})
        
        if not oss:
            print("❌ 配置文件中未找到 'oss' 配置项", file=sys.stderr)
            sys.exit(1)
            
        if 'internalEndpoint' not in oss:
            print("❌ 配置文件中缺少 'internalEndpoint' 配置项", file=sys.stderr)
            sys.exit(1)
            
        if 'accessKey' not in oss or 'accessSecret' not in oss:
            print("❌ 配置文件中缺少 'accessKey' 或 'accessSecret' 配置项", file=sys.stderr)
            sys.exit(1)

        endpoint, secure = parse_minio_url(oss['internalEndpoint'])
        client = Minio(
            endpoint,
            access_key=oss['accessKey'],
            secret_key=oss['accessSecret'],
            secure=secure
        )

        # 确保输出目录存在
        output_dir = os.path.dirname(os.path.abspath(output_path))
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # 下载文件
        client.fget_object(bucket_name, file_key, output_path)
        print(f"✅ 已下载: {file_key} → {output_path}")
        
    except S3Error as e:
        print(f"❌ MinIO 错误: {e}", file=sys.stderr)
        sys.exit(1)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="mindedge-model-tool",
        description="从 MinIO 下载文件的命令行工具"
    )
    parser.add_argument(
        "file_key",
        help="MinIO 对象键（object key），存储桶名称通过 -b 参数指定"
    )
    parser.add_argument(
        "-o", "--output",
        default="./downloaded_file",
        help="本地保存路径"
    )
    parser.add_argument(
        "-c", "--config",
        help="配置文件路径（JSON，含 oss.accessKey 等）"
    )
    parser.add_argument(
        "-b", "--bucket",
        default="suanpan",
        help="MinIO 存储桶名称，默认为 'suanpan'"
    )

    args = parser.parse_args()
    download_file(args.file_key, args.output, args.config, args.bucket)