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
        key_data: Optional[bytes] = None,
        key_file: Optional[str] = None,
        key_file_password: Optional[str] = None,
    ):
        self.key_size = key_size
        self.load(key_data, key_file, key_file_password)

    def load_data(self, key_data: bytes, password: Optional[str] = None):
        private_key = serialization.load_pem_private_key(
            key_data,
            password=password,
            backend=default_backend()
        )
        return private_key

    def load_file(self, path: str, password: Optional[str] = None):
        with open(path, 'rb') as f:
            return self.load_data(f.read(), password=password)

    def load(self, key_data=None, key_file=None, password: Optional[str] = None):
        if key_data:
            self.key = self.load_data(key_data, password=password)
        elif key_file:
            self.key = self.load_file(path=key_file, password=password)
        else:
            self.key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=self.key_size,
                backend=default_backend()
            )

    @property
    def base64(self):
        return base64.b64encode(self.pem).decode("utf-8")

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


class Cert:

    def __init__(
            self,
            crt_data: Optional[bytes] = None,
            crt_file: Optional[str] = None):
        self.load(crt_data, crt_file)

    def load_data(self, crt_data: bytes):
        return x509.load_pem_x509_certificate(
            crt_data, default_backend())

    def load_file(self, path: str):
        with open(path, 'rb') as f:
            return self.load_data(f.read())

    def load(self, crt_data=None, crt_file=None):
        if crt_data:
            self.crt = self.load_data(crt_data)
        elif crt_file:
            self.crt = self.load_file(path=crt_file)
        else:
            self.crt = None

    @property
    def pem(self):
        return self.crt.public_bytes(serialization.Encoding.PEM)

    @property
    def base64(self):
        return base64.b64encode(self.pem).decode("utf-8")

    @property
    def subject(self):
        return self.crt.subject.rfc4514_string()

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
