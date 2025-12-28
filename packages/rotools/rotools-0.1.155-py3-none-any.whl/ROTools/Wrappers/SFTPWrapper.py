import logging

import paramiko

log = logging.getLogger(__name__)

class SFTPWrapper:
    def __init__(self, ftp_config):
        self.host = ftp_config.host
        self.port = ftp_config.port
        self.username = ftp_config.user
        self.password = ftp_config.password
        self.remote_root = ftp_config.get("remote_root")

        self.transport = None
        self.sftp = None

    def __enter__(self) -> paramiko.SFTPClient:
        self.transport = paramiko.Transport((self.host, self.port))
        self.transport.connect(username=self.username, password=self.password)
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)

        if self.remote_root:
            self.sftp.chdir(self.remote_root)

        return self

    def remove(self, path, throw=True):
        try:
            self.sftp.remove(path)
        except FileNotFoundError:
            if throw:
                raise
            log.warning(f"File not found on server, skipping deletion: {path}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.sftp:
            self.sftp.close()
        if self.transport:
            self.transport.close()
