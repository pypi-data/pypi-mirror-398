# 使用icrawler库实现图片下载器
# pip install icrawler Pillow

import os
import sys
import hashlib
import glob
import shutil
import io
import logging
import re
from collections import defaultdict


# 自动安装缺失的依赖
def _install_missing_packages():
    """自动安装缺失的依赖包"""
    missing_packages = []

    try:
        import icrawler
    except ImportError:
        missing_packages.append("icrawler")

    try:
        from PIL import Image
    except ImportError:
        missing_packages.append("Pillow")

    try:
        import requests
    except ImportError:
        missing_packages.append("requests")

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        missing_packages.append("beautifulsoup4")

    if missing_packages:
        print(f"检测到缺失的依赖包: {missing_packages}")
        print("正在尝试自动安装...")

        import subprocess

        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✓ 成功安装 {package}")
            except subprocess.CalledProcessError as e:
                print(f"✗ 安装 {package} 失败: {e}")
                print(f"请手动运行: pip install {package}")
                return False

        print("依赖包安装完成，正在重新导入...")
        return True
    return True


# 尝试安装缺失的包
if not _install_missing_packages():
    print("请手动安装缺失的依赖包后重试")
    sys.exit(1)

# 导入依赖包
try:
    from icrawler.builtin import (
        BingImageCrawler,
        BaiduImageCrawler,
        GoogleImageCrawler,  # 原版有bug，使用下方的FixedGoogleImageCrawler替代
        FlickrImageCrawler,
        GreedyImageCrawler,
        UrlListCrawler,
    )
    from icrawler.builtin.google import GoogleFeeder
    from icrawler import Crawler, Parser, ImageDownloader as IcrawlerDownloader
    from PIL import Image
    from icrawler.storage import BaseStorage
    import requests
    from bs4 import BeautifulSoup
    import urllib.parse
    import time
    import json
except ImportError as e:
    print(f"导入依赖包失败: {e}")
    print("请运行以下命令安装依赖:")
    print("pip install icrawler Pillow requests beautifulsoup4")
    sys.exit(1)


class FixedGoogleParser(Parser):
    """修复的Google图片解析器，确保总是返回列表而不是None"""

    def parse(self, response):
        # 使用response.text让requests自动处理编码和解压
        try:
            content = response.text
        except Exception:
            content = response.content.decode("utf-8", "ignore")

        soup = BeautifulSoup(content, "html.parser")
        image_divs = soup.find_all(name="script")

        all_uris = []
        for div in image_divs:
            txt = str(div)
            # 使用更精确的正则表达式匹配图片URL
            uris = re.findall(r'https?://[^\s\'"<>\[\]]+\.(?:jpg|jpeg|png|webp)', txt, re.I)
            if uris:
                # 解码unicode转义序列
                decoded_uris = []
                for uri in uris:
                    try:
                        decoded = bytes(uri, "utf-8").decode("unicode-escape")
                        decoded_uris.append(decoded)
                    except Exception:
                        decoded_uris.append(uri)
                all_uris.extend(decoded_uris)

        # 去重
        unique_uris = list(set(all_uris))
        if unique_uris:
            return [{"file_url": uri} for uri in unique_uris]
        # 返回空列表而不是None，避免TypeError
        return []


class FixedGoogleImageCrawler(Crawler):
    """使用修复的解析器的Google图片爬虫"""

    def __init__(
        self, feeder_cls=GoogleFeeder, parser_cls=FixedGoogleParser,
        downloader_cls=IcrawlerDownloader, *args, **kwargs
    ):
        super().__init__(feeder_cls, parser_cls, downloader_cls, *args, **kwargs)
        # 设置更真实的浏览器请求头，避免被Google识别为bot
        # 注意：不能用set_session()因为它会创建新的session对象，
        # 而parser/downloader已经持有旧session的引用
        custom_headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.session.headers.update(custom_headers)

    def crawl(
        self,
        keyword,
        filters=None,
        offset=0,
        max_num=1000,
        min_size=None,
        max_size=None,
        language=None,
        file_idx_offset=0,
        overwrite=False,
        max_idle_time=None,
    ):
        if offset + max_num > 1000:
            if offset > 1000:
                self.logger.error("Offset cannot exceed 1000")
                return
            elif max_num > 1000:
                max_num = 1000 - offset
                self.logger.warning(
                    "Due to Google's limitation, max_num has been set to %d.",
                    1000 - offset,
                )
        feeder_kwargs = dict(
            keyword=keyword, offset=offset, max_num=max_num,
            language=language, filters=filters
        )
        downloader_kwargs = dict(
            max_num=max_num,
            min_size=min_size,
            max_size=max_size,
            file_idx_offset=file_idx_offset,
            overwrite=overwrite,
            max_idle_time=max_idle_time,
        )
        super().crawl(feeder_kwargs=feeder_kwargs, downloader_kwargs=downloader_kwargs)


