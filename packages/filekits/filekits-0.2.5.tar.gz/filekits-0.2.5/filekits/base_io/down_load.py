import os
import base64
import requests
from funcguard.tools import send_request

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}


def _send_request_with_retry(url, headers=None):
    """
    内部方法：发送带重试的请求，处理阿里CDN特殊逻辑

    Args:
        url: 请求的URL
        headers: 自定义请求头（可选）
        return_type: 返回类型，可选值：'json', 'text', 'response'

    Returns:
        response: 请求响应对象或解析后的数据
    """
    if headers is None:
        headers = DEFAULT_HEADERS

    # 为阿里cdn添加特殊处理
    # if "https://cbu01.alicdn.com" in url:
    #     response = send_request(method='GET', url=url, headers=headers, return_type=return_type)

    response = send_request(
        method="GET", url=url, headers=headers, return_type="response"
    )

    return response


# 下载网络文件
def download_file(url, download_dir, file_name="", return_type="name"):
    """
    使用 send_request 自动重试功能下载网络文件

    Args:
        url: 文件URL
        download_dir: 下载目录
        file_name: 自定义文件名（可选，如果不提供则从URL提取）
        return_type: 返回类型，可选值：
            - "name": 仅返回文件名（默认）
            - "path": 仅返回完整路径
            - "both": 返回(路径, 文件名)元组

    Returns:
        根据return_type参数返回：
            - "name": 文件名
            - "path": 完整路径
            - "both": (路径, 文件名)元组
        示例用法：
            file_path, file_name = download_file(url, download_dir, return_type="both")
    """
    # 生成文件名
    if file_name == "":
        file_name = url.split("/")[-1]
    else:
        # 如果提供了自定义文件名但没有扩展名，从URL获取扩展名
        if "." not in file_name:
            file_extension = url.split(".")[-1] if "." in url.split("/")[-1] else ""
            if file_extension:
                file_name = f"{file_name}.{file_extension}"

    file_path = os.path.join(download_dir, file_name)

    # 检查文件是否已经存在
    if os.path.exists(file_path):
        print(f"文件 {file_name} 已经存在，跳过下载")
    else:
        try:
            response = _send_request_with_retry(url)

            # 以二进制模式写入文件
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    if chunk:  # 过滤掉空chunk
                        file.write(chunk)

        except Exception as e:
            print(f"文件下载失败, url： {url} \nReason：{e}")
            raise e  # 重新抛出异常，让调用者处理

    if return_type == "name":
        return file_name
    elif return_type == "path":
        return file_path
    elif return_type == "both":
        return file_path, file_name
    else:
        raise ValueError("return_type 参数错误，请传入 'name'、'path' 或 'both'")


# 批量下载文件(单线程)，默认下载图片
def download_files(
    files, output_folder,
    return_type="list", extensions=None, on_fail_action="skip"
):
    """
    批量下载文件

    Args:
        files: 文件URL列表
        output_folder: 下载目录
        return_type: 返回类型，"list"或"dict"
        extensions: 允许的文件扩展名列表，None表示允许所有类型
        on_fail_action: 失败次数过多时的行为，可选值：
            - "skip": 跳过并结束整个循环（默认）
            - "raise": 抛出异常，报出错误

    Returns:
        根据return_type参数返回文件路径列表或字典列表

    Raises:
        RuntimeError: 当on_fail_action="raise"且下载失败次数过多时抛出
    """
    if extensions is None:
        extensions = []

    files_path = []
    i = 0  # 将i移到循环外部
    download_fail_count = 0  # 将失败计数器也移到外部，按整个批次计算
    failed_urls = []  # 记录失败的URL

    for url in files:
        # 提取文件扩展名
        ext = os.path.splitext(url)[1]

        # 判断是否允许该扩展名
        if extensions and ext.lower() not in extensions:
            print(f"跳过不支持的文件类型: {url}")
            continue

        # 替换文件类型后缀，避免后面重复拼接形成.jpg.jpg的情况
        file_name = url.split("/")[-1].replace(ext, "")

        # 如果文件名太短，加前缀防止重命名冲突
        if len(file_name) < 7:
            file_name = f"{i}_{file_name}"
            i += 1

        try:
            file_path = download_file(url, output_folder, file_name, return_type="path")
        except Exception as e:
            print(f"文件下载失败，已跳过：{url}")
            download_fail_count += 1
            failed_urls.append(url)

            if download_fail_count > 3:
                error_msg = f"文件下载失败次数过多，已失败 {download_fail_count} 个文件。失败的URL: {failed_urls}"

                if on_fail_action == "raise":
                    raise RuntimeError(error_msg)
                elif on_fail_action == "skip":
                    print(error_msg + "，已跳过剩余文件")
                    break  # 终止整个循环
                else:
                    raise ValueError(
                        "on_fail_action 参数错误，请传入 'skip' 或 'raise'"
                    )

            continue

        if return_type == "list":
            files_path.append(file_path)
        elif return_type == "dict":
            files_path.append({"path": file_path, "url": url})
        else:
            raise ValueError("return_type 参数错误，请传入 'list' 或 'dict'")

    return files_path


# 下载网络文件并转为base64编码
def download_encode_base64(url):
    """
    下载网络文件并直接返回base64编码

    Args:
        url: 文件URL

    Returns:
        str: 文件的base64编码字符串

    Raises:
        Exception: 下载失败时抛出异常
    """
    try:
        response = _send_request_with_retry(url)

        # 读取文件内容并转为base64
        file_data = response.content
        base64_data = base64.b64encode(file_data).decode("utf-8")

        return base64_data

    except Exception as e:
        print(f"文件下载或转换base64失败, url：{url} \n Reason：{e}")
        raise e


# 批量 下载网络文件并转为base64编码
def batch_download_encode_base64(urls: list, skip_error=True):
    """
    批量下载网络文件并转为base64编码

    Args:
        urls: 文件URL列表
        skip_error: 是否跳过错误文件，默认True

    Returns:
        list: 包含每个文件base64编码的列表

    Raises:
        Exception: 下载失败时抛出异常
    """
    base64_list = []
    for url in urls:
        try:
            base64_data = download_encode_base64(url)
            base64_list.append(base64_data)
        except Exception as e:
            if skip_error:
                print(f"跳过错误文件 {url}，错误信息：{e}")
            else:
                raise e
    return base64_list


# 检查url是否有效
def check_url_valid(url, headers=None, max_retries=3):
    """
    检查url是否有效

    Args:
        url: 文件URL
        headers: 自定义请求头（可选）
        max_retries: 最大重试次数，默认3次

    Returns:
        bool: 如果URL有效则返回True，否则返回False
    """
    if headers is None:
        headers = DEFAULT_HEADERS
    
    for attempt in range(max_retries):
        try:
            response = requests.head(url, headers=headers, timeout=60, allow_redirects=True)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(str(e))
            # HEAD请求失败，立即尝试GET请求作为降级方案
            print(f"HEAD请求失败，尝试使用GET请求检查URL:\n{url}")
            try:
                response = requests.get(url, headers=headers, timeout=60, allow_redirects=True, stream=True)
                return response.status_code == 200
            except requests.exceptions.RequestException as get_e:
                print(f"GET请求也失败:\n{str(get_e)}")
                if attempt < max_retries - 1:
                    print(f"URL检查失败，正在重试 ({attempt + 1}/{max_retries})\n{url}")
                    continue
                else:
                    print(f"URL检查失败，已达到最大重试次数 ({max_retries}):\n{url}")
                    return False
    return False
