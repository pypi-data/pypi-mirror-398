# coding=utf-8

import os
import sys
import json
import shlex
import socket
import threading
import subprocess
from typing import Any

from loguru import logger

from applyx.conf import settings


class SingletonType(type):
    _singleton_lock = threading.Lock()
    def __call__(cls, *args, **kwargs):
        if not hasattr(cls, '_singleton'):
            with SingletonType._singleton_lock:
                if not hasattr(cls, '_singleton'):
                    cls._singleton = super(SingletonType, cls).__call__(*args, **kwargs)
        return cls._singleton


def check_connection(host: str, port: int, timeout=1):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.shutdown(timeout)
    except socket.gaierror:
        return False
    except socket.timeout:
        return False
    except ConnectionRefusedError:
        return False
    else:
        return True


def mqtt_publish(topic: str, payload: dict, qos=0, retain=False):
    from paho.mqtt import client, publish

    config = settings.get('mqtt')
    if config is None:
        logger.error('[mqtt] missing settings for mqtt')
        return

    try:
        publish.single(
            topic=topic,
            payload=json.dumps(payload),
            qos=qos,
            retain=retain,
            hostname=config.admin.host,
            port=config.admin.port,
            client_id=settings.get('project.name'),
            transport='tcp',
            tls=None,
            auth=None,
            keepalive=60,
            will=None,
            protocol=client.MQTTv311,
        )
    except Exception as e:
        logger.error(f'[mqtt] {str(e)}')


def setup_signal(handler=None):
    import signal

    SIGNALS = {
        signal.SIGHUP: 'SIGHUP',
        signal.SIGINT: 'SIGINT',
        signal.SIGTERM: 'SIGTERM',
    }

    def exit_handler(signum: signal.Signals, frame: Any):
        # import traceback
        # stack = traceback.format_stack(frame)
        # print(f"\n{''.join(stack)}\n")
        import colorama

        print(
            f'{colorama.Fore.WHITE}[ SIGNAL ] : {signum} - {SIGNALS[signum]}{colorama.Fore.RESET}'
        )
        sys.exit(0)

    def wrapped_handler(signum: signal.Signals, frame: Any):
        # new line after ^C
        print()

        if handler:
            handler(signum, frame)
        else:
            exit_handler(signum, frame)

    # catch kill signal except for SIGKILL(9) / SIGSTOP(19)
    for signum in SIGNALS:
        signal.signal(signum, wrapped_handler)


def rsync_files(src='', dst='', pem='', options='-azq'):
    tunnel = f"ssh -o 'StrictHostKeyChecking no' -i {pem}"
    cmd = f"rsync -e '{tunnel}' {options} {src} {dst}"
    process = subprocess.Popen(
        shlex.split(cmd),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    stdout, stderr = process.communicate()
    if stderr:
        raise Exception(stderr.decode('utf8'))


def get_store_dir():
    store_dir = os.environ.get('STORE_DIR')
    if store_dir:
        return store_dir
    return os.path.realpath(os.path.join(settings.get('project.workspace'), settings.get('project.folder.store')))


def get_log_dir():
    return os.path.realpath(os.path.join(settings.get('project.workspace'), settings.get('project.folder.log')))
