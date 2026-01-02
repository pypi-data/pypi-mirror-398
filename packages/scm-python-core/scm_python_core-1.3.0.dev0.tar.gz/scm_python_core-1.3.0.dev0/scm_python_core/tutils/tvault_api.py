import tlog.tlogging as tl
import os, platform
import json
import tutils.context_opt as tcontext
import tutils.thpe as thpe
import tio.tfile as tf

import logging
import http.client as http_client

log = tl.log if hasattr(tl, "log") else None
# import urllib3

# Known Issues: ssz,2025-10-25, workaround C:\Python314\Lib\site-packages\urllib3\connectionpool.py:1097: InsecureRequestWarning: Unverified HTTPS request is being made to host 'nas246.shao.sh'. Adding certificate verification is strongly advised. See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#tls-warnings
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if tl.PRINT_DETAILS:
    http_client.HTTPConnection.debuglevel = 1
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.DEBUG)
    logging.getLogger("urllib3").propagate = True

VAULT_API_BASE_URL = "https://nas246.shao.sh:8200/v1"
VAULT_PROXY_API_BASE_URL = "http://192.168.50.246:8100/v1"
VAULT_ADDR_API_URL_FIELD = "VAULT_ADDR_API_URL"
VAULT_TEST_ROOT_TOKEN_FIELD = "VAULT_TEST_ROOT_TOKEN"
VAULT_TEST_CONTEXT_FIELD = "TEST_CONTEXT"
USER_PROFILE = os.path.expanduser("~")
VAULT_CLIENT_CERT = (
    os.path.join(USER_PROFILE, ".keystore", "shao.sh.client.crt"),
    os.path.join(USER_PROFILE, ".keystore", "shao.sh.client.key"),
)


def vault_server_authorization_header(vault_template={}, context={}):
    api_cmd = vault_template["api-cmd"]
    if api_cmd.startswith(VAULT_PROXY_API_BASE_URL):
        return {}
    if VAULT_TEST_ROOT_TOKEN_FIELD in context:
        token = context[VAULT_TEST_ROOT_TOKEN_FIELD]
    else:
        token = (
            vault_template["vault-token"]
            if "vault-token" in vault_template
            else tf.dotenv("vault-root-token")
        )
    headers = {
        "X-Vault-Token": token,
    }
    return headers


def vault_context(enable_test_context=True, **kwargs) -> dict:
    context = thpe.create_env_context()
    vault_template = thpe.load_yaml_from_install(
        f"vilink/vault-template/vault-context", "vilink", skip_replace=True
    )
    if enable_test_context:
        if VAULT_TEST_CONTEXT_FIELD in vault_template:
            vault_test_context_dict = vault_template[VAULT_TEST_CONTEXT_FIELD]
            del vault_template[VAULT_TEST_CONTEXT_FIELD]
            for key, value in vault_test_context_dict.items():
                vault_template[key] = value
    else:
        if VAULT_TEST_CONTEXT_FIELD in vault_template:
            del vault_template[VAULT_TEST_CONTEXT_FIELD]

    tcontext.replace_object(context, vault_template)
    extends_dict = tcontext.deep_merge({}, vault_template)
    for key, value in kwargs.items():
        if key.endswith("_LIST") and isinstance(value, list):
            key = f'list::{key.replace("_LIST", "")}'
        extends_dict[key] = value
    return tcontext.deep_merge(context, extends_dict)


def vault_get_sys_keys():
    return thpe.load_yaml_from_install(
        f"vilink/vault-template/vault-sys-keys", "vilink", skip_replace=True
    )


JWT_CLIENT_TOKEN_FILE = (
    os.path.join("/sh", "lib", "jwt_client_token.txt")
    if "Linux" == platform.system()
    else os.path.join(USER_PROFILE, "jwt_client_token.txt")
)


def vault_id(key: str):
    return vault_secret_request(key, "id")


def vault_secret(key: str):
    return vault_secret_request(key, "password")


def vault_secret_with_root_token(key: str):
    return vault_secret_request(key, "password", use_root_token=True)


