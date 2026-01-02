import tlog.tlogging as tl
import os, datetime, re, requests
import fnmatch
import hashlib
import shutil
import yaml
import tempfile
import tutils.thpe as thpe
import tutils.tstr as tstr

import xml.etree.ElementTree as ET
import chardet
import codecs
from pathlib import Path
import logging
import http.client as http_client

log = tl.log if hasattr(tl, "log") else None

if tl.PRINT_DETAILS:
    http_client.HTTPConnection.debuglevel = 1
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.DEBUG)
    logging.getLogger("urllib3").propagate = True

GITLAB_API_BASE_URL = "https://de.vicp.net:58443/api/v4"
GITLAB_API_EMBED_FILE_EXT_LIST = [".xml", ".yaml", ".json"]


def gitlab_api_list(url: str, is_template_file=True):
    """
    url format https://de.vicp.net:58443/Shao/doc-template/-/raw/main/template/yaml-antd
    url 也可能是个文件,如何判断是否为文件采用预定义的ext来区分
    known issues: 2014-08-20 预定义的文件名不能作为文件夹了,这个可以接受
    """
    # 处理url是文件
    for embed_file_ext in GITLAB_API_EMBED_FILE_EXT_LIST:
        if url.endswith(embed_file_ext):
            file_path = os.path.basename(url)
            return {
                file_path: f"${{::TEMPLATE_FILE}}={url}" if is_template_file else url
            }
    foo = url.split("/-/")
    first_url = foo[0]
    second_url = foo[1]
    git_repo_name = first_url[tstr.find_nth_occurrence(first_url, "/", 3) + 1 :]
    # 设置 GitLab 项目的相关信息
    PROJECT_ID = gitlab_api_search_project_id(git_repo_name)
    ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"  # 替换为你的 GitLab 访问令牌
    REF = second_url.split("/")[1]  # 分支名称
    PATH = second_url[
        tstr.find_nth_occurrence(second_url, "/", 2) + 1 :
    ]  # 要列出文件的路径

    # 构建 API 请求的 URL
    api_url = f"{GITLAB_API_BASE_URL}/projects/{PROJECT_ID}/repository/tree"
    # print(f"{git_repo_name} {REF} {PATH}")

    # 设置请求参数
    params = {
        "ref": REF,
        "path": PATH,
        "per_page": 100,
        "pagination": "keyset",
        "recursive": True,
    }  # 递归列出所有文件

    # 设置请求头"PRIVATE-TOKEN": ACCESS_TOKEN
    headers = {}
    # 列出所有文件的 URL
    base_raw_url = f"{first_url}/-/raw/{REF}/{PATH}"
    result_files: dict[str, str] = {}

    # type=tree 目录, type=blob 文件
    while True:
        response = thpe.get_request_session().get(
            api_url, headers=headers, params=params
        )
        if tl.PRINT_DETAILS:
            print(response.request.headers)
            print(response.status_code)
        response.raise_for_status()

        # 解析响应数据
        files = response.json()
        for file in files:
            file_path = file["path"].replace(PATH + "/", "")
            file_url = f"{base_raw_url}/{file_path}"
            file_type = file["type"]
            if file_type == "blob":
                result_files[file_path] = (
                    f"${{::TEMPLATE_FILE}}={file_url}" if is_template_file else file_url
                )
        if "next" in response.links:
            after_page = response.links["next"]["url"].split("&page=")[-1]
            params["page"] = after_page[: after_page.find("&")]
        else:
            break
    return result_files


def gitlab_api_search_project_id(git_repo_name: str):

    # 设置 GitLab API 的基本信息
    ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"  # 替换为你的 GitLab 访问令牌
    PROJECT_NAME = git_repo_name[git_repo_name.find("/") + 1 :]  # 你要查询的项目名称

    # 构建 API 请求的 URL
    api_url = f"{GITLAB_API_BASE_URL}/projects"

    # 设置请求参数
    params = {"search": PROJECT_NAME}

    # 设置请求头"PRIVATE-TOKEN": ACCESS_TOKEN
    headers = {}

    # 发出请求
    response = requests.get(api_url, headers=headers, params=params)
    response.raise_for_status()

    # 解析响应数据
    projects = response.json()

    # 查找匹配的项目并打印项目 ID
    for project in projects:
        if project["path_with_namespace"] == git_repo_name:
            # print(f"Project Name: {project['name']}, Project ID: {project['id']}")
            return project["id"]
    else:
        print(f"{PROJECT_NAME} not found path_with_namespace {git_repo_name}")
        raise Exception("No matching project found.")


def gitlab_api_search_project_by_pattern(git_repo_name: str, pattern: str):

    PROJECT_NAME = git_repo_name[git_repo_name.find("/") + 1 :]  # 你要查询的项目名称
    api_url = f"{GITLAB_API_BASE_URL}/projects"
    params = {"search": PROJECT_NAME, "per_page": 100}
    headers = {}
    response = requests.get(api_url, headers=headers, params=params)
    response.raise_for_status()
    projects = response.json()

    for project in projects:
        print(pattern.replace("${NAME}", project["name"]))