class URLCapturingHandler(logging.Handler):
    """自定义日志处理器，用于捕获icrawler的URL信息"""

    def __init__(self):
        super().__init__()
        self.url_mappings = {}
        self.image_counter = 0

    def emit(self, record):
        """处理日志记录，提取URL信息"""
        if hasattr(record, "getMessage"):
            message = record.getMessage()
            # 匹配类似 "image #1    https://example.com/image.jpg" 的日志格式
            url_match = re.search(r"image #(\d+)\s+(https?://[^\s]+)", message)
            if url_match:
                image_num = int(url_match.group(1))
                url = url_match.group(2)
                # 根据icrawler的命名约定，图片文件名格式为 000001.jpg, 000002.jpg 等
                filename = f"{image_num:06d}.jpg"
                self.url_mappings[filename] = url


class URLMappingStorage(BaseStorage):
    """自定义存储类，用于捕获URL映射信息"""

    def __init__(self, root_dir, url_mappings):
        super().__init__(root_dir)
        self.url_mappings = url_mappings

    def write(self, task, **kwargs):
        """重写write方法来捕获URL信息"""
        file_idx = super().write(task, **kwargs)
        if file_idx is not None:
            # 捕获URL和文件路径信息
            filename = self.get_filename(task, file_idx, **kwargs)
            self.url_mappings.append(
                {
                    "file_path": filename,
                    "original_url": task.get("img_url", ""),
                    "keyword": task.get("keyword", ""),
                    "engine": task.get("engine", ""),
                }
            )
        return file_idx


