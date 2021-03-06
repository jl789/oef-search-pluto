import argparse
import multiprocessing
import subprocess
import time
import os
from utils.src.python.resources import binaryfile
import time
import socket
from utils.src.python.Logging import has_logger, get_logger


def _run_search_node(name: str, node_ip: str, node_port: int, dap_port_start: int, director_api_port: int,
                     http_port: int, ssl_certificate: str, q: multiprocessing.Queue, log_file: str):
    from network_oef.src.python.FullLocalSearchNode import FullSearchNone
    from utils.src.python.Logging import configure as configure_logging
    configure_logging(file=log_file)
    logger = get_logger("NODE_RUN: "+name)

    node = FullSearchNone(name, node_ip, node_port, [{
        #"run_py_dap": True,
        #"file": "ai_search_engine/src/resources/dap_config.json",
        #"port": dap_port_start,
        "run_mode": "CPP", #PY/CPP
        "port": dap_port_start,
        "name": "in_memory_dap"
    }
    ], http_port, ssl_certificate, "api/src/resources/website", director_api_port=director_api_port,
                          log_dir=os.path.split(log_file)[0])
    logger.error("**** Node %s started", name)
    time.sleep(1)
    try:
        while True:
            con = q.get()
            logger.info("**** SearchProcess got peer: %s @ %s ", con[2], con[0]+":"+str(con[1]))
            if len(con) != 3:
                logger.error("**** Stopping connection queue listening, because invalid con: ", con)
                break
            node.add_remote_peer(*con)
        node.block()
    except Exception as e:
        logger.exception("Exception in run_search_node: ", e)
    except:
        logger.exception("Exception")
    logger.error("******* EXIT SEARCH NODE")


class FullNode:
    @has_logger
    def __init__(self):
        self._search_queue = multiprocessing.Queue()
        self._search_process = None
        self._search_ip = None
        self._search_port = None
        self._node_key = ""
        self._core_process = None

    def start_search(self, node_key: str, ip: str, port: int, dap_port: int, director_port: int, http_port: int = -1,
                     ssl_certificate: str = "", log_file: str = ""):
        self._search_process = multiprocessing.Process(target=_run_search_node, args=(node_key, ip, port, dap_port,
                                                                                      director_port, http_port,
                                                                                      ssl_certificate,
                                                                                      self._search_queue,
                                                                                      log_file)
                                                       )
        self._search_process.start()
        self._search_ip = ip
        self._search_port = port
        self._node_key = node_key

    def start_core(self, core_key: str, ip: str, port: int, oef_core=None, log_file: str = ""):
        if oef_core is None:
            oef_core = binaryfile("fetch_teams/OEFNode", as_file=True).name
        while True:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if sock.connect_ex((self._search_ip, self._search_port)) != 0:
                time.sleep(0.5)
                print(".")
            else:
                break
        if len(log_file) > 0:
            log_file = open(log_file, 'w')
            self._core_process = subprocess.Popen([oef_core, core_key, ip, str(port), self._search_ip,
                                                   str(self._search_port)], stdout=log_file, stderr=log_file)
        else:
            self._core_process = subprocess.Popen([oef_core, core_key, ip, str(port), self._search_ip,
                                                   str(self._search_port)])

    def add_peer(self, node_key: str, host: str, port: int) -> bool:
        try:
            host = socket.gethostbyname(host)
        except Exception as e:
            self.exception("Resolution failed, because: " + str(e))
            return False
        port = int(port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if sock.connect_ex((host, port)) != 0:
            self.info("Connection to search node @ {}:{} failed, because socket not open!".format(host, port))
            return False
        try:
            self._search_queue.put([host, port, node_key])
        except Exception as e:
            self.exception("Failed to put peer to search_queue: ", str(e))
        return True

    def wait(self):
        self._search_process.join()
        self.error("****** SEARCH PROCESS EXITED: ", self._search_process.exitcode, " (node key: ", self._node_key, ")")
        self._core_process.wait()
        self.error("****** CORE PROCESS EXITED")
