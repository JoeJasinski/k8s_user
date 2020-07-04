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

class CSRAndKey:
    def __init__(
            self,
            common_name,
            additional_subject: Optional[Dict]=None,
            dnsnames: Optional[Dict]=None,
            keysize: int=4092,
            key_file: Optional[str] = None,
            key_file_password: Optional[str] = None):
        if not additional_subject:
            additional_subject = {}
        if not dnsnames:
            dnsnames = {}

        self.key = (
            self.load_key(key_file, key_file_password)
            if key_file else rsa.generate_private_key(
                public_exponent=65537,
                key_size=keysize,
                backend=default_backend()
            ))
        
        attribue_list = [
            x509.NameAttribute(NameOID.COMMON_NAME, common_name)
        ] + [x509.NameAttribute(NAME_ATTRIBUTE_MAPING.get(a, a), v) 
             for a, v in additional_subject.items()]
        
        self.csr = x509.CertificateSigningRequestBuilder().subject_name(
            x509.Name(attribue_list)).add_extension(
                    x509.SubjectAlternativeName(
                        dnsnames
                    ),
                    critical=False,
                ).sign(self.key, hashes.SHA256(), default_backend())

    def load_key(self, key_file, password=None):
        with open(key_file, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=password,
                backend=default_backend())
        return private_key
        
    @property
    def key_pem(self):
        return self.key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    @property
    def csr_pem(self):
         return self.csr.public_bytes(serialization.Encoding.PEM)

    @property    
    def csr_base64(self):
        return base64.b64encode(self.csr_pem).decode("utf-8")
    
    def csr_save(self, path: str):
        with open(path, "wb") as f:
            f.write(self.csr_pem)
            
    def key_save(self, path: str):
        with open(path, "wb") as f:
            f.write(self.key_pem)

