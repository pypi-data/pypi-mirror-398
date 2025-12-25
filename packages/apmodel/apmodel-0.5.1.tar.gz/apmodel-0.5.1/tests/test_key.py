import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa
from multiformats import multibase, multicodec

from apmodel._core.key import (
    _encode_private_key_as_multibase,
    _encode_public_key_as_multibase,
    _load_private_key_from_multibase,
    _load_public_key_from_multibase,
)


def test_load_private_key_from_multibase_ed25519():
    # Generate an Ed25519 key pair for testing
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Encode the private key in multibase format
    wrapped = multicodec.wrap(
        "ed25519-priv",
        private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        ),
    )
    multibase_encoded = multibase.encode(wrapped, "base58btc")

    # Load the key back
    loaded_key = _load_private_key_from_multibase(multibase_encoded)

    # Check that it's the same type and can sign data
    assert isinstance(loaded_key, ed25519.Ed25519PrivateKey)
    signature = loaded_key.sign(b"test message")
    public_key.verify(signature, b"test message")


def test_load_private_key_from_multibase_rsa():
    # Generate an RSA key pair for testing
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Encode the private key in multibase format
    wrapped = multicodec.wrap(
        "rsa-priv",
        private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ),
    )
    multibase_encoded = multibase.encode(wrapped, "base58btc")

    # Load the key back
    loaded_key = _load_private_key_from_multibase(multibase_encoded)

    # Check that it's the same type and can sign data
    assert isinstance(loaded_key, rsa.RSAPrivateKey)


def test_load_public_key_from_multibase_ed25519():
    # Generate an Ed25519 key pair for testing
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Encode the public key in multibase format
    wrapped = multicodec.wrap(
        "ed25519-pub",
        public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        ),
    )
    multibase_encoded = multibase.encode(wrapped, "base58btc")

    # Load the key back
    loaded_key = _load_public_key_from_multibase(multibase_encoded)

    # Check that it's the same type
    assert isinstance(loaded_key, ed25519.Ed25519PublicKey)


def test_load_public_key_from_multibase_rsa():
    # Generate an RSA key pair for testing
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()

    # Encode the public key in multibase format
    wrapped = multicodec.wrap(
        "rsa-pub",
        public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.PKCS1,
        ),
    )
    multibase_encoded = multibase.encode(wrapped, "base58btc")

    # Load the key back
    loaded_key = _load_public_key_from_multibase(multibase_encoded)

    # Check that it's the same type
    assert isinstance(loaded_key, rsa.RSAPublicKey)


def test_encode_public_key_as_multibase_ed25519():
    # Generate an Ed25519 key pair for testing
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Encode the public key as multibase
    encoded = _encode_public_key_as_multibase(public_key)

    # Decode and check
    decoded = multibase.decode(encoded)
    codec, data = multicodec.unwrap(decoded)

    assert codec.name == "ed25519-pub"
    assert data == public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def test_encode_public_key_as_multibase_rsa():
    # Generate an RSA key pair for testing
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()

    # Encode the public key as multibase
    encoded = _encode_public_key_as_multibase(public_key)

    # Decode and check
    decoded = multibase.decode(encoded)
    codec, data = multicodec.unwrap(decoded)

    assert codec.name == "rsa-pub"
    assert data == public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.PKCS1,
    )


def test_encode_private_key_as_multibase_ed25519():
    private_key = ed25519.Ed25519PrivateKey.generate()

    encoded = _encode_private_key_as_multibase(private_key)

    decoded = multibase.decode(encoded)
    codec, data = multicodec.unwrap(decoded)

    assert codec.name == "ed25519-priv"
    assert data == private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )


def test_encode_private_key_as_multibase_rsa():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    encoded = _encode_private_key_as_multibase(private_key)

    decoded = multibase.decode(encoded)
    codec, data = multicodec.unwrap(decoded)

    assert codec.name == "rsa-priv"
    assert data == private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def test_load_invalid_private_key_format():
    with pytest.raises(ValueError):
        _load_private_key_from_multibase("invalid_key_string")


def test_load_invalid_public_key_format():
    with pytest.raises(ValueError):
        _load_public_key_from_multibase("invalid_key_string")


def test_encode_unsupported_public_key_type():
    class UnsupportedKeyType:
        pass

    with pytest.raises(ValueError):
        _encode_public_key_as_multibase(UnsupportedKeyType())  # pyrefly: ignore


def test_encode_unsupported_private_key_type():
    class UnsupportedKeyType:
        pass

    with pytest.raises(ValueError):
        _encode_private_key_as_multibase(UnsupportedKeyType())  # pyrefly: ignore


def test_load_unsupported_codec():
    # Create a multibase with an unsupported codec that exists in multicodec table
    # Using a codec that is not handled by our functions (not ed25519-priv, rsa-priv, ed25519-pub, rsa-pub)
    wrapped = multicodec.wrap(
        "identity", b"dummy_data"
    )  # identity is a valid codec but not supported by our functions
    multibase_encoded = multibase.encode(wrapped, "base58btc")

    with pytest.raises(ValueError):
        _load_private_key_from_multibase(multibase_encoded)

    with pytest.raises(ValueError):
        _load_public_key_from_multibase(multibase_encoded)
