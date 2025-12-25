import datetime
import ipaddress

from .discovery import Discovery

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    INSTALLED = True
except ImportError:
    INSTALLED = False


def generate_certificate(server_uuid: str, host: str) -> tuple[bytes, bytes]:
    """
    Generate a self-signed certificate according to the SiLA 2 standard.

    In short, the Common Name is set to "SiLA2" and the custom OID
    `1.3.6.1.4.1.58583` is set to the provided server uuid. In
    addition to localhost, the certificate uses the grpc server's ip
    address as an alternative name.

    Args:
      server_uuid: The server's uuid used for the custom SiLA OID.
      host: The host on which the grpc server is bound to.

    Returns:
      A tuple containing first the private key as PEM-encoded bytes
      and second the certificate as PEM-encoded bytes.
    """

    if not INSTALLED:
        msg = "Cannot import 'cryptography'"
        raise ImportError(msg)

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_key_content = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    subject = issuer = x509.Name([x509.NameAttribute(x509.OID_COMMON_NAME, "SiLA2")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.DNSName("localhost"),
                    x509.IPAddress(ipaddress.IPv4Address(Discovery.find_ip_address(host))),
                ]
            ),
            critical=False,
        )
        .add_extension(
            x509.UnrecognizedExtension(x509.ObjectIdentifier("1.3.6.1.4.1.58583"), str(server_uuid).encode("ascii")),
            critical=False,
        )
        .sign(private_key, hashes.SHA256())
    )
    cert_content = cert.public_bytes(serialization.Encoding.PEM)

    return (private_key_content, cert_content)