class ImageDownloader:
    """使用icrawler库实现的图片下载器"""

    def __init__(self, save_dir="downloaded_images"):
        """
        初始化图片下载器

        参数:
            save_dir: 图片保存的目录，默认为"downloaded_images"
        """
        self.save_dir = save_dir
        self.save_mapping = False
        self.url_mappings = []
        os.makedirs(save_dir, exist_ok=True)

    def download_from_baidu(self, keyword, num_images=20):
        """
        从百度图片搜索并下载图片

        参数:
            keyword: 搜索关键词
            num_images: 要下载的图片数量

        返回:
            下载的图片数量
        """
        # 为每个关键词创建一个临时目录
        temp_dir = os.path.join(self.save_dir, "_temp_" + keyword.replace(" ", "_"))
        os.makedirs(temp_dir, exist_ok=True)

        # 创建最终保存的关键词目录
        keyword_dir = os.path.join(self.save_dir, keyword.replace(" ", "_"))
        os.makedirs(keyword_dir, exist_ok=True)

        print(f"从百度搜索并下载 '{keyword}' 的图片...")

        # 创建百度爬虫
        crawler = BaiduImageCrawler(
            downloader_threads=4, storage={"root_dir": temp_dir}
        )

        # 执行爬取
        crawler.crawl(keyword=keyword, max_num=num_images)

        # 如果需要保存URL映射，先从日志中提取URL信息
        url_mappings = []
        if self.save_mapping:
            url_mappings = self._extract_urls_from_temp_dir(temp_dir, keyword, "baidu")

        # 转换所有图片为jpg格式并使用哈希文件名，保存到对应关键词目录
        converted = self._convert_images_to_jpg_with_hash(
            temp_dir, keyword, keyword_dir, "baidu", url_mappings
        )

        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)

        return converted

    def download_from_bing(self, keyword, num_images=20):
        """
        从必应图片搜索并下载图片

        参数:
            keyword: 搜索关键词
            num_images: 要下载的图片数量

        返回:
            下载的图片数量
        """
        # 为每个关键词创建一个临时目录
        temp_dir = os.path.join(self.save_dir, "_temp_" + keyword.replace(" ", "_"))
        os.makedirs(temp_dir, exist_ok=True)

        # 创建最终保存的关键词目录
        keyword_dir = os.path.join(self.save_dir, keyword.replace(" ", "_"))
        os.makedirs(keyword_dir, exist_ok=True)

        print(f"从必应搜索并下载 '{keyword}' 的图片...")

        # 如果需要捕获URL，设置日志处理器
        url_handler = None
        if self.save_mapping:
            url_handler = URLCapturingHandler()
            # 获取icrawler相关的所有logger并添加我们的处理器
            loggers = ["icrawler", "downloader", "parser", "feeder"]
            for logger_name in loggers:
                logger = logging.getLogger(logger_name)
                logger.addHandler(url_handler)
                logger.setLevel(logging.INFO)

        # 创建必应爬虫
        crawler = BingImageCrawler(downloader_threads=4, storage={"root_dir": temp_dir})

        # 执行爬取
        crawler.crawl(keyword=keyword, max_num=num_images)

        # 移除URL处理器
        if url_handler:
            loggers = ["icrawler", "downloader", "parser", "feeder"]
            for logger_name in loggers:
                logger = logging.getLogger(logger_name)
                logger.removeHandler(url_handler)

        # 如果需要保存URL映射，从URL处理器中获取URL信息
        url_mappings = {}
        if self.save_mapping and url_handler:
            url_mappings = url_handler.url_mappings

        # 转换所有图片为jpg格式并使用哈希文件名，保存到对应关键词目录
        converted = self._convert_images_to_jpg_with_hash(
            temp_dir, keyword, keyword_dir, "bing", url_mappings
        )

        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)

        return converted

    def download_from_google(self, keyword, num_images=20):
        """
        从谷歌图片搜索并下载图片

        参数:
            keyword: 搜索关键词
            num_images: 要下载的图片数量

        返回:
            下载的图片数量

        注意:
            Google经常更改其HTML结构，可能导致icrawler的解析器失效。
            如果遇到问题，建议使用bing或baidu引擎替代。
        """
        # 为每个关键词创建一个临时目录
        temp_dir = os.path.join(self.save_dir, "_temp_" + keyword.replace(" ", "_"))
        os.makedirs(temp_dir, exist_ok=True)

        # 创建最终保存的关键词目录
        keyword_dir = os.path.join(self.save_dir, keyword.replace(" ", "_"))
        os.makedirs(keyword_dir, exist_ok=True)

        print(f"从谷歌搜索并下载 '{keyword}' 的图片...")

        try:
            # 创建使用修复解析器的谷歌爬虫
            crawler = FixedGoogleImageCrawler(
                downloader_threads=4, storage={"root_dir": temp_dir}
            )

            # 执行爬取
            crawler.crawl(keyword=keyword, max_num=num_images)
        except Exception as e:
            print(f"Google搜索失败: {e}")
            print("提示: Google经常更改HTML结构，建议使用bing或baidu引擎替代")

        # 如果需要保存URL映射，先从日志中提取URL信息
        url_mappings = []
        if self.save_mapping:
            url_mappings = self._extract_urls_from_temp_dir(temp_dir, keyword, "google")

        # 转换所有图片为jpg格式并使用哈希文件名，保存到对应关键词目录
        converted = self._convert_images_to_jpg_with_hash(
            temp_dir, keyword, keyword_dir, "google", url_mappings
        )

        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)

        return converted

    def download_from_flickr(
        self, keyword, num_images=20, api_key=None, api_secret=None, tag_mode="any"
    ):
        """
        从Flickr搜索并下载图片

        参数:
            keyword: 搜索关键词
            num_images: 要下载的图片数量
            api_key: Flickr API key (可选，如果没有会使用匿名模式，但功能受限)
            api_secret: Flickr API secret (可选)
            tag_mode: 标签匹配模式，'any'或'all'

        返回:
            下载的图片数量
        """
        # 为每个关键词创建一个临时目录
        temp_dir = os.path.join(self.save_dir, "_temp_" + keyword.replace(" ", "_"))
        os.makedirs(temp_dir, exist_ok=True)

        # 创建最终保存的关键词目录
        keyword_dir = os.path.join(self.save_dir, keyword.replace(" ", "_"))
        os.makedirs(keyword_dir, exist_ok=True)

        print(f"从Flickr搜索并下载 '{keyword}' 的图片...")

        try:
            # 创建Flickr爬虫
            if api_key and api_secret:
                # 使用API密钥
                crawler = FlickrImageCrawler(
                    api_key=api_key,
                    api_secret=api_secret,
                    downloader_threads=4,
                    storage={"root_dir": temp_dir},
                )
            else:
                # 匿名模式（功能受限但不需要API密钥）
                print("警告: 未提供Flickr API密钥，使用匿名模式（功能受限）")
                crawler = FlickrImageCrawler(
                    downloader_threads=4, storage={"root_dir": temp_dir}
                )

            # 执行爬取
            crawler.crawl(text=keyword, max_num=num_images, tag_mode=tag_mode)

        except Exception as e:
            print(f"Flickr爬取失败: {e}")
            print("提示: 如果需要更好的功能，请申请Flickr API密钥")
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)
            return 0

        # 如果需要保存URL映射，先从日志中提取URL信息
        url_mappings = []
        if self.save_mapping:
            url_mappings = self._extract_urls_from_temp_dir(temp_dir, keyword, "flickr")

        # 转换所有图片为jpg格式并使用哈希文件名，保存到对应关键词目录
        converted = self._convert_images_to_jpg_with_hash(
            temp_dir, keyword, keyword_dir, "flickr", url_mappings
        )

        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)

        return converted

    def download_from_website(
        self, urls, keyword="website_images", num_images=20, allowed_domains=None
    ):
        """
        从指定网站抓取所有图片（贪婪模式）

        参数:
            urls: 目标网站URL列表或单个URL
            keyword: 用于目录命名的关键词
            num_images: 最大下载图片数量
            allowed_domains: 允许的域名列表，None表示不限制

        返回:
            下载的图片数量
        """
        if isinstance(urls, str):
            urls = [urls]

        # 为每个关键词创建一个临时目录
        temp_dir = os.path.join(self.save_dir, "_temp_" + keyword.replace(" ", "_"))
        os.makedirs(temp_dir, exist_ok=True)

        # 创建最终保存的关键词目录
        keyword_dir = os.path.join(self.save_dir, keyword.replace(" ", "_"))
        os.makedirs(keyword_dir, exist_ok=True)

        print(f"从网站 {urls} 贪婪抓取图片...")

        try:
            # 创建贪婪爬虫
            crawler = GreedyImageCrawler(
                downloader_threads=4, storage={"root_dir": temp_dir}
            )

            # 执行爬取
            for url in urls:
                print(f"正在抓取网站: {url}")
                crawler.crawl(
                    domains=[url] if allowed_domains is None else allowed_domains,
                    max_num=num_images // len(urls),  # 平均分配每个URL的下载量
                )

        except Exception as e:
            print(f"网站抓取失败: {e}")
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)
            return 0

        # 如果需要保存URL映射，先从日志中提取URL信息
        url_mappings = []
        if self.save_mapping:
            url_mappings = self._extract_urls_from_temp_dir(
                temp_dir, keyword, "website"
            )

        # 转换所有图片为jpg格式并使用哈希文件名，保存到对应关键词目录
        converted = self._convert_images_to_jpg_with_hash(
            temp_dir, keyword, keyword_dir, "website", url_mappings
        )

        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)

        return converted

    def download_from_urls(self, url_list, keyword="url_images", num_images=None):
        """
        从URL列表下载图片

        参数:
            url_list: 图片URL列表或包含URL的文件路径
            keyword: 用于目录命名的关键词
            num_images: 最大下载数量，None表示下载所有

        返回:
            下载的图片数量
        """
        # 处理URL列表输入
        if isinstance(url_list, str):
            # 如果是文件路径
            if os.path.isfile(url_list):
                with open(url_list, "r", encoding="utf-8") as f:
                    urls = [line.strip() for line in f if line.strip()]
            else:
                # 如果是单个URL
                urls = [url_list]
        else:
            urls = url_list

        if not urls:
            print("错误: 没有找到有效的URL")
            return 0

        if num_images:
            urls = urls[:num_images]

        # 为每个关键词创建一个临时目录
        temp_dir = os.path.join(self.save_dir, "_temp_" + keyword.replace(" ", "_"))
        os.makedirs(temp_dir, exist_ok=True)

        # 创建最终保存的关键词目录
        keyword_dir = os.path.join(self.save_dir, keyword.replace(" ", "_"))
        os.makedirs(keyword_dir, exist_ok=True)

        print(f"从 {len(urls)} 个URL下载图片...")

        try:
            # 创建URL列表爬虫
            crawler = UrlListCrawler(
                downloader_threads=4, storage={"root_dir": temp_dir}
            )

            # 执行爬取
            crawler.crawl(urls)

        except Exception as e:
            print(f"URL列表下载失败: {e}")
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)
            return 0

        # 如果需要保存URL映射，先从日志中提取URL信息
        url_mappings = []
        if self.save_mapping:
            url_mappings = self._extract_urls_from_temp_dir(temp_dir, keyword, "urls")

        # 转换所有图片为jpg格式并使用哈希文件名，保存到对应关键词目录
        converted = self._convert_images_to_jpg_with_hash(
            temp_dir, keyword, keyword_dir, "urls", url_mappings
        )

        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)

        return converted

    def download_from_unsplash(self, keyword, num_images=20, per_page=30):
        """
        从Unsplash搜索并下载高质量免费图片（改用HTML解析方式）

        参数:
            keyword: 搜索关键词
            num_images: 要下载的图片数量
            per_page: 每页图片数量（最大30）

        返回:
            下载的图片数量
        """
        # 为每个关键词创建一个临时目录
        temp_dir = os.path.join(self.save_dir, "_temp_" + keyword.replace(" ", "_"))
        os.makedirs(temp_dir, exist_ok=True)

        # 创建最终保存的关键词目录
        keyword_dir = os.path.join(self.save_dir, keyword.replace(" ", "_"))
        os.makedirs(keyword_dir, exist_ok=True)

        print(f"从Unsplash搜索并下载 '{keyword}' 的图片...")

        try:
            downloaded_count = 0
            page = 1

            # 更真实的浏览器请求头
            session = requests.Session()
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
            }
            session.headers.update(headers)

            while downloaded_count < num_images:
                try:
                    # 构建搜索URL（使用网页版搜索）
                    search_url = (
                        f"https://unsplash.com/s/photos/{urllib.parse.quote(keyword)}"
                    )
                    if page > 1:
                        search_url += f"?page={page}"

                    print(f"  正在获取第 {page} 页...")
                    time.sleep(1)  # 增加延迟避免被限制

                    response = session.get(search_url, timeout=15)

                    if response.status_code != 200:
                        print(f"  搜索失败，状态码: {response.status_code}")
                        break

                    # 解析HTML寻找图片
                    soup = BeautifulSoup(response.content, "html.parser")

                    # 寻找图片元素
                    img_elements = soup.find_all("img", {"src": True})
                    found_images = []

                    for img in img_elements:
                        src = img.get("src", "")
                        # 过滤出Unsplash的图片URL
                        if "images.unsplash.com" in src and (
                            "photo-" in src or "unsplash-" in src
                        ):
                            # 尝试获取更高质量版本
                            if "?ixlib=" in src:
                                # 修改URL参数获取更大尺寸
                                src = src.split("?")[0] + "?ixlib=rb-4.0.3&w=1080&q=80"
                            found_images.append(src)

                    if not found_images:
                        print(f"  第 {page} 页没有找到有效图片")
                        break

                    # 下载图片
                    for img_url in found_images[
                        : min(20, num_images - downloaded_count)
                    ]:
                        if downloaded_count >= num_images:
                            break

                        try:
                            # 下载图片
                            img_response = session.get(img_url, timeout=15)
                            if img_response.status_code == 200:
                                # 生成文件名
                                filename = f"unsplash_{downloaded_count + 1}.jpg"
                                temp_path = os.path.join(temp_dir, filename)

                                with open(temp_path, "wb") as f:
                                    f.write(img_response.content)

                                downloaded_count += 1
                                print(
                                    f"    下载图片 {downloaded_count}/{num_images}: {filename}"
                                )

                            # 避免请求过快
                            time.sleep(0.3)

                        except Exception as e:
                            print(f"    下载单张图片失败: {e}")
                            continue

                    page += 1
                    if page > 10:  # 限制最大页数避免无限循环
                        break

                except Exception as e:
                    print(f"  页面获取失败: {e}")
                    break

            print(f"  Unsplash: 成功下载 {downloaded_count} 张图片")

        except Exception as e:
            print(f"Unsplash搜索失败: {e}")
            downloaded_count = 0

        # 转换所有图片为jpg格式并使用哈希文件名
        url_mappings = []
        if self.save_mapping:
            url_mappings = self._extract_urls_from_temp_dir(
                temp_dir, keyword, "unsplash"
            )

        converted = self._convert_images_to_jpg_with_hash(
            temp_dir, keyword, keyword_dir, "unsplash", url_mappings
        )

        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)

        return converted

    def download_from_pixabay(self, keyword, num_images=20, category="all"):
        """
        从Pixabay搜索并下载免费图片

        参数:
            keyword: 搜索关键词
            num_images: 要下载的图片数量
            category: 图片分类（all, backgrounds, fashion, nature, science, education等）

        返回:
            下载的图片数量
        """
        # 为每个关键词创建一个临时目录
        temp_dir = os.path.join(self.save_dir, "_temp_" + keyword.replace(" ", "_"))
        os.makedirs(temp_dir, exist_ok=True)

        # 创建最终保存的关键词目录
        keyword_dir = os.path.join(self.save_dir, keyword.replace(" ", "_"))
        os.makedirs(keyword_dir, exist_ok=True)

        print(f"从Pixabay搜索并下载 '{keyword}' 的图片...")

        try:
            downloaded_count = 0
            page = 1
            per_page = 20  # Pixabay每页最多20张

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            while downloaded_count < num_images:
                # 构建搜索URL
                search_url = "https://pixabay.com/api/"
                params = {
                    "key": "9656065-a4094594c34f9ac14c7fc4c39",  # 免费的默认key
                    "q": keyword,
                    "image_type": "photo",
                    "category": category,
                    "per_page": min(per_page, num_images - downloaded_count),
                    "page": page,
                }

                print(f"  正在获取第 {page} 页...")
                response = requests.get(
                    search_url, params=params, headers=headers, timeout=10
                )

                if response.status_code != 200:
                    print(f"  搜索失败，状态码: {response.status_code}")
                    break

                data = response.json()
                hits = data.get("hits", [])

                if not hits:
                    print(f"  第 {page} 页没有更多结果")
                    break

                # 下载图片
                for photo in hits:
                    if downloaded_count >= num_images:
                        break

                    try:
                        # 获取图片URL（选择webformatURL）
                        img_url = photo.get("webformatURL") or photo.get(
                            "largeImageURL"
                        )
                        if not img_url:
                            continue

                        # 下载图片
                        img_response = requests.get(
                            img_url, headers=headers, timeout=15
                        )
                        if img_response.status_code == 200:
                            # 生成文件名
                            photo_id = photo.get("id", f"pixabay_{downloaded_count}")
                            filename = f"{photo_id}.jpg"
                            temp_path = os.path.join(temp_dir, filename)

                            with open(temp_path, "wb") as f:
                                f.write(img_response.content)

                            downloaded_count += 1
                            print(
                                f"    下载图片 {downloaded_count}/{num_images}: {filename}"
                            )

                        # 避免请求过快
                        time.sleep(0.1)

                    except Exception as e:
                        print(f"    下载单张图片失败: {e}")
                        continue

                page += 1
                time.sleep(0.5)  # 页面间延迟

            print(f"  Pixabay: 成功下载 {downloaded_count} 张图片")

        except Exception as e:
            print(f"Pixabay搜索失败: {e}")
            downloaded_count = 0

        # 转换所有图片为jpg格式并使用哈希文件名
        url_mappings = []
        if self.save_mapping:
            url_mappings = self._extract_urls_from_temp_dir(
                temp_dir, keyword, "pixabay"
            )

        converted = self._convert_images_to_jpg_with_hash(
            temp_dir, keyword, keyword_dir, "pixabay", url_mappings
        )

        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)

        return converted

    def download_from_pexels(self, keyword, num_images=20, per_page=20):
        """
        从Pexels搜索并下载免费图片（改进反爬策略）

        参数:
            keyword: 搜索关键词
            num_images: 要下载的图片数量
            per_page: 每页图片数量

        返回:
            下载的图片数量
        """
        # 为每个关键词创建一个临时目录
        temp_dir = os.path.join(self.save_dir, "_temp_" + keyword.replace(" ", "_"))
        os.makedirs(temp_dir, exist_ok=True)

        # 创建最终保存的关键词目录
        keyword_dir = os.path.join(self.save_dir, keyword.replace(" ", "_"))
        os.makedirs(keyword_dir, exist_ok=True)

        print(f"从Pexels搜索并下载 '{keyword}' 的图片...")

        try:
            downloaded_count = 0
            page = 1

            # 创建会话并设置完整的浏览器请求头
            session = requests.Session()
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Cache-Control": "max-age=0",
            }
            session.headers.update(headers)

            # 首先访问主页建立会话
            try:
                print("  正在建立会话...")
                session.get("https://www.pexels.com/", timeout=10)
                time.sleep(1)
            except:
                pass  # 忽略主页访问错误

            while downloaded_count < num_images:
                try:
                    # 构建搜索URL
                    if page == 1:
                        search_url = f"https://www.pexels.com/search/{urllib.parse.quote(keyword)}/"
                    else:
                        search_url = f"https://www.pexels.com/search/{urllib.parse.quote(keyword)}/?page={page}"

                    print(f"  正在获取第 {page} 页...")
                    time.sleep(2)  # 增加延迟

                    response = session.get(search_url, timeout=15)

                    if response.status_code != 200:
                        print(f"  搜索失败，状态码: {response.status_code}")
                        if response.status_code == 403:
                            print("  可能被反爬机制阻止，尝试继续...")
                        break

                    # 解析HTML
                    soup = BeautifulSoup(response.content, "html.parser")

                    # 查找图片元素 - 使用更精确的选择器
                    found_images = []

                    # 方法1: 查找所有img标签
                    img_elements = soup.find_all("img")
                    for img in img_elements:
                        src = img.get("src", "")
                        # 过滤Pexels图片URL
                        if "images.pexels.com" in src:
                            # 尝试获取更大尺寸的图片
                            if "?auto=compress" in src and "w=" in src:
                                # 修改URL获取更大尺寸
                                base_url = src.split("?")[0]
                                src = (
                                    base_url
                                    + "?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1"
                                )
                            found_images.append(src)

                    # 方法2: 查找srcset属性
                    for img in img_elements:
                        srcset = img.get("srcset", "")
                        if srcset and "images.pexels.com" in srcset:
                            # 从srcset中提取最大尺寸的URL
                            urls = srcset.split(",")
                            for url_info in urls:
                                url_part = url_info.strip().split(" ")[0]
                                if "images.pexels.com" in url_part:
                                    found_images.append(url_part)

                    # 去重
                    found_images = list(set(found_images))

                    if not found_images:
                        print(f"  第 {page} 页没有找到有效图片")
                        break

                    print(f"  找到 {len(found_images)} 张图片")

                    # 下载图片
                    for img_url in found_images[
                        : min(15, num_images - downloaded_count)
                    ]:
                        if downloaded_count >= num_images:
                            break

                        try:
                            # 清理URL
                            if img_url.startswith("//"):
                                img_url = "https:" + img_url

                            # 下载图片
                            img_response = session.get(img_url, timeout=15)
                            if img_response.status_code == 200:
                                # 生成文件名
                                filename = f"pexels_{downloaded_count + 1}.jpg"
                                temp_path = os.path.join(temp_dir, filename)

                                with open(temp_path, "wb") as f:
                                    f.write(img_response.content)

                                downloaded_count += 1
                                print(
                                    f"    下载图片 {downloaded_count}/{num_images}: {filename}"
                                )

                            # 避免请求过快
                            time.sleep(0.5)

                        except Exception as e:
                            print(f"    下载单张图片失败: {e}")
                            continue

                    page += 1
                    if page > 8:  # 限制最大页数
                        break

                except Exception as e:
                    print(f"  页面获取失败: {e}")
                    break

            print(f"  Pexels: 成功下载 {downloaded_count} 张图片")

        except Exception as e:
            print(f"Pexels搜索失败: {e}")
            downloaded_count = 0

        # 转换所有图片为jpg格式并使用哈希文件名
        url_mappings = []
        if self.save_mapping:
            url_mappings = self._extract_urls_from_temp_dir(temp_dir, keyword, "pexels")

        converted = self._convert_images_to_jpg_with_hash(
            temp_dir, keyword, keyword_dir, "pexels", url_mappings
        )

        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)

        return converted

    def download_images(self, keyword, num_images=20, engine="bing", **kwargs):
        """
        根据关键词从指定搜索引擎下载图片

        参数:
            keyword: 搜索关键词
            num_images: 要下载的图片数量
            engine: 搜索引擎，支持传统引擎和免费图片源
                传统引擎: "baidu"、"bing"、"google"、"flickr"
                免费图片源: "unsplash"、"pixabay"、"pexels" (无需API密钥)
                特殊功能: "website"、"urls"
            **kwargs: 特定引擎的额外参数
                - flickr: api_key, api_secret, tag_mode
                - website: urls (必需), allowed_domains
                - urls: url_list (必需)
                - pixabay: category (可选)
                - unsplash/pexels: per_page (可选)

        返回:
            下载的图片数量
        """
        if engine == "baidu":
            return self.download_from_baidu(keyword, num_images)
        elif engine == "bing":
            return self.download_from_bing(keyword, num_images)
        elif engine == "google":
            return self.download_from_google(keyword, num_images)
        elif engine == "flickr":
            return self.download_from_flickr(
                keyword,
                num_images,
                api_key=kwargs.get("api_key"),
                api_secret=kwargs.get("api_secret"),
                tag_mode=kwargs.get("tag_mode", "any"),
            )
        elif engine == "unsplash":
            return self.download_from_unsplash(
                keyword, num_images, per_page=kwargs.get("per_page", 30)
            )
        elif engine == "pixabay":
            return self.download_from_pixabay(
                keyword, num_images, category=kwargs.get("category", "all")
            )
        elif engine == "pexels":
            return self.download_from_pexels(
                keyword, num_images, per_page=kwargs.get("per_page", 20)
            )
        elif engine == "website":
            urls = kwargs.get("urls")
            if not urls:
                raise ValueError("使用website引擎时必须提供'urls'参数")
            return self.download_from_website(
                urls,
                keyword=keyword,
                num_images=num_images,
                allowed_domains=kwargs.get("allowed_domains"),
            )
        elif engine == "urls":
            url_list = kwargs.get("url_list")
            if not url_list:
                raise ValueError("使用urls引擎时必须提供'url_list'参数")
            return self.download_from_urls(
                url_list, keyword=keyword, num_images=num_images
            )
        else:
            raise ValueError(
                f"不支持的搜索引擎: {engine}，请使用 'baidu', 'bing', 'google', 'flickr', 'unsplash', 'pixabay', 'pexels', 'website' 或 'urls'"
            )

    def _get_image_hash(self, image_data):
        """
        计算图片内容的MD5哈希值

        参数:
            image_data: 图片二进制数据

        返回:
            图片的哈希值
        """
        return hashlib.md5(image_data).hexdigest()

    def _extract_urls_from_temp_dir(self, temp_dir, keyword, engine):
        """
        从临时目录中提取文件名到URL的映射（使用icrawler的内置文件名约定）

        参数:
            temp_dir: 临时目录路径
            keyword: 搜索关键词
            engine: 搜索引擎

        返回:
            URL映射列表
        """
        # icrawler会将下载的图片按数字序号命名（000001.jpg, 000002.jpg, ...）
        # 我们创建一个映射字典来存储已知的URL信息
        # 由于无法直接从icrawler获取URL映射，这里提供基础结构
        # URL信息将在转换过程中从其他源获取
        mappings = []

        # 获取临时目录中的所有图片文件
        image_files = sorted(glob.glob(os.path.join(temp_dir, "*.*")))

        for i, img_path in enumerate(image_files):
            filename = os.path.basename(img_path)
            mappings.append(
                {
                    "temp_filename": filename,
                    "temp_path": img_path,
                    "index": i + 1,
                    "original_url": "",  # 将在后续流程中填充
                }
            )

        return mappings

    def _convert_images_to_jpg_with_hash(
        self, directory, keyword, target_dir, engine, url_mappings=None
    ):
        """
        将目录中的所有图片转换为jpg格式，并使用哈希值作为文件名

        参数:
            directory: 图片所在目录
            keyword: 搜索关键词（用于元数据）
            target_dir: 图片保存的目标目录
            engine: 使用的搜索引擎
            url_mappings: URL映射列表（可选）

        返回:
            成功转换的图片数量
        """
        converted_count = 0
        # 获取所有图片文件
        image_files = glob.glob(os.path.join(directory, "*.*"))

        for i, img_path in enumerate(image_files):
            try:
                # 尝试打开图片
                with open(img_path, "rb") as f:
                    image_data = f.read()

                # 计算图片内容的哈希值
                hash_value = self._get_image_hash(image_data)

                try:
                    # 尝试加载图片以确保它是有效的
                    img = Image.open(io.BytesIO(image_data))

                    # 转换为RGB模式（以防是RGBA或其他模式）
                    if img.mode != "RGB":
                        img = img.convert("RGB")

                    # 使用哈希值作为文件名
                    jpg_filename = f"{hash_value}.jpg"
                    jpg_path = os.path.join(target_dir, jpg_filename)

                    # 如果文件已存在，跳过（避免重复）
                    if os.path.exists(jpg_path):
                        print(f"图片已存在 (哈希值: {hash_value})")
                        converted_count += 1
                        continue

                    # 保存为jpg
                    img.save(jpg_path, "JPEG")

                    # 更新URL映射信息（如果有保存URL映射的需求）
                    if self.save_mapping:
                        original_filename = os.path.basename(img_path)
                        # 从URL映射中获取原始URL
                        original_url = ""
                        if url_mappings and isinstance(url_mappings, dict):
                            original_url = url_mappings.get(original_filename, "")

                        mapping_entry = {
                            "original_filename": original_filename,
                            "final_filename": jpg_filename,
                            "final_path": jpg_path,
                            "keyword": keyword,
                            "engine": engine,
                            "original_url": original_url,
                            "hash": hash_value,
                        }
                        self.url_mappings.append(mapping_entry)

                    converted_count += 1
                    print(f"保存图片到 {target_dir}: {jpg_filename}")

                except Exception as e:
                    print(f"处理图片失败: {e}")

            except Exception as e:
                print(f"无法处理图片 {img_path}: {e}")

        print(f"成功处理并哈希化 {converted_count} 张图片，保存到 '{target_dir}'")
        return converted_count


