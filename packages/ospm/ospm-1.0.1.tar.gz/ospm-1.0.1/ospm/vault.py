import pickle
from pathlib import Path
from nacl.secret import SecretBox
import nacl.utils
from nacl.exceptions import CryptoError
from argon2.low_level import hash_secret_raw, Type
from platformdirs import user_data_dir
from dataclasses import dataclass

data_dir = Path(user_data_dir("ospm"))


class Vault:
    def __init__(self, name: str):
        self.name = name
        self.filename = name + ".ospm"
        self.passwords: list[PasswordEntry] = []

    def get_bytes(self) -> bytes:
        return pickle.dumps(self)

    def add_password(self, password, name, account="", note=""):
        self.passwords.append(PasswordEntry(
            password=password,
            name=name,
            note=note,
            account=account
        ))

    def delete_password(self, pass_id: int):
        del self.passwords[pass_id]

    @classmethod
    def from_bytes(cls, data: bytes):
        return pickle.loads(data)

    def save_vault(self, master_password: str):
        if not Path.exists(data_dir):
            data_dir.mkdir(parents=True)
        with open(data_dir / self.filename, "wb") as f:
            f.write(encrypt(
                derive_key(master_password),
                self.get_bytes()
            ))


@dataclass
class PasswordEntry:
    password: str
    name: str
    note: str
    account: str


def encrypt(key: bytes, data: bytes) -> bytes:
    return SecretBox(key).encrypt(data, nacl.utils.random(SecretBox.NONCE_SIZE))


def decrypt(key: bytes, cipher: bytes) -> bytes:
    try:
        return SecretBox(key).decrypt(cipher)
    except CryptoError:
        print("\033[91mError: Wrong master password\033[0m")
        exit()


def derive_key(master_password: str) -> bytes:
    return hash_secret_raw(
        secret=master_password.encode(),
        salt=bytes(0xab0b),
        time_cost=4,
        memory_cost=131072,
        parallelism=2,
        hash_len=32,
        type=Type.ID
    )


def get_vault_file_data(vault_name: str) -> bytes:
    if not Path.is_dir(data_dir):
        data_dir.mkdir(parents=True)

    with open(data_dir / vault_name, "rb") as f:
        return f.read()


def verify_vault_initialised(vault_name: str = "vault.ospm"):
    if not Path.is_dir(data_dir):
        data_dir.mkdir(parents=True)

    if not Path.exists(data_dir / vault_name):
        print("First initialise your vault -\033[94m ospm init")
        exit()


def get_vault(master_password: str, vault_name: str = "vault.ospm") -> Vault:
    return Vault.from_bytes(
        decrypt(
            derive_key(master_password),
            get_vault_file_data(vault_name)
        )
    )


def is_vault_initialised(vault_name: str = "vault.ospm"):
    if not Path.is_dir(data_dir):
        data_dir.mkdir(parents=True)

    return Path.exists(data_dir / vault_name)