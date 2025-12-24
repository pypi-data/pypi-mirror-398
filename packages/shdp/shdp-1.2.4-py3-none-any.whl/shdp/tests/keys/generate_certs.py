import datetime
import os

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def generate_test_certificates(output_dir: str = "."):
    """Génère un certificat auto-signé et une clé privée pour les tests."""

    # Générer la clé privée
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # Créer le certificat
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "SHDP Test CA"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SHDP Tests"),
        ]
    )

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(private_key, hashes.SHA256())
    )

    # Créer le dossier si nécessaire
    os.makedirs(output_dir, exist_ok=True)

    # Sauvegarder le certificat
    with open(os.path.join(output_dir, "cert.pem"), "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    # Sauvegarder la clé privée
    with open(os.path.join(output_dir, "key.pem"), "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )


if __name__ == "__main__":
    generate_test_certificates("./")