def download_images_cli(
    keywords,
    num_images=50,
    engines=None,
    save_dir="downloaded_images",
    save_mapping=True,
    flickr_api_key=None,
    flickr_api_secret=None,
    website_urls=None,
    url_list_file=None,
):
    """
    CLI友好的图片下载函数

    参数:
        keywords: 搜索关键词列表或单个关键词字符串
        num_images: 每个关键词要下载的图片数量，默认50
        engines: 要使用的搜索引擎列表，默认["bing", "google"]
                支持: "bing", "google", "baidu", "flickr", "website", "urls"
        save_dir: 图片保存目录，默认"downloaded_images"
        save_mapping: 是否保存图像元数据到metadata.jsonl文件，默认True
        flickr_api_key: Flickr API密钥（使用flickr引擎时需要）
        flickr_api_secret: Flickr API密钥（使用flickr引擎时需要）
        website_urls: 网站URL列表（使用website引擎时需要），用逗号分隔
        url_list_file: 包含图片URL列表的文件路径（使用urls引擎时需要）

    返回:
        下载统计信息字典
    """
    # 处理输入参数
    if isinstance(keywords, str):
        keywords = [keywords]

    if engines is None:
        engines = ["bing", "google"]
    elif isinstance(engines, str):
        engines = [engines]

    # 创建下载器实例
    downloader = ImageDownloader(save_dir=save_dir)
    downloader.save_mapping = save_mapping

    # 统计信息
    stats = {
        "total_keywords": len(keywords),
        "total_engines": len(engines),
        "downloads": {},
        "total_downloaded": 0,
    }

    print(f"开始下载图片...")
    print(f"关键词数量: {len(keywords)}")
    print(f"每个关键词下载: {num_images} 张图片")
    print(f"使用搜索引擎: {', '.join(engines)}")
    print(f"保存目录: {save_dir}")
    print("-" * 60)

    # 下载每个关键词的图片
    for i, keyword in enumerate(keywords, 1):
        print(f"\n[{i}/{len(keywords)}] 处理关键词: '{keyword}'")
        stats["downloads"][keyword] = {}

        for engine in engines:
            try:
                print(f"  使用 {engine} 搜索...")

                # 准备引擎特定的参数
                engine_kwargs = {}

                if engine == "flickr":
                    if flickr_api_key:
                        engine_kwargs["api_key"] = flickr_api_key
                    if flickr_api_secret:
                        engine_kwargs["api_secret"] = flickr_api_secret

                elif engine == "website":
                    if website_urls:
                        urls = [url.strip() for url in website_urls.split(",")]
                        engine_kwargs["urls"] = urls
                    else:
                        print(f"  {engine}: 跳过 - 需要提供 website_urls 参数")
                        stats["downloads"][keyword][engine] = 0
                        continue

                elif engine == "urls":
                    if url_list_file:
                        engine_kwargs["url_list"] = url_list_file
                    else:
                        print(f"  {engine}: 跳过 - 需要提供 url_list_file 参数")
                        stats["downloads"][keyword][engine] = 0
                        continue

                downloaded_count = downloader.download_images(
                    keyword, num_images=num_images, engine=engine, **engine_kwargs
                )
                stats["downloads"][keyword][engine] = downloaded_count
                stats["total_downloaded"] += downloaded_count
                print(f"  {engine}: 成功下载 {downloaded_count} 张图片")

            except Exception as e:
                print(f"  {engine}: 下载失败 - {e}")
                stats["downloads"][keyword][engine] = 0

        print("-" * 50)

    # 保存元数据表（如果需要）
    if save_mapping and downloader.url_mappings:
        import json
        from pathlib import Path

        metadata_file = Path(save_dir) / "metadata.jsonl"

        # 检查文件是否已存在，决定是新建还是追加
        if metadata_file.exists():
            print(f"\n追加元数据到: {metadata_file}")
            mode = "a"
        else:
            print(f"\n保存元数据表到: {metadata_file}")
            mode = "w"

        with open(metadata_file, mode, encoding="utf-8") as f:
            for mapping in downloader.url_mappings:
                json.dump(mapping, f, ensure_ascii=False)
                f.write("\n")

        print(f"已保存 {len(downloader.url_mappings)} 条元数据记录")

    # 打印总结
    print(f"\n下载完成!")
    print(f"总共下载了 {stats['total_downloaded']} 张图片")
    print(f"图片保存在: {save_dir}")

    return stats


def main():
    """主函数，演示如何使用ImageDownloader类"""
    # 创建下载器实例
    downloader = ImageDownloader(save_dir="女性图片集")

    # 示例关键词
    keywords = [
        "户外自拍女性",
        "女性写真",
        "动漫女角色",
        "影视剧女角色",
        "短片",
        "校园 女生",
        "随手拍",
        "女性 自拍",
    ]

    # 下载每个关键词的图片
    for keyword in keywords:
        downloader.download_images(keyword, num_images=100, engine="bing")
        downloader.download_images(keyword, num_images=100, engine="google")
        downloader.download_images(keyword, num_images=100, engine="baidu")
        print("-" * 50)


if __name__ == "__main__":
    # download_images_simple()
    main()
