# arpakit

from __future__ import annotations

import asyncssh
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from pydantic import BaseModel, Field


class SSHKeys(BaseModel):
    private_key: str = Field()
    public_key: str = Field()


def generate_ed25519_via_asyncssh_ssh_keys() -> SSHKeys:
    key = asyncssh.generate_private_key("ssh-ed25519")

    private_key_str = key.export_private_key().decode()
    public_key_str = key.export_public_key().decode()

    return SSHKeys(
        private_key=private_key_str,
        public_key=public_key_str
    )


def generate_ed25519_via_cryptography_ssh_keys() -> SSHKeys:
    private_key = ed25519.Ed25519PrivateKey.generate()

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption()
    )

    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH
    )

    return SSHKeys(
        private_key=private_bytes.decode(),
        public_key=public_key.decode()
    )
