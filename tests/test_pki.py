import os
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from k8s_user.pki import CSRandKey, CSR, Key, Cert

FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'fixtures',
    )

def test__key__init():
    k = Key()
    private_key = serialization.load_pem_private_key(
            k.pem,
            password=None,
            backend=default_backend()
        )
    assert k.key.private_numbers().q == private_key.private_numbers().q
    assert k.key.private_numbers().q == private_key.private_numbers().q


def test__key__pem():
    k = Key()
    assert k.pem.decode("utf-8").startswith(
        "-----BEGIN RSA PRIVATE KEY-----")
    assert k.pem.decode("utf-8").endswith(
        "-----END RSA PRIVATE KEY-----\n")


def test__key__key_size():
    k = Key(key_size=2048)
    assert k.key.key_size == 2048


def test__key__load():
    k = Key(key_file=os.path.join(FIXTURE_DIR, "01_crypto_key.pem"))
    assert (k.key.private_numbers().q ==
            144297355258033432961864249587566476417513395433306785930002598799109052058830086122084681049876654212847918251721493275668666135181801876080277008509389732804065133754794433634493195096633781919315478959132232587747522900893559497688267541882710926783531946921083827536107483831548399710096915589910119439697)
    assert (k.key.private_numbers().p ==
            155077597940994614685764714448196016481909530132221791492830636731403171936034167712684220338148449908312644390351813791630716591276752117103135699908938691335706645010018715863379137684598697481255169748674781389790109894698488651804364689336883691051597751748383115970680207826187946147682102388504221500771)


def test__key__save(tmp_path):
    k = Key()
    save_key = tmp_path / "key.pem"
    save_key.write_text("")
    k.save(path=save_key)

    with open(save_key) as f:
        k_from_file = serialization.load_pem_private_key(
                f.read().encode('utf-8'),
                password=None,
                backend=default_backend()
            )
        assert k.key.private_numbers().q == k_from_file.private_numbers().q
        assert k.key.private_numbers().q == k_from_file.private_numbers().q


def test__csr__init__key_match_csr_pubkey():
    k = Key()
    c = CSR(key=k, common_name="joe")
    assert (
        k.key.public_key().public_numbers().n ==
        c.csr.public_key().public_numbers().n
    )


@pytest.mark.parametrize("cn,additional_subject,expected", 
[
    pytest.param("joe", None, "CN=joe"),
    pytest.param("joe", {"O": "corp"}, "O=corp,CN=joe"),
    pytest.param("joe", {"OU": "IT"}, "OU=IT,CN=joe"),
    pytest.param("joe", {"C": "US"}, "C=US,CN=joe"),
    pytest.param("joe", {"ST": "IL"}, "ST=IL,CN=joe"),
    pytest.param("joe", {"L": "Chicago"}, "L=Chicago,CN=joe"),
    pytest.param("joe", {"SN": "Doe"}, "2.5.4.4=Doe,CN=joe"),
    pytest.param("joe", {"GN": "Joe"}, "2.5.4.42=Joe,CN=joe"),
    pytest.param("joe", {"T": "mytitle"}, "2.5.4.12=mytitle,CN=joe"),
    pytest.param("joe", {
        "O": "corp",
        "OU": "IT",
        "T": "mytitle",
        "C": "US",
        "ST": "IL",
        "L": "Chicago",
        "SN": "Doe",
        "GN": "Joe",
    }, "2.5.4.42=Joe,2.5.4.4=Doe,L=Chicago,ST=IL,C=US,2.5.4.12=mytitle,OU=IT,O=corp,CN=joe"),
])
def test__csr__subject(cn, additional_subject, expected):
    k = Key()
    c = CSR(key=k, common_name=cn, additional_subject=additional_subject)
    assert c.subject == expected


def test__csr__pem():
    k = Key()
    cc = CSR(key=k, common_name="joe")
    assert cc.pem.decode("utf-8").startswith(
        "-----BEGIN CERTIFICATE REQUEST-----")
    assert cc.pem.decode("utf-8").endswith(
        "-----END CERTIFICATE REQUEST-----\n")


def test__csr__base64():
    k = Key()
    cc = CSR(key=k, common_name="joe")
    assert cc.base64[:32] == "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURSBS"


def test__csr__save(tmp_path):
    k = Key()
    cc = CSR(key=k, common_name="joe")
    save_csr = tmp_path / "csr.pem"
    save_csr.write_text("")
    cc.save(path=save_csr)

    with open(save_csr) as f:
        saved_csr = f.read()

    assert saved_csr.startswith(
        "-----BEGIN CERTIFICATE REQUEST-----")
    assert saved_csr.endswith(
        "-----END CERTIFICATE REQUEST-----\n")


def test__cert__init__crt_file():
    ct = Cert(crt_file=os.path.join(FIXTURE_DIR, "03_cert.pem"))
    assert ct.crt.serial_number == 61276984187087310175771381080539889888


def test__cert__init__crt_data():
    with open(os.path.join(FIXTURE_DIR, "03_cert.pem"), 'rb') as f:
        ct = Cert(crt_data=f.read())
    assert ct.crt.serial_number == 61276984187087310175771381080539889888


def test__cert__init__subject():
    ct = Cert(crt_file=os.path.join(FIXTURE_DIR, "03_cert.pem"))
    assert ct.subject == "CN=john2,O=jazstudios"


def test__cert__pem():
    ct = Cert(crt_file=os.path.join(FIXTURE_DIR, "03_cert.pem"))
    assert ct.pem.decode("utf-8").startswith(
        "-----BEGIN CERTIFICATE-----")
    assert ct.pem.decode("utf-8").endswith(
        "-----END CERTIFICATE-----\n")

def test__cert__save(tmp_path):
    ct = Cert(crt_file=os.path.join(FIXTURE_DIR, "03_cert.pem"))
    save_crt = tmp_path / "cert.pem"
    save_crt.write_text("")
    ct.save(path=save_crt)

    with open(save_crt) as f:
        saved_crt = f.read()
    assert saved_crt.startswith(
        "-----BEGIN CERTIFICATE-----")
    assert saved_crt.endswith(
        "-----END CERTIFICATE-----\n")


def test__csrandkey__init():
    ck = CSRandKey(
        common_name="joe",
        additional_subject={"O": "myorg"},
        key_size=2048,
    )
    assert ck.csr.subject == "O=myorg,CN=joe"

    assert (
        ck.key.key.public_key().public_numbers().n ==
        ck.csr.csr.public_key().public_numbers().n
    )
