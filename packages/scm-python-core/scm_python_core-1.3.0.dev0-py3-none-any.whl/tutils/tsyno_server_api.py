import tlog.tlogging as tl
import requests
import json
import os
import tlog.tlogging as tl
import tio.tfile as tf
import tio.tshell as ts
import tutils.thpe as thpe
import tutils.context_opt as tcontext
import base64, hashlib
from tutils.tvault_api import vault_secret


log = tl.log
SYNO_SID_CACHE_FILE = os.path.join(os.path.expanduser("~"), ".syno_sid")

SYNO_SERVER_API_BASE_URL = "http://192.168.50.236:5000/webapi"
SYNO_SID = "SYNO_SID"
SYNO_USER = "SYNO_USER"
SYNO_PASSWORD_KEY = "SYNO_PASSWORD_KEY"
SYNO_RESPONSE_SUCCESS = "success"
SYNO_OFFSET = "SYNO_OFFSET"
SYNO_LIMIT = "SYNO_LIMIT"
SYNO_OBJECT_ID = "SYNO_OBJECT_ID"


def syno_context(**kwargs):
    login_context = thpe.load_yaml_from_install(
        f"vilink/syno-template/login-context", "vilink", skip_replace=True
    )
    login_context = tcontext.deep_merge(login_context, kwargs)
    context = thpe.create_env_context()
    syno_context = tcontext.deep_merge(context, login_context)
    if SYNO_SID not in syno_context:
        if os.path.exists(SYNO_SID_CACHE_FILE):
            syno_context[SYNO_SID] = tf.readlines(SYNO_SID_CACHE_FILE)[0]
    if SYNO_SID in syno_context:
        syno_context[SYNO_OFFSET] = 0
        syno_context[SYNO_LIMIT] = 1
        data = syno_get(
            syno_context,
            "note-list",
        )
        if SYNO_RESPONSE_SUCCESS in data:
            return syno_context
    data = syno_get(
        syno_context,
        "note-login",
        is_login=True,
    )
    if SYNO_RESPONSE_SUCCESS in data:
        syno_context[SYNO_SID] = data["data"]["sid"]
        tf.writelines(SYNO_SID_CACHE_FILE, [syno_context[SYNO_SID]])
        return syno_context
    else:
        raise Exception("Can't get sid in synology")


def openssl_key_iv(password, salt, key_len=32, iv_len=16):
    """兼容 OpenSSL EVP_BytesToKey"""
    data = b""
    prev = b""
    while len(data) < (key_len + iv_len):
        prev = hashlib.md5(prev + password + salt).digest()
        data += prev
    return data[:key_len], data[key_len : key_len + iv_len]


def decrypt_note(encrypted_b64, passphrase):
    from Crypto.Cipher import AES

    data = base64.b64decode(encrypted_b64)
    assert data.startswith(b"Salted__")
    salt = data[8:16]
    key, iv = openssl_key_iv(passphrase.encode(), salt)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(data[16:])
    # 去掉 PKCS#7 padding
    pad_len = decrypted[-1]
    return decrypted[:-pad_len].decode("utf-8")


def syno_get(context: dict, syno_template: str, is_login=False):
    api_cmd = thpe.load_yaml_from_install(
        f"vilink/syno-template/{syno_template}", "vilink", env_context=context
    )
    print(api_cmd, api_cmd)
    if SYNO_SID not in context and not is_login:
        raise ValueError(f"{SYNO_SID} is not set in context")
    if not is_login:
        url = f"{SYNO_SERVER_API_BASE_URL}/{api_cmd}&_sid={context[SYNO_SID]}"
    else:
        url = f"{SYNO_SERVER_API_BASE_URL}/{api_cmd}"
    response = thpe.get_request_session().get(
        url,
    )  # verify=False 对应 -k
    if response.status_code in (200, 201):
        data = response.json()
        if SYNO_RESPONSE_SUCCESS in data and not data[SYNO_RESPONSE_SUCCESS]:
            print(f"SYNO API FAILURE:: {api_cmd}", data)
        return data
    else:
        raise Exception(response.text)


def syno_note_content_handler(
    context: dict, syno_template: str, object_id: str, encrypt=False, dataReturn=False
):
    context[SYNO_OBJECT_ID] = object_id
    json_response = syno_get(
        context,
        syno_template,
    )
    data = json_response["data"]
    if dataReturn or "content" not in data:
        return data
    content = data["content"]  # 从 API 返回的 content
    if encrypt:
        passphrase = vault_secret("WIFI_PASSWORD_OF_SSZ")
        return decrypt_note(content, passphrase)
    else:
        return content


def syno_note_content(context: dict, object_id: str, encrypt=False, dataReturn=False):
    return syno_note_content_handler(
        context, "note-content", object_id, encrypt, dataReturn
    )


def syno_note_notebook_content(context: dict, object_id: str):
    return syno_note_content_handler(context, "note-notebook-content", object_id)


# def syno_note_folder_content(context: dict, object_id: str, encrypt=False):
#     return syno_note_content_handler(context, "note-folder-content", object_id)


def syno_note_list_handler(
    context: dict, syno_template: str, item_field_name="notes", offset=0, limit=2
):
    context[SYNO_OFFSET] = offset
    context[SYNO_LIMIT] = limit
    json_response = syno_get(
        context,
        syno_template,
    )
    data = json_response["data"]
    return data[item_field_name] if item_field_name in data else data


def syno_note_list(context: dict, offset=0, limit=2):
    return syno_note_list_handler(context, "note-list", "notes", offset, limit)


def syno_note_latest_list(context: dict, offset=0, limit=2):
    return syno_note_list_handler(context, "note-latest-list", "notes", offset, limit)


def syno_note_notebook_list(context: dict, offset=0, limit=2):
    return syno_note_list_handler(
        context, "note-notebook-list", "notebooks", offset, limit
    )


def syno_webapi_list(context: dict) -> dict:
    json_response = syno_get(
        context,
        "webapi-list",
    )
    data = json_response["data"]
    return data


def syno_note_stack_list(context: dict, offset=0, limit=2):
    return syno_note_list_handler(context, "note-stack-list", "stacks", offset, limit)
