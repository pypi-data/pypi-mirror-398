from keyblock.crypto import (
    create_project_key,
    decrypt_private_key,
    decrypt_secret,
    encrypt_private_key,
    encrypt_secret,
    generate_keypair,
    unwrap_project_key,
    wrap_project_key,
)


def test_private_key_roundtrip():
    kp = generate_keypair()
    encrypted = encrypt_private_key(kp["secret_key"], "correct horse battery staple")
    decrypted = decrypt_private_key(encrypted, "correct horse battery staple")
    assert decrypted == kp["secret_key"]


def test_project_key_wrap_unwrap():
    recipient = generate_keypair()
    project_key = create_project_key()
    envelope = wrap_project_key(project_key, recipient["public_key"])
    recovered = unwrap_project_key(envelope, recipient["secret_key"])
    assert recovered == project_key


def test_secret_encrypt_decrypt():
    project_key = create_project_key()
    encrypted = encrypt_secret("hello-cli", project_key)
    decrypted = decrypt_secret(encrypted, project_key)
    assert decrypted == "hello-cli"

