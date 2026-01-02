import sys, re, os, requests
import tlog.tlogging as tl
import tio.tfile as tf
import tio.tshell as ts
import tutils.thpe as thpe
import tutils.tgitlab_api as tgitlab_api
import tutils.context_opt as tcontext

log = tl.log


def exercise_lib_gitlab_api_handler():
    log.info("exercise_lib_gitlab_api_handler")
    print(
        tgitlab_api.gitlab_api_list(
            "https://de.vicp.net:58443/Shao/doc-template/-/raw/main/template/misc/solution-meta"
        )
    )


def exercise_search_project_id(git_repo_name: str):

    # 设置 GitLab API 的基本信息
    GITLAB_BASE_URL = "https://de.vicp.net:58443/api/v4"
    ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"  # 替换为你的 GitLab 访问令牌
    PROJECT_NAME = "doc-template"  # 你要查询的项目名称

    # 构建 API 请求的 URL
    api_url = f"{GITLAB_BASE_URL}/projects"

    # 设置请求参数
    params = {"search": PROJECT_NAME}

    # 设置请求头"PRIVATE-TOKEN": ACCESS_TOKEN
    headers = {}

    # 发出请求
    response = requests.get(
        api_url, headers=headers, params=params, verify=thpe.SSZ_ROOT_CA
    )
    response.raise_for_status()

    # 解析响应数据
    projects = response.json()

    # 查找匹配的项目并打印项目 ID
    for project in projects:
        if project["path_with_namespace"] == git_repo_name:
            print(f"Project Name: {project['name']}, Project ID: {project['id']}")
            return project["id"]
    else:
        raise Exception("No matching project found.")