def vault_secret_request(key: str, result_field: str, use_root_token=False):
    """retrieve the secret from vault server
    if result is empty, the secret of key is missing in the vault server

    Args:
        key (str): secret key

    Returns:
        str: the secret text
    """
    vault_app_name = "ssz"
    if "VAULT_APP_NAME" in os.environ:
        vault_app_name = os.getenv("VAULT_APP_NAME")
    # Known Issues: ssz,2025.10.25 没有vault_client_token同步的优先用vault proxy
    if os.path.exists(JWT_CLIENT_TOKEN_FILE) or os.path.exists(
        os.path.join(USER_PROFILE, ".env")
    ):
        vault_client_token = (
            tf.readlines(JWT_CLIENT_TOKEN_FILE)[0]
            if os.path.exists(JWT_CLIENT_TOKEN_FILE)
            else "${dotenv::'vault_client_token'}"
        )
        if use_root_token:
            vault_template = {
                "api-cmd": f"secret/data/{vault_app_name}/${{USER_NAME}}",
            }
        else:
            vault_template = {
                "vault-token": vault_client_token,
                "api-cmd": f"secret/data/{vault_app_name}/${{USER_NAME}}",
            }
    else:
        vault_template = {
            "api-cmd": f"{VAULT_PROXY_API_BASE_URL}/secret/data/{vault_app_name}/${{USER_NAME}}",
        }
    try:
        return vault_get(
            context=vault_context(False, USER_NAME=key),
            vault_template=vault_template,
            filed_name="data",
        )["data"][result_field]
    except Exception as e:
        error_message = str(e).strip()
        # Known Issues: ssz, 2025.10.25, 暂时先用出错信息来判别有没有密码存在
        if '{"errors":[]}' == error_message:
            return ""
        log.error(error_message)
        return key


def vault_request(
    context: dict, vault_template_key: str, data_hander=None, filed_name: str = ""
):
    vault_template = thpe.load_yaml_from_install(
        f"vilink/vault-template/{vault_template_key}", "vilink", skip_replace=True
    )
    if "vault-context" in vault_template:
        for key, value in vault_template["vault-context"].items():
            context[key] = value
    request_method = vault_template["X"]  # type: ignore
    if request_method == "POST":
        return vault_post(
            context=context, data_hander=data_hander, vault_template=vault_template
        )
    if request_method == "PUT":
        return vault_put(
            context=context, data_hander=data_hander, vault_template=vault_template
        )
    if request_method == "GET":
        return vault_get(
            context=context, filed_name=filed_name, vault_template=vault_template
        )
    if request_method == "LIST":
        return vault_list(
            context=context, filed_name=filed_name, vault_template=vault_template
        )
    if request_method == "DELETE":
        return vault_delete(context=context, vault_template=vault_template)


def vault_post(
    context: dict, vault_template_key="", data_hander=None, vault_template={}
):
    if not vault_template:
        vault_template = thpe.load_yaml_from_install(
            f"vilink/vault-template/{vault_template_key}", "vilink", skip_replace=True
        )
    tcontext.replace_object(context, vault_template)
    api_cmd = vault_template["api-cmd"]  # type: ignore
    runtime_vault_api_base_url = vault_api_base_url(context=context)
    url = f"{runtime_vault_api_base_url}/{api_cmd}"
    data = vault_template["body"] if "body" in vault_template else None  # type: ignore
    if data_hander:
        data_hander(context, data)
    print("-----vault_post", url, data)
    response = thpe.get_request_session().post(
        url,
        headers=vault_server_authorization_header(vault_template, context=context),
        data=json.dumps(data) if data else None,
        cert=VAULT_CLIENT_CERT,
    )
    if tl.PRINT_DETAILS:
        print(response.request.headers)
        print(response.status_code)
    if response.status_code in (200, 201, 202, 204):
        return response.json() if response.text else response
    else:
        raise Exception(response.text)  # response.text


