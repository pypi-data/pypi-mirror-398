import re
import os
import json
import logging
import gzip
import bz2
import zstandard as zstd
import xml.etree.ElementTree as ET
from tempfile import TemporaryDirectory
from pathlib import Path
import requests
import traceback
import functools
import inspect
from typing import Callable,List, Any, Generator, Tuple
import requests.exceptions

log=logging.getLogger(__name__)

def enter_and_leave_function(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
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
                exc_info=False
            )
            raise

    return wrapper

class Gitee():
    def __init__(self):
        self.__base_url= "https://gitee.com/api/v5"
        self.__access_token="aa6cb32539129acf5605793f91a1588c"

    def get_branches_list_by_repo(self,repo_name,owner_name):
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
        self.compressed_patterns = {
            "zst": re.compile(r'primary\.xml\.zst', re.I),
            "gz": re.compile(r'primary\.xml\.gz', re.I),
            "bz2": re.compile(r'primary\.xml\.bz2', re.I)
        }
        self.ns_map = {
            "rpm": "http://linux.duke.edu/metadata/rpm",
            "default": "http://linux.duke.edu/metadata/common"
        }

    def _get_repodata_file_list(self, repodata_url: str) -> List[str]:
        try:
            resp = requests.get(repodata_url, timeout=30)
            resp.raise_for_status()
            file_pattern = re.compile(r'href="([a-f0-9]+-primary\.xml(\.[a-z0-9]+)?)"')
            files = file_pattern.findall(resp.text)
            file_list = list({f[0] for f in files})
            log.debug(f"Found repodata files: {file_list}")
            return file_list
        except Exception as e:
            log.error(f"Failed to get repodata file list from {repodata_url}: {str(e)}")
            return []

    def _download_file(self, file_url: str, save_path: str) -> bool:
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
        rpm_names = set()
        try:
            with open(xml_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            root = ET.fromstring(xml_content)
            packages = root.findall(".//package[@type='rpm']")
            if not packages:
                packages = root.findall(".//default:package[@type='rpm']",
                                        namespaces={"default": self.ns_map["default"]})

            log.debug(f"Found {len(packages)} RPM packages in primary.xml")
            for pkg in packages:
                name_elem = pkg.find("name")
                if name_elem is None:
                    name_elem = pkg.find("default:name", namespaces={"default": self.ns_map["default"]})
                if name_elem is not None and name_elem.text:
                    pkg_name = name_elem.text.strip()
                    if pkg_name:
                        rpm_names.add(pkg_name)
                        log.debug(f"Extracted package name: {pkg_name}")
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
        try:
            repo_url = repo_url.rstrip('/')
            repodata_url = f"{repo_url}/repodata/"
            log.info(f"Start to get RPM list from repo: {repo_url}")
            repodata_files = self._get_repodata_file_list(repodata_url)
            if not repodata_files:
                log.warning(f"No files found in repodata directory: {repodata_url}")
                return []
            primary_file = None
            compressed_type = None
            for f in repodata_files:
                if f.endswith('primary.xml'):
                    primary_file = f
                    break
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

            with TemporaryDirectory() as tmp_dir:
                file_url = f"{repodata_url}/{primary_file}"
                local_file = os.path.join(tmp_dir, primary_file)

                if not self._download_file(file_url, local_file):
                    return []

                xml_path = os.path.join(tmp_dir, 'primary.xml')
                if compressed_type:
                    if not self._decompress_file(local_file, xml_path):
                        return []
                else:
                    xml_path = local_file

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
        log.info("正在初始化 Gitee 接口操作实例...")
        gitee = Gitee()
        for repo_name, repo_url in gitee.get_repo_name_and_repo_html_url_by_org("src-openEuler"):
            log.info(f"正在检查仓库: {repo_name}，地址: {repo_url}")
            branches = gitee.get_branches_list_by_repo(repo_name, "src-openEuler")
            if not branches:
                log.warning(f"仓库 {repo_name}（{repo_url}）未发现任何分支，已跳过")
                continue
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

