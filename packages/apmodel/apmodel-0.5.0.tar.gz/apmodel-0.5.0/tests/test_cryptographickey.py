import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from apmodel.extra.security import CryptographicKey


def test_cryptographic_key_creation():
    # Test creating a CryptographicKey instance
    key = CryptographicKey(id="did:example:123#key-1", owner="did:example:123")

    assert key.id == "did:example:123#key-1"
    assert key.owner == "did:example:123"
    assert key.type == "CryptographicKey"


def test_cryptographic_key_public_key_property_with_pem_string():
    # Generate an RSA key pair for testing
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()

    # Get the PEM representation of the public key
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    # Create a CryptographicKey instance
    key = CryptographicKey(
        id="did:example:123#key-1", owner="did:example:123", public_key_pem=public_pem
    )

    # Access the public key property
    retrieved_public_key = key.public_key

    assert retrieved_public_key is not None
    assert isinstance(retrieved_public_key, rsa.RSAPublicKey)


def test_cryptographic_key_public_key_property_with_pem_bytes():
    # Generate an RSA key pair for testing
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()

    # Get the PEM representation of the public key as bytes
    public_pem_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # Create a CryptographicKey instance
    key = CryptographicKey(
        id="did:example:123#key-1",
        owner="did:example:123",
        public_key_pem=public_pem_bytes,
    )

    # Access the public key property
    retrieved_public_key = key.public_key

    assert retrieved_public_key is not None
    assert isinstance(retrieved_public_key, rsa.RSAPublicKey)


def test_cryptographic_key_public_key_property_with_no_pem():
    # Create a CryptographicKey instance without public key PEM
    key = CryptographicKey(id="did:example:123#key-1", owner="did:example:123")

    # Access the public key property
    retrieved_public_key = key.public_key

    assert retrieved_public_key is None


def test_cryptographic_key_set_public_key_with_rsa_public_key():
    # Generate an RSA key pair for testing
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()

    # Create a CryptographicKey instance
    key = CryptographicKey(id="did:example:123#key-1", owner="did:example:123")

    # Set the public key
    key.set_public_key = public_key

    # Check that the PEM representation was set
    assert key.public_key_pem is not None
    assert isinstance(key.public_key_pem, str)

    # Check that the public key property returns the correct key
    retrieved_key = key.public_key
    assert retrieved_key is not None
    assert isinstance(retrieved_key, rsa.RSAPublicKey)


def test_cryptographic_key_set_public_key_with_rsa_private_key():
    # Generate an RSA key pair for testing
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Create a CryptographicKey instance
    key = CryptographicKey(id="did:example:123#key-1", owner="did:example:123")

    # Set the public key using the private key (should extract the public key)
    key.set_public_key = private_key

    # Check that the PEM representation was set
    assert key.public_key_pem is not None
    assert isinstance(key.public_key_pem, str)

    # Check that the public key property returns the correct key
    retrieved_key = key.public_key
    assert retrieved_key is not None
    assert isinstance(retrieved_key, rsa.RSAPublicKey)


def test_cryptographic_key_invalid_key_type():
    # Test with an invalid key type that is not RSA
    class InvalidKeyType:
        pass

    key = CryptographicKey(
        id="did:example:123#key-1",
        owner="did:example:123",
        public_key_pem="invalid pem data",
    )

    # This should raise a ValueError when accessing public_key
    with pytest.raises(ValueError):
        _ = key.public_key


def test_cryptographic_key_serialization():
    # Generate an RSA key pair for testing
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()

    # Get the PEM representation of the public key
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    # Create a CryptographicKey instance
    key = CryptographicKey(
        id="did:example:123#key-1", owner="did:example:123", public_key_pem=public_pem
    )

    # Check serialization
    serialized = key.model_dump(by_alias=True)
    assert serialized["id"] == "did:example:123#key-1"
    assert serialized["owner"] == "did:example:123"
    assert "publicKeyPem" in serialized
    assert serialized["type"] == "CryptographicKey"
