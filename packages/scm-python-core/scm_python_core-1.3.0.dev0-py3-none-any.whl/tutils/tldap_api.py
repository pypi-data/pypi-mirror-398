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

LDAP_API_BASE_URL = "http://192.168.50.69:18084/sample/webapi"
# VAULT_PROXY_API_BASE_URL = "http://192.168.50.246:8100/v1"
LDAP_ADDR_API_URL_FIELD = "LDAP_ADDR_API_URL"
# VAULT_TEST_ROOT_TOKEN_FIELD = "VAULT_TEST_ROOT_TOKEN"
LDAP_TEST_CONTEXT_FIELD = "TEST_CONTEXT"
# USER_PROFILE = os.path.expanduser("~")
# VAULT_CLIENT_CERT = (
#     os.path.join(USER_PROFILE, ".keystore", "shao.sh.client.crt"),
#     os.path.join(USER_PROFILE, ".keystore", "shao.sh.client.key"),
# )


def ldap_api_base_url(context: dict):
    return (
        context[LDAP_ADDR_API_URL_FIELD]
        if LDAP_ADDR_API_URL_FIELD in context
        else LDAP_API_BASE_URL
    )


def ldap_context(enable_test_context=True, **kwargs) -> dict:
    context = thpe.create_env_context()
    ldap_template = thpe.load_yaml_from_install(
        f"vilink/vault-template/ldap-context", "vilink", skip_replace=True
    )
    if enable_test_context:
        if LDAP_TEST_CONTEXT_FIELD in ldap_template:
            ldap_test_context_dict = ldap_template[LDAP_TEST_CONTEXT_FIELD]
            del ldap_template[LDAP_TEST_CONTEXT_FIELD]
            for key, value in ldap_test_context_dict.items():
                ldap_template[key] = value
    else:
        if LDAP_TEST_CONTEXT_FIELD in ldap_template:
            del ldap_template[LDAP_TEST_CONTEXT_FIELD]

    tcontext.replace_object(context, ldap_template)
    extends_dict = tcontext.deep_merge({}, ldap_template)
    for key, value in kwargs.items():
        if key.endswith("_LIST") and isinstance(value, list):
            key = f'list::{key.replace("_LIST", "")}'
        extends_dict[key] = value
    return tcontext.deep_merge(context, extends_dict)


def ldap_header(ldap_template={}, context={}):
    headers = {}
    if "api-headers" in ldap_template:
        api_headers: list[str] = ldap_template["api-headers"]
        for header in api_headers:
            key, value = header.split(":")
            headers[key] = value.lstrip()
    return headers


def ldap_request(
    context: dict, ldap_template_key: str, data_hander=None, filed_name: str = ""
):
    ldap_template = thpe.load_yaml_from_install(
        f"vilink/vault-template/{ldap_template_key}", "vilink", skip_replace=True
    )
    if "ldap-context" in ldap_template:  # type: ignore
        for key, value in ldap_template["ldap-context"].items():  # type: ignore
            context[key] = value
    request_method = ldap_template["X"]  # type: ignore
    if request_method == "POST":
        return ldap_post(
            context=context, data_hander=data_hander, ldap_template=ldap_template
        )
    # if request_method == "PUT":
    #     return vault_put(
    #         context=context, data_hander=data_hander, ldap_template=ldap_template
    #     )
    if request_method == "GET":
        return ldap_get(
            context=context, filed_name=filed_name, ldap_template=ldap_template
        )
    # if request_method == "LIST":
    #     return vault_list(
    #         context=context, filed_name=filed_name, ldap_template=ldap_template
    #     )
    # if request_method == "DELETE":
    #     return vault_delete(context=context, ldap_template=ldap_template)


def ldap_post(context: dict, ldap_template_key="", data_hander=None, ldap_template={}):
    if not ldap_template:
        ldap_template = thpe.load_yaml_from_install(
            f"vilink/vault-template/{ldap_template_key}", "vilink", skip_replace=True
        )
    tcontext.replace_object(context, ldap_template)
    api_cmd = ldap_template["api-cmd"]  # type: ignore
    runtime_ldap_api_base_url = ldap_api_base_url(context=context)
    url = f"{runtime_ldap_api_base_url}/{api_cmd}"
    data = ldap_template["body"] if "body" in ldap_template else None  # type: ignore
    if data_hander:
        data_hander(context, data)
    print("-----ldap_post", url, data)
    response = thpe.get_request_session().post(
        url,
        headers=ldap_header(ldap_template, context=context),
        data=json.dumps(data) if data else None,
    )
    if tl.PRINT_DETAILS:
        print(response.request.headers)
        print(response.status_code)
    if response.status_code in (200, 201, 202, 204):
        return response.json() if response.text else response
    else:
        raise Exception(response.text)  # response.text


def ldap_get(
    context: dict, ldap_template_key="", filed_name: str = "", ldap_template={}
):
    if not ldap_template:
        ldap_template = thpe.load_yaml_from_install(
            f"vilink/vault-template/{ldap_template_key}", "vilink", skip_replace=True
        )
    tcontext.replace_object(context, ldap_template)
    api_cmd = ldap_template["api-cmd"]  # type: ignore
    # Known Issues: ssz,2025.10.25 支持绝对路径
    runtime_ldap_api_base_url = ldap_api_base_url(context=context)
    url = api_cmd if "://" in api_cmd else f"{runtime_ldap_api_base_url}/{api_cmd}"
    if tl.PRINT_DETAILS:
        log.info(f"{url}")
    print("---vault_get", url)
    response = thpe.get_request_session().get(
        url,
        headers=ldap_header(ldap_template, context=context),
    )
    if response.status_code in (200, 201):
        return response.text
        # return response.json()[filed_name] if filed_name else response.json()
    else:
        raise Exception(response.text)