def vault_put(
    context: dict, vault_template_key="", data_hander=None, vault_template={}
) -> bool:
    if not vault_template:
        vault_template = thpe.load_yaml_from_install(
            f"vilink/vault-template/{vault_template_key}", "vilink", skip_replace=True
        )
    tcontext.replace_object(context, vault_template)
    api_cmd = vault_template["api-cmd"]  # type: ignore
    runtime_vault_api_base_url = vault_api_base_url(context=context)
    url = f"{runtime_vault_api_base_url}/{api_cmd}"
    data = vault_template["body"] if "body" in vault_template else None  # type: ignore
    if data_hander:
        data_hander(context, data)
    print("-----vault_put", api_cmd, data)
    response = thpe.get_request_session().put(
        url,
        headers=vault_server_authorization_header(),
        json=data,
        cert=VAULT_CLIENT_CERT,
    )
    if response.status_code in (200, 204):
        return True
    else:
        raise Exception(response.text)


def vault_api_base_url(context: dict):
    return (
        context[VAULT_ADDR_API_URL_FIELD]
        if VAULT_ADDR_API_URL_FIELD in context
        else VAULT_API_BASE_URL
    )


def vault_get(
    context: dict, vault_template_key="", filed_name: str = "", vault_template={}
):
    if not vault_template:
        vault_template = thpe.load_yaml_from_install(
            f"vilink/vault-template/{vault_template_key}", "vilink", skip_replace=True
        )
    tcontext.replace_object(context, vault_template)
    api_cmd = vault_template["api-cmd"]  # type: ignore
    # Known Issues: ssz,2025.10.25 支持绝对路径
    runtime_vault_api_base_url = vault_api_base_url(context=context)
    url = api_cmd if "://" in api_cmd else f"{runtime_vault_api_base_url}/{api_cmd}"
    if tl.PRINT_DETAILS:
        log.info(f"{url}")
    print("---vault_get", url)
    response = thpe.get_request_session().get(
        url,
        headers=vault_server_authorization_header(vault_template, context),
        cert=VAULT_CLIENT_CERT,
    )
    if response.status_code in (200, 201):
        return response.json()[filed_name] if filed_name else response.json()
    else:
        raise Exception(response.text)


def vault_list(
    context: dict, vault_template_key="", filed_name: str = "", vault_template={}
):
    if not vault_template:
        vault_template = thpe.load_yaml_from_install(
            f"vilink/vault-template/{vault_template_key}", "vilink", skip_replace=True
        )
    tcontext.replace_object(context, vault_template)
    api_cmd = vault_template["api-cmd"]  # type: ignore
    runtime_vault_api_base_url = vault_api_base_url(context=context)
    url = f"{runtime_vault_api_base_url}/{api_cmd}"
    if tl.PRINT_DETAILS:
        log.info(f"{url}")
    response = thpe.get_request_session().request(
        "LIST",
        url,
        headers=vault_server_authorization_header(context=context),
        cert=VAULT_CLIENT_CERT,
    )
    if tl.PRINT_DETAILS:
        print(response.request.headers)
        print(response.status_code)
    if response.status_code in (200, 201):
        return response.json()[filed_name] if filed_name else response.json()
    else:
        raise Exception(response.text)


def vault_delete(context: dict, vault_template_key="", vault_template={}):
    if not vault_template:
        vault_template = thpe.load_yaml_from_install(
            f"vilink/vault-template/{vault_template_key}", "vilink", skip_replace=True
        )
    tcontext.replace_object(context, vault_template)
    api_cmd = vault_template["api-cmd"]  # type: ignore
    runtime_vault_api_base_url = vault_api_base_url(context=context)
    url = f"{runtime_vault_api_base_url}/{api_cmd}"
    if tl.PRINT_DETAILS:
        log.info(f"{url}")
    response = thpe.get_request_session().request(
        "DELETE",
        url,
        headers=vault_server_authorization_header(context=context),
        cert=VAULT_CLIENT_CERT,
    )
    if tl.PRINT_DETAILS:
        print(response.request.headers)
        print(response.status_code)
    if response.status_code in (200, 201, 204):
        return response.text
    else:
        raise Exception(response.text)
