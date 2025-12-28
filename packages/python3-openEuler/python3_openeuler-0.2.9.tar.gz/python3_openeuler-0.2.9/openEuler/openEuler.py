import re
import os
import json
import logging
import tempfile
import urllib.parse
import gzip
import bz2
import zstandard as zstd
import xml.etree.ElementTree as ET
from typing import List
from tempfile import TemporaryDirectory
from typing import Generator
from pathlib import Path
import git
import requests
from bs4 import BeautifulSoup
import traceback
import functools
import inspect
from typing import Callable, Any
from typing import List, Dict, Any, Optional

import requests.exceptions
from typing import Generator, Optional,Tuple

log=logging.getLogger(__name__)

def enter_and_leave_function(func: Callable) -> Callable:
    """
    函数调用日志装饰器：
    1. 记录函数入参、调用位置
    2. 正常执行时记录返回值
    3. 异常时记录完整堆栈（含函数内具体报错行数）
    """

    @functools.wraps(func)  # 保留原函数元信息（如 __name__、__doc__）
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # 获取函数定义的文件路径和行号（基础位置信息）
        func_def_file = inspect.getsourcefile(func) or "unknown_file"
        func_def_file = func_def_file.split("/")[-1]
        func_def_line = inspect.getsourcelines(func)[1] if func_def_file != "unknown_file" else "unknown_line"
        log.info(
            f"[{func_def_file}: {func_def_line}]"
            f"[{func.__name__}()]"
            f"| args={args}, kwargs={kwargs}"
        )

        try:
            result = func(*args, **kwargs)
            log.info(
                f"[{func_def_file}: {func_def_line}]"
                f" finish run function {func.__name__}(), return value is: {result} "
            )
            return result

        except Exception as e:
            error_traceback = traceback.format_exc()

            log.error(
                f"[{func_def_file}: {func_def_line}]"
                f"failed to run function {func.__name__}() :Failed. "
                f"| error_type：{type(e).__name__} "
                f"| error_message：{str(e)} "
                f"| full_stack_trace：\n{error_traceback}",
                exc_info=False  # 已手动捕获堆栈，避免 logging 重复打印
            )
            raise  # 重新抛出异常，不中断原异常链路

    return wrapper

class Gitee():
    def __init__(self):
        self.__base_url= "https://gitee.com/api/v5"
        self.__access_token="aa6cb32539129acf5605793f91a1588c"

    def get_branches_list_by_repo(self,repo_name,owner_name):
        """
        获取仓库的所有分支
        :param repo_name: 仓库名称
        :param owner_name: 仓库所属空间地址(企业、组织或个人的地址
        :return:
        """
        url = f"{self.__base_url}/repos/{owner_name}/{repo_name}/branches"
        page=1
        parameters={
            "access_token":self.__access_token,
            "repo":repo_name,
            "owner":owner_name,
            "sort":"name",
            "direction":"asc",
            "page":page,
            "per_page":10
        }
        headers={
            "Content-Type":"application/json",
            "Accept":"application/json",
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
        }
        branches=[]
        while True:
            response=requests.get(url,params=parameters,headers=headers)
            if response.status_code==200:
                data=response.json()
                for branch in data:
                    branches.append(branch["name"])
                page+=1
                parameters["page"]=page
                if len(data)==0:
                    return branches
            else:
                log.error(f"request url is {url}, parameters is {parameters},headers is {headers} failed, response status code is {response.status_code}")
                return branches

    def get_repo_name_and_repo_html_url_by_org(self,org_name):
        log.info(f"begin to get openEuler repo names and repo html urls by org {org_name}...")
        url = f"{self.__base_url}/orgs/{org_name}/repos"
        page=1
        parameters={
            "access_token":"aa6cb32539129acf5605793f91a1588c",
            "org":org_name,
            "page":page,
            "per_page":10,
            "type":"all"
        }
        headers={
            "Content-Type":"application/json",
            "Accept":"application/json",
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
        }
        page=1
        log.info(f"begin to request url is {url}, parameters is {parameters},headers is {headers}...")
        while True:
            response=requests.get(url,params=parameters,headers=headers)
            if response.status_code==200:
                data=response.json()
                for repo in data:
                    yield repo["name"],repo["html_url"]
                page+=1
                parameters["page"]=page
                if len(data)==0:
                    break
            else:
                log.error(f"request url is {url}, parameters is {parameters},headers is {headers} failed, response status code is {response.status_code}")
                break


