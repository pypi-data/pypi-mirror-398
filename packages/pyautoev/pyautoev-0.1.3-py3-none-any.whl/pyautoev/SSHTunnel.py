# -*- coding: utf-8 -*-

from sshtunnel import SSHTunnelForwarder


class SshTunnel:
    def __init__(self, ssh_ip: str = None, ssh_port: int = None, ssh_username: str = None, ssh_password: str = None,
                 remote_ip: str = None, remote_port: int = None) -> None:
        self.__tunnel = SSHTunnelForwarder(
            ssh_address_or_host=(ssh_ip, ssh_port),
            ssh_username=ssh_username,
            ssh_password=ssh_password,
            remote_bind_address=(remote_ip, remote_port)
        )

    @property
    def tunnel(self) -> SSHTunnelForwarder:
        return self.__tunnel

    @tunnel.setter
    def tunnel(self, tunnel: SSHTunnelForwarder = None) -> None:
        self.__tunnel = tunnel

    @property
    def is_active(self) -> bool:
        return self.__tunnel.is_active

    @property
    def local_bind_port(self) -> int:
        return self.__tunnel.local_bind_port if self.is_active else -1

    def start(self) -> None:
        if not self.is_active:
            self.__tunnel.start()

    def close(self) -> None:
        if self.is_active:
            self.__tunnel.close()

