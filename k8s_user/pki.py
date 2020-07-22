from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import base64
import collections
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
    "ST": NameOID.STATE_OR_PROVINCE_NAME,
    "L": NameOID.LOCALITY_NAME,
    "STREET": NameOID.STREET_ADDRESS,
    "SN": NameOID.SURNAME,
    "GN": NameOID.GIVEN_NAME,
    "T": NameOID.TITLE,
    "DC": NameOID.DOMAIN_COMPONENT,
    "UID": NameOID.USER_ID,
}


KeyBundle = collections.namedtuple("KeyBundle", "user_name user_key user_csr user_cert")


class Key:
    def __init__(
        self,
        key_size: int = 4092,
        key_data: Optional[bytes] = None,
        key_file: Optional[str] = None,
        key_file_password: Optional[str] = None,
    ):
        self.created = False
        self.key_size = key_size
        self.key_data = key_data
        self.key_file = key_file
        self.key_file_password = key_file_password

        if self.key_file or self.key_data:
            self.load()
        else:
            self.generate()
            self.created = True

    def load_data(self, key_data: bytes, password: Optional[str] = None):
        private_key = serialization.load_pem_private_key(
            key_data, password=password, backend=default_backend()
        )
        return private_key

    def load_file(self, path: str, password: Optional[str] = None):
        with open(path, "rb") as f:
            return self.load_data(f.read(), password=password)

    def load(self):
        if self.key_data:
            self.key = self.load_data(
                key_data=self.key_data, password=self.key_file_password)
        elif self.key_file:
            self.key = self.load_file(
                path=self.key_file, password=self.key_file_password)
        else:
            raise ValueError("Must supply key_data or key_file")

    def generate(self):
        self.key = rsa.generate_private_key(
            public_exponent=65537, key_size=self.key_size, backend=default_backend()
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
        key: Key,
        common_name: str,
        additional_subject: Optional[Dict] = None,
        dnsnames: Optional[Dict] = None,
        csr_data: Optional[bytes] = None,
        csr_file: Optional[str] = None,
        signing_hash_algo: Optional[Any] = None,
    ):
        self.created = False
        self.key = key
        self.csr_data = csr_data
        self.csr_file = csr_file
        self.signing_hash_algo  = (
            signing_hash_algo if signing_hash_algo else hashes.SHA256)

        if not additional_subject:
            additional_subject = {}
        self.attribue_list = [x509.NameAttribute(NameOID.COMMON_NAME, common_name)] + [
            x509.NameAttribute(NAME_ATTRIBUTE_MAPING.get(a, a), v)
            for a, v in additional_subject.items()
        ]

        if not dnsnames:
            dnsnames = {}
        self.dnsnames = dnsnames

        if self.csr_file or self.csr_data:
            self.load()
        else:
            self.generate()
            self.created = True

    def load_data(self, csr_data: bytes):
        csr = x509.load_pem_x509_csr(
            csr_data, backend=default_backend()
        )
        return csr

    def load_file(self, path: str):
        with open(path, "rb") as f:
            return self.load_data(f.read())

    def load(self):
        if self.csr_data:
            self.csr = self.load_data(csr_data=self.csr_data)
        elif self.csr_file:
            self.csr = self.load_file(path=self.csr_file)
        else:
            raise ValueError("Must supply csr_data or csr_file")

    def generate(self):
        self.csr = (
            x509.CertificateSigningRequestBuilder()
            .subject_name(x509.Name(self.attribue_list))
            .add_extension(x509.SubjectAlternativeName(self.dnsnames), critical=False,)
            .sign(self.key.key, self.signing_hash_algo(), default_backend())
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
        self, crt_data: Optional[bytes] = None, crt_file: Optional[str] = None
    ):
        self.load(crt_data, crt_file)

    def load_data(self, crt_data: bytes):
        return x509.load_pem_x509_certificate(crt_data, default_backend())

    def load_file(self, path: str):
        with open(path, "rb") as f:
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
        csr_file: Optional[str] = None,
    ):

        self.key = Key(
            key_size=key_size,
            key_file=key_file,
            key_file_password=key_file_password,
        )
        self.csr = CSR(
            key=self.key,
            common_name=common_name,
            additional_subject=additional_subject,
            dnsnames=dnsnames,
            csr_file=csr_file,
        )
