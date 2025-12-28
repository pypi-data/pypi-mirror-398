# Enhanced Downloader

一个功能强大的Python下载模块，支持：

- 单线程和多线程下载
- 自动检测服务器是否支持分片
- 断点续传
- 进度显示
- 返回内容或保存到文件
- 智能下载策略

## 安装

```bash
pip install enhanced_downloader
```

## 使用示例

```python
from enhanced_downloader import download_file

# 下载并保存到指定路径
download_path = download_file("https://example.com/large_file.zip", save_path="/path/to/save")
print(f"文件保存路径: {download_path}")

# 下载并返回内容
file_content = download_file("https://example.com/file.txt", return_content=True)
print(f"获取到文件内容，大小: {len(file_content)} 字节")

# 使用更多参数
download_path = download_file(
    url="https://example.com/large_file.zip",
    save_path="output.zip",
    num_threads=20,
    timeout=60,
    temp_dir="/tmp/downloads",
    min_size_for_multithread=5*1024*1024  # 5MB以上使用多线程
)
```

## 高级用法

```python
from enhanced_downloader import EnhancedDownloader

# 创建下载器实例
downloader = EnhancedDownloader()

# 使用实例方法
downloader.download(
    url="https://example.com/file.zip",
    save_path="downloads/file.zip",
    num_threads=30,
    force_single_thread=False
)
```

## 参数说明

- `url`: 下载链接
- `save_path`: 保存文件的路径，支持目录或完整文件路径
- `return_content`: 是否返回文件内容而不是保存到本地
- `chunk_size`: 下载块大小
- `timeout`: 请求超时时间（秒）
- `num_threads`: 多线程下载时的线程数
- `temp_dir`: 临时文件目录
- `force_single_thread`: 是否强制使用单线程下载
- `min_size_for_multithread`: 启用多线程下载的最小文件大小

## 版本更新
- 0.1.0: 初始版本
- 0.1.1: 优化多线程下载性能
- 0.1.2: 添加速度限制功能
- 0.1.3: 未指定目录时自动保存到最大可用磁盘，修复路径判断逻辑
- 0.2.0: 添加允许指定代理功能，优化下载速度

## 许可证

MIT License - 详见 LICENSE 文件