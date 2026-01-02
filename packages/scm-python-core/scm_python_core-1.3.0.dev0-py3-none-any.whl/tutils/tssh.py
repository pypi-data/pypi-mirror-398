import yaml
import sys, re, os
import socket
import tlog.tlogging as tl
import paramiko
import time
import glob
from scp import SCPClient
import tio.tfile as tf
import tutils.context_opt as tcontext
from typing import Callable, Union, Literal

log = tl.log
last_time = time.time()
last_sent = 0
last_rate = 0
sshcli_authorizations = {}


def initLastSent():
    global last_sent, last_time, last_rate
    last_time = time.time()
    last_sent = 0
    last_rate = 0


def getSendRate(sent):
    global last_sent, last_time, last_rate
    if sent < last_sent:
        initLastSent()
    current_time = time.time()
    gap = current_time - last_time
    if gap < 1:
        return last_rate, False
    rate = float(sent - last_sent) / 1024 / gap
    last_rate = rate
    last_sent = sent
    last_time = current_time
    return rate, True


"""
这个应该在cli初始化前显式调用
需要 hardcode
"""


def init_sshcli(sshcli_root={}):
    global sshcli_authorizations
    if sshcli_root and "authorizations" in sshcli_root:
        sshcli_authorizations = sshcli_root["authorizations"]


def parse_remote_path(remote):
    usr = "root"
    passwd = None
    if "@" in remote:
        usr = remote[0 : remote.find("@")]
        remote = remote[remote.find("@") + 1 :]
    host = remote[0 : remote.find(":")]
    remote_path = remote[remote.find(":") + 1 :].replace("//", "/")
    port = 22

    def ____host_match(authorization_hosts):
        if host in authorization_hosts:
            return True
        #  re.match(r'^\w', x)
        for inner_host in authorization_hosts:
            if re.match(f"{inner_host}", host):
                return True
        return False

    for authorization in sshcli_authorizations:
        # alias有可能没有配置
        alias = authorization["alias"] if "alias" in authorization else ""
        if usr == authorization["usr"] and (
            host == alias or ____host_match(authorization["host"])
        ):
            if "passwd" in authorization:
                passwd = authorization["passwd"]
            if "port" in authorization:
                port = authorization["port"]
            if host == alias:
                host = authorization["host"][0]
            break
    return usr, passwd, port, host, remote_path


def progress4(filename, size, sent, peername):
    # def 2 seconds for filter the fast file copy
    if time.time() - last_time < 2:
        return
    changeLine = "\r\n" if sent >= size else "\r"
    strFilename = filename if isinstance(filename, str) else filename.decode()
    rate, allowPresent = getSendRate(sent)
    # if allowPresent:
    sys.stdout.write(
        "(%s:%s) %60s: %6.2f%%  %10d KB %10.2f KB/s %s"
        % (
            peername[0],
            peername[1],
            strFilename,
            float(sent) / float(size) * 100,
            sent / 1024,
            rate,
            changeLine,
        )
    )


def ssh(
    host: str,
    passwd: Union[str, None] = None,
    cmd="ls -l",
    port=22,
    usr="root",
    exit=False,
):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, port=port, username=usr, password=passwd)
    stdin, stdout, stderr = client.exec_command(cmd)
    result = stdout.read().decode("utf-8")
    client.close()
    if exit and result:
        log.info(cmd + " output is not empty, so exit 1")
        sys.exit(1)
    return result


def put(remote, passwd=None, local="help", port=22, recursive=False):
    usr, passwd1, port, host, remotePath = parse_remote_path(remote)
    if not passwd:
        passwd = passwd1
    # print('put', local, remotePath, host, port, usr, passwd)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, port=port, username=usr, password=passwd, timeout=3)
    # transport = client.get_transport()
    # sftp_put_dir(transport, local, remotePath)
    # scp = SCPClient(ssh.get_transport(), progress4=progress4)
    with SCPClient(client.get_transport(), progress4=progress4) as scpclient:
        global last_sent, last_time
        last_time = time.time()
        last_sent = 0
        local_exists = os.path.exists(local)
        # 使用log.info过多,在多级进程调用会导致父进程死锁
        # log.info(f"local={local} exists={local_exists}")
        # print(f'{local} exists={local_exists}')
        for path in glob.glob(local):
            log.info(f"scpclient.put {path} {remotePath}")
            # print(f'scpclient.put {path} {remotePath}')
            scpclient.put(path, remotePath, recursive=recursive, preserve_times=True)
    client.close()


def get(remote, passwd=None, local="help", port=22, recursive=False):
    usr, passwd1, port, host, remotePath = parse_remote_path(remote)
    if not passwd:
        passwd = passwd1
    # print('get', local, remotePath, host, port, usr, passwd)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, port=port, username=usr, password=passwd, timeout=3)
    # transport = client.get_transport()
    # sftp_put_dir(transport, local, remotePath)
    # scp = SCPClient(ssh.get_transport(), progress4=progress4)
    # 需要在get_transport()中添加清理(sanitize), 否则，通配符将按字面意义处理.
    with SCPClient(
        client.get_transport(), progress4=progress4, sanitize=lambda x: x
    ) as scpclient:
        global last_sent, last_time
        last_time = time.time()
        last_sent = 0
        scpclient.get(remotePath, local, recursive=recursive, preserve_times=True)
    client.close()


def save_vilink_meta(meta, root="."):
    current_path = os.path.abspath(root)
    tf.yaml_dump(os.path.join(current_path, "vilink.meta"), meta)


def init_vilink_handler(
    hosts, port: int = 22, root: str = ".", format: str = ".sh", identity_file=None
):
    host, *tail = tcontext.is_str(hosts) and [hosts] or hosts
    format = format.replace(",", " ")
    meta = {}
    meta["remoteHost"] = host
    meta["port"] = port
    meta["format"] = format.split(" ")
    if identity_file:
        meta["identity_file"] = identity_file
    if tail:
        meta["remoteHosts"] = [
            {"port": port, "remoteHost": remoteHost} for remoteHost in tail
        ]
    save_vilink_meta(meta, root)