class RepoRpmParser:
    def __init__(self):
        # 支持的primary.xml压缩格式（优先级从高到低）
        self.compressed_patterns = {
            "zst": re.compile(r'primary\.xml\.zst', re.I),
            "gz": re.compile(r'primary\.xml\.gz', re.I),
            "bz2": re.compile(r'primary\.xml\.bz2', re.I)
        }
        # RPM元数据命名空间（覆盖默认命名空间+rpm前缀）
        self.ns_map = {
            "rpm": "http://linux.duke.edu/metadata/rpm",
            "default": "http://linux.duke.edu/metadata/common"
        }

    def _get_repodata_file_list(self, repodata_url: str) -> List[str]:
        """
        获取repodata目录下的文件列表
        :param repodata_url: repodata目录URL（如 https://xxx/repodata/）
        :return: 文件名称列表
        """
        try:
            resp = requests.get(repodata_url, timeout=30)
            resp.raise_for_status()
            # 适配Apache/Nginx索引页格式，提取primary.xml相关文件
            file_pattern = re.compile(r'href="([a-f0-9]+-primary\.xml(\.[a-z0-9]+)?)"')
            files = file_pattern.findall(resp.text)
            # 去重并返回完整文件名
            file_list = list({f[0] for f in files})
            log.debug(f"Found repodata files: {file_list}")
            return file_list
        except Exception as e:
            log.error(f"Failed to get repodata file list from {repodata_url}: {str(e)}")
            return []

    def _download_file(self, file_url: str, save_path: str) -> bool:
        """
        下载文件到指定路径（流式下载，支持大文件）
        :param file_url: 文件URL
        :param save_path: 本地保存路径
        :return: 下载成功返回True，失败返回False
        """
        try:
            resp = requests.get(file_url, stream=True, timeout=60)
            resp.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            log.debug(f"Downloaded file: {file_url} -> {save_path}")
            return True
        except Exception as e:
            log.error(f"Failed to download {file_url}: {str(e)}")
            return False

    def _decompress_file(self, compressed_path: str, output_path: str) -> bool:
        """
        根据文件后缀解压压缩包（支持zst/gz/bz2）
        :param compressed_path: 压缩文件路径
        :param output_path: 解压后输出路径
        :return: 解压成功返回True，失败返回False
        """
        try:
            if compressed_path.endswith('.zst'):
                with open(compressed_path, 'rb') as f_in:
                    dctx = zstd.ZstdDecompressor()
                    with open(output_path, 'wb') as f_out:
                        dctx.copy_stream(f_in, f_out)
            elif compressed_path.endswith('.gz'):
                with gzip.open(compressed_path, 'rb') as f_in:
                    with open(output_path, 'wb') as f_out:
                        f_out.write(f_in.read())
            elif compressed_path.endswith('.bz2'):
                with bz2.open(compressed_path, 'rb') as f_in:
                    with open(output_path, 'wb') as f_out:
                        f_out.write(f_in.read())
            else:
                log.error(f"Unsupported compression format: {compressed_path}")
                return False
            log.debug(f"Decompressed file: {compressed_path} -> {output_path}")
            return True
        except Exception as e:
            log.error(f"Failed to decompress {compressed_path}: {str(e)}")
            return False

    def _parse_primary_xml(self, xml_path: str) -> List[str]:
        """
        解析primary.xml文件（兼容命名空间），提取所有RPM包名并去重
        :param xml_path: primary.xml文件路径
        :return: 去重后的RPM包名列表
        """
        rpm_names = set()
        try:
            # 读取XML文件并处理编码
            with open(xml_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()

            # 解析XML（处理默认命名空间）
            root = ET.fromstring(xml_content)

            # 方案1：无命名空间的情况（如示例XML）
            packages = root.findall(".//package[@type='rpm']")
            # 方案2：带默认命名空间的情况
            if not packages:
                packages = root.findall(".//default:package[@type='rpm']",
                                        namespaces={"default": self.ns_map["default"]})

            log.debug(f"Found {len(packages)} RPM packages in primary.xml")

            # 遍历所有package节点提取name
            for pkg in packages:
                # 尝试直接找name子节点（无命名空间）
                name_elem = pkg.find("name")
                # 带默认命名空间的name节点
                if name_elem is None:
                    name_elem = pkg.find("default:name", namespaces={"default": self.ns_map["default"]})

                if name_elem is not None and name_elem.text:
                    pkg_name = name_elem.text.strip()
                    if pkg_name:  # 过滤空白包名
                        rpm_names.add(pkg_name)
                        log.debug(f"Extracted package name: {pkg_name}")

            # 转有序列表返回
            result = sorted(list(rpm_names))
            log.info(f"Extracted {len(result)} unique RPM package names")
            return result

        except ET.ParseError as e:
            log.error(f"XML parse error in {xml_path}: {str(e)}")
            return []
        except Exception as e:
            log.error(f"Failed to parse primary.xml {xml_path}: {str(e)}")
            return []

    def get_rpm_list(self, repo_url: str) -> List[str]:
        """
        从指定repo地址获取所有RPM包名列表（去重）
        核心流程：
        1. 拼接repodata目录URL
        2. 探测primary.xml或其压缩包
        3. 下载并解压（如需）
        4. 解析XML提取包名并去重
        :param repo_url: 仓库基础URL（如 https://xxx/openEuler-24.03-LTS-SP2/OS/x86_64/）
        :return: 去重后的RPM包名列表，失败返回空列表
        """
        try:
            # 步骤1：拼接repodata目录URL（处理末尾/）
            repo_url = repo_url.rstrip('/')
            repodata_url = f"{repo_url}/repodata/"
            log.info(f"Start to get RPM list from repo: {repo_url}")

            # 步骤2：获取repodata目录文件列表
            repodata_files = self._get_repodata_file_list(repodata_url)
            if not repodata_files:
                log.warning(f"No files found in repodata directory: {repodata_url}")
                return []

            # 步骤3：查找primary.xml或其压缩包
            primary_file = None
            compressed_type = None

            # 优先找未压缩的primary.xml
            for f in repodata_files:
                if f.endswith('primary.xml'):
                    primary_file = f
                    break

            # 未找到则找压缩包
            if not primary_file:
                for c_type, pattern in self.compressed_patterns.items():
                    for f in repodata_files:
                        if pattern.search(f):
                            primary_file = f
                            compressed_type = c_type
                            break
                    if primary_file:
                        break

            if not primary_file:
                log.error(f"No primary.xml (or compressed) found in {repodata_url}")
                return []
            log.info(f"Found primary file: {primary_file} (compressed type: {compressed_type or 'none'})")

            # 步骤4：临时目录处理文件（自动清理）
            with TemporaryDirectory() as tmp_dir:
                file_url = f"{repodata_url}/{primary_file}"
                local_file = os.path.join(tmp_dir, primary_file)

                # 下载文件
                if not self._download_file(file_url, local_file):
                    return []

                # 解压（如需）
                xml_path = os.path.join(tmp_dir, 'primary.xml')
                if compressed_type:
                    if not self._decompress_file(local_file, xml_path):
                        return []
                else:
                    xml_path = local_file  # 未压缩直接使用

                # 步骤5：解析XML提取包名
                rpm_names = self._parse_primary_xml(xml_path)
                return rpm_names

        except Exception as e:
            log.error(f"get rpm list from repo {repo_url} failed, error message is {str(e)}")
            return []

class OpenEuler():
    def __init__(self):
        pass

    def get_rpm_list(self,repo_url):
        try:
            return RepoRpmParser().get_rpm_list(repo_url)
        except Exception as e:
            log.error(f"get rpm list from repo {repo_url} failed, error message is {str(e)}")
            return []

    def get_openEuler_everything_rpm_list(self, os_version: str, os_arch: str):
        url=f"https://fast-mirror.isrc.ac.cn/openeuler/openEuler-{os_version}/everything/{os_arch}"
        return self.get_rpm_list(url)

    def get_openEuler_epol_rpm_list(self, os_version: str, os_arch: str):
        url = f"https://fast-mirror.isrc.ac.cn/openeuler/openEuler-{os_version}/epol/{os_arch}"
        return self.get_rpm_list(url)

    def get_openEuler_update_rpm_list(self, os_version: str, os_arch: str):
        url = f"https://fast-mirror.isrc.ac.cn/openeuler/openEuler-{os_version}/update/{os_arch}"
        return self.get_rpm_list(url)

    def get_openEuler_os_rpm_list(self, os_version: str, os_arch: str):
        url = f"https://fast-mirror.isrc.ac.cn/openeuler/openEuler-{os_version}/OS/{os_arch}"
        return self.get_rpm_list(url)

    def get_openEuler_all_rpm_list(self, os_version: str, os_arch: str):
        all_rpm_list=[]
        rs=self.get_openEuler_os_rpm_list(os_version, os_arch)
        all_rpm_list.extend(rs)
        rs=self.get_openEuler_update_rpm_list(os_version, os_arch)
        all_rpm_list.extend(rs)
        rs=self.get_openEuler_epol_rpm_list(os_version, os_arch)
        all_rpm_list.extend(rs)
        rs=self.get_openEuler_everything_rpm_list(os_version, os_arch)
        all_rpm_list.extend(rs)
        return list(set(all_rpm_list))

    def get_core_src_list(self):
        core_src_list=[]
        src_path=Path(__file__).resolve().parent / "openEuler_core_src.txt"
        try:
            with open(src_path, "r",encoding="utf-8") as f:
                for line in f.readlines():
                    if not line.strip():
                        continue
                    line_segs = line.strip().split("|")
                    if len(line_segs)>=3:
                        core_src_list.append(line_segs[2].strip())
        except Exception as e:
            log.error(f"get core src list failed, error is {e}")
        finally:
            return core_src_list


    def get_openEuler_repo_names_and_urls(
            self,
            os_version: str
    ) -> Generator[Tuple[str, str], None, None]:
        """
        从 Gitee 的 src-openEuler 组织中筛选出包含指定 openEuler 版本分支的仓库信息。

        函数通过调用 Gitee 相关接口，遍历 src-openEuler 组织下的所有仓库，
        检查仓库是否存在与目标 openEuler 版本匹配的分支，若存在则返回该仓库的名称和 HTML 地址。

        Args:
            os_version: 目标 openEuler 版本号（如 "24.03-LTS-SP2"），用于匹配仓库分支

        Yields:
            Generator[Tuple[str, str], None, None]:
                迭代返回符合条件的仓库信息元组：
                - 第一个元素：仓库名称（如 "kernel"）
                - 第二个元素：仓库的 HTML 访问地址（如 "https://gitee.com/src-openEuler/kernel"）

        Notes:
            依赖 Gitee 类的以下方法：
            - get_repo_name_and_repo_html_url_by_org(org_name: str): 用于获取指定组织下所有仓库的名称和 HTML 地址
            - get_branches_list_by_repo(repo_name: str, org_name: str): 用于获取指定仓库的所有分支名称列表
        """
        # 初始化 Gitee 接口操作实例
        log.info("正在初始化 Gitee 接口操作实例...")
        gitee = Gitee()

        # 遍历 src-openEuler 组织下的所有仓库（名称 + HTML 地址）
        for repo_name, repo_url in gitee.get_repo_name_and_repo_html_url_by_org("src-openEuler"):
            log.info(f"正在检查仓库: {repo_name}，地址: {repo_url}")

            # 获取当前仓库的所有分支列表
            branches = gitee.get_branches_list_by_repo(repo_name, "src-openEuler")
            # 处理无分支的异常情况
            if not branches:
                log.warning(f"仓库 {repo_name}（{repo_url}）未发现任何分支，已跳过")
                continue

            # 检查目标版本分支是否存在，存在则返回该仓库信息
            branch = f"openEuler-{os_version}"
            if branch in branches:
                log.info(f"仓库 {repo_name}（{repo_url}）已找到目标版本分支 {branch}")
                yield repo_name, repo_url



    def get_openEuler_core_rpm_list(self,os_version,os_arch):
        core_src_list=self.get_core_src_list()
        core_rpm_list=[]
        os_rpm2src=self.get_openEuler_os_rpm2src(os_version,os_arch)
        for rpm_name,src_name in os_rpm2src.items():
            if src_name in core_src_list and rpm_name not in core_rpm_list:
                core_rpm_list.append(rpm_name)
        return core_rpm_list


    def get_openEuler_os_rpm2src(self,os_version,os_arch):
        rpm2src_file_path=Path(__file__).resolve().parent / "pkg_info" / f"openEuler_{os_version}_{os_arch}_os.json"
        rpm2src_data=dict({})
        try:
            with open(rpm2src_file_path, "r",encoding="utf-8") as f:
                rpm2src_data = json.load(f)
        except FileNotFoundError:
            log.error(f"未找到 {rpm2src_file_path} 文件")
        except json.JSONDecodeError:
            log.error(f"{rpm2src_file_path} 文件格式错误")
        except Exception as e:
            log.error(f"{rpm2src_file_path} 文件读取错误: {str(e)}")
        finally:
            return rpm2src_data

    def get_openEuler_update_rpm2src(self,os_version,os_arch):
        rpm2src_file_path=Path(__file__).resolve().parent / "pkg_info" / f"openEuler_{os_version}_{os_arch}_update.json"
        rpm2src_data=dict({})
        try:
            with open(rpm2src_file_path, "r",encoding="utf-8") as f:
                rpm2src_data = json.load(f)
        except FileNotFoundError:
            log.error(f"未找到 {rpm2src_file_path} 文件")
        except json.JSONDecodeError:
            log.error(f"{rpm2src_file_path} 文件格式错误")
        except Exception as e:
            log.error(f"{rpm2src_file_path} 文件读取错误: {str(e)}")
        finally:
            return rpm2src_data

    def get_openEuler_everything_rpm2src(self,os_version,os_arch):
        rpm2src_file_path=Path(__file__).resolve().parent / "pkg_info" / f"openEuler_{os_version}_{os_arch}_everything.json"
        rpm2src_data=dict({})
        try:
            with open(rpm2src_file_path, "r",encoding="utf-8") as f:
                rpm2src_data = json.load(f)
        except FileNotFoundError:
            log.error(f"未找到 {rpm2src_file_path} 文件")
        except json.JSONDecodeError:
            log.error(f"{rpm2src_file_path} 文件格式错误")
        except Exception as e:
            log.error(f"{rpm2src_file_path} 文件读取错误: {str(e)}")
        finally:
            return rpm2src_data

    def get_openEuler_epol_rpm2src(self,os_version,os_arch):
        rpm2src_file_path=Path(__file__).resolve().parent / "pkg_info" / f"openEuler_{os_version}_{os_arch}_epol.json"
        rpm2src_data=dict({})
        try:
            with open(rpm2src_file_path, "r",encoding="utf-8") as f:
                rpm2src_data = json.load(f)
        except FileNotFoundError:
            log.error(f"未找到 {rpm2src_file_path} 文件")
        except json.JSONDecodeError:
            log.error(f"{rpm2src_file_path} 文件格式错误")
        except Exception as e:
            log.error(f"{rpm2src_file_path} 文件读取错误: {str(e)}")
        finally:
            return rpm2src_data

if __name__ == "__main__":

    # rpm=RepoRpmParser()
    # rs=rpm.get_rpm_list("https://fast-mirror.isrc.ac.cn/openeuler/openEuler-24.03-LTS-SP2/OS/x86_64/")
    # for elem in rs:
    #     print(elem)
    # print(f"total {len( rs)} rpms")

    # oe=OpenEuler()
    # rs=oe.get_rpm_list("https://fast-mirror.isrc.ac.cn/openeuler/openEuler-24.03-LTS-SP2/OS/x86_64/")
    # for elem in rs:
    #     print(elem)
    # print(f"total {len( rs)} rpms")

    # oe = OpenEuler()
    # rs = oe.get_openEuler_os_rpm_list("24.03-LTS-SP2", "x86_64")
    # print(f"os {len(rs)} rpms")

    # oe=OpenEuler()
    # rs=oe.get_openEuler_update_rpm_list("24.03-LTS-SP2", "x86_64")
    # print(f"os {len( rs)} rpms")

    # oe = OpenEuler()
    # rs = oe.get_openEuler_everything_rpm_list("24.03-LTS-SP2", "x86_64")
    # print(f"os {len(rs)} rpms")

    # oe = OpenEuler()
    # rs = oe.get_openEuler_all_rpm_list("24.03-LTS-SP2", "x86_64")
    # print(f"os {len(rs)} rpms")

    # oe=OpenEuler()
    # repos_generator = oe.get_openEuler_repo_names_and_urls(
    #     os_version="24.03-LTS-SP2"
    # )
    # log.info("正在获取 openEuler 24.03-LTS-SP2 x86_64 架构的仓库信息...")
    # count = 0
    # for repo_name, repo_url in repos_generator:
    #     log.info(f"正在处理仓库: {repo_name}，地址: {repo_url}")
    #     count += 1
    #     print(f"{repo_name}：{repo_url}")
    # log.info("共获取到 %d 个仓库" % count)


    # oe = OpenEuler()
    # rs = oe.get_openEuler_os_rpm2src("24.03-LTS-SP1", "x86_64")
    # print(len(rs.keys()))
    # rs = oe.get_openEuler_update_rpm2src("24.03-LTS-SP1", "x86_64")
    # print(len(rs.keys()))
    # rs=oe.get_core_src_list()
    # print(rs)

    pass

