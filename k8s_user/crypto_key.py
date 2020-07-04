from typing import Optional, Dict, List
from datetime import datetime, timezone
import base64
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization


NAME_ATTRIBUTE_MAPING = {
    "O": NameOID.ORGANIZATION_NAME,
    "OU": NameOID.ORGANIZATIONAL_UNIT_NAME,
    "CN": NameOID.COMMON_NAME,
    "C": NameOID.COUNTRY_NAME,
    "S": NameOID.STATE_OR_PROVINCE_NAME,
    "L": NameOID.LOCALITY_NAME,
    "SN": NameOID.SURNAME,
    "GN": NameOID.GIVEN_NAME,
    "T": NameOID.TITLE,
}


class Key:
    def __init__(
        self,
        key_size: int = 4092,
        key_file: Optional[str] = None,
        key_file_password: Optional[str] = None,
    ):

        self.key = (
            self.load(key_file, key_file_password)
            if key_file
            else rsa.generate_private_key(
                public_exponent=65537, key_size=key_size, backend=default_backend()
            )
        )

    def load(self, key_file: str, password: Optional[str] = None):
        with open(key_file, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(), password=password, backend=default_backend()
            )
        return private_key

    @property
    def pem(self):
        return self.key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )

    def save(self, path: str):
        with open(path, "wb") as f:
            f.write(self.pem)


class CSR:
    def __init__(
        self,
        key,
        common_name: str,
        additional_subject: Optional[Dict] = None,
        dnsnames: Optional[Dict] = None,
    ):
        if not additional_subject:
            additional_subject = {}
        if not dnsnames:
            dnsnames = {}

        attribue_list = [x509.NameAttribute(NameOID.COMMON_NAME, common_name)] + [
            x509.NameAttribute(NAME_ATTRIBUTE_MAPING.get(a, a), v)
            for a, v in additional_subject.items()
        ]

        self.csr = (
            x509.CertificateSigningRequestBuilder()
            .subject_name(x509.Name(attribue_list))
            .add_extension(x509.SubjectAlternativeName(dnsnames), critical=False,)
            .sign(key.key, hashes.SHA256(), default_backend())
        )

    @property
    def subject(self):
        return self.csr.subject.rfc4514_string()

    @property
    def pem(self):
        return self.csr.public_bytes(serialization.Encoding.PEM)

    @property
    def base64(self):
        return base64.b64encode(self.pem).decode("utf-8")

    def save(self, path: str):
        with open(path, "wb") as f:
            f.write(self.pem)


class CSRandKey:
    def __init__(
        self,
        common_name,
        additional_subject: Optional[Dict] = None,
        dnsnames: Optional[Dict] = None,
        key_size: int = 4092,
        key_file: Optional[str] = None,
        key_file_password: Optional[str] = None,
    ):

        self.key = Key(key_size, key_file, key_file_password,)

        self.csr = CSR(self.key, common_name, additional_subject, dnsnames,)
