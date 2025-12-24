import os
from pathlib import Path
from typing import Any, Optional, Union
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
import base64
import yaml

# Support both package-relative and direct imports
try:
    from .serialization import XSer
except ImportError:
    from serialization import XSer



class Encryptor:
    """
    Encryption utilities for Python objects and raw bytes.

    This class provides symmetric encryption capabilities using Fernet (AES-128 in CBC mode)
    with support for both cryptographic key-based and password-based encryption.

    Features
    --------
    - Encrypt/decrypt arbitrary Python objects via pickle serialization
    - Encrypt/decrypt raw bytes
    - Password-based encryption with PBKDF2 key derivation
    - Direct key-based encryption with Fernet keys
    - Automatic salt generation and storage for password-based operations

    Security Notes
    --------------
    - Uses Fernet symmetric encryption (AES-128-CBC with HMAC authentication)
    - Password-based encryption uses PBKDF2-HMAC-SHA256 with 480,000 iterations
    - Salt is 16 bytes and randomly generated for each password encryption
    - Keys are 32 bytes (256 bits) when generated

    Examples
    --------
    Key-based encryption:
        >>> key = Encryptor.generate_key()
        >>> encrypted = Encryptor.encrypt_bytes(b"secret data", key=key)
        >>> decrypted = Encryptor.decrypt_bytes(encrypted, key=key)

    Password-based encryption:
        >>> encrypted = Encryptor.encrypt_bytes(b"secret data", password="my_password")
        >>> decrypted = Encryptor.decrypt_bytes(encrypted, password="my_password")

    Object encryption:
        >>> data = {"users": ["alice", "bob"], "count": 42}
        >>> encrypted = Encryptor.encrypt_object(data, password="my_password")
        >>> decrypted = Encryptor.decrypt_object(encrypted, password="my_password")
    """

    # PBKDF2 parameters for password-based key derivation
    _PBKDF2_ITERATIONS = 480_000  # OWASP recommendation as of 2023
    _SALT_SIZE = 16  # 128 bits

    @staticmethod
    def generate_key() -> bytes:
        """
        Generate a new Fernet-compatible encryption key.

        Returns
        -------
        bytes
            A 32-byte URL-safe base64-encoded key suitable for Fernet encryption.

        Notes
        -----
        Store this key securely. Loss of the key means permanent loss of access
        to encrypted data. The key should be kept secret and never transmitted
        or stored alongside encrypted data.

        Examples
        --------
        >>> key = Encryptor.generate_key()
        >>> # Store key securely (e.g., environment variable, key management service)
        >>> with open("secret.key", "wb") as f:
        ...     f.write(key)
        """
        return Fernet.generate_key()

    @staticmethod
    def load_or_generate_key(key_file_path: Union[str, Path]) -> bytes:
        """
        Load an encryption key from a signed file, or generate and save a new one.

        This method provides convenient key file management using SignedFile for
        integrity verification. Keys are stored as signed (but not encrypted) files.

        If the key file exists, it is read and verified using SignedFile.read().
        If the file does not exist, a new key is generated and saved using
        SignedFile.write() with integrity protection but no encryption.

        Parameters
        ----------
        key_file_path : Union[str, Path]
            Path to the key file. Can be a string or Path object.

        Returns
        -------
        bytes
            The encryption key (either loaded from file or newly generated).

        Raises
        ------
        ValueError
            If the key file exists but fails signature verification, indicating
            the file has been tampered with or is corrupted.

        Examples
        --------
        First use (generates and saves key):
            >>> key = Encryptor.load_or_generate_key("my_app.key")
            >>> # Key generated and saved to 'my_app.key'

        Subsequent uses (loads existing key):
            >>> key = Encryptor.load_or_generate_key("my_app.key")
            >>> # Key loaded from existing 'my_app.key'

        Using the key:
            >>> key = Encryptor.load_or_generate_key("encryption.key")
            >>> encrypted = Encryptor.encrypt_bytes(b"data", key=key)
            >>> decrypted = Encryptor.decrypt_bytes(encrypted, key=key)

        Notes
        -----
        - The key file is signed (SHA-256) but NOT encrypted
        - Signature verification ensures the key hasn't been tampered with
        - Keys are 32 bytes (256 bits) and URL-safe base64-encoded
        - Store key files in secure locations with appropriate file permissions
        - Consider using OS-level encryption (e.g., encrypted filesystems) for
          additional protection of key files at rest
        """
        # Late import to avoid circular dependency
        from signature import SignedFile

        path = Path(key_file_path)

        if path.exists():
            key_data = SignedFile.read(path)
            assert isinstance(key_data, bytes), "Key file read should return bytes"
            return key_data

        # File doesn't exist - generate and save new key
        key = Encryptor.generate_key()
        SignedFile.write(path, key)
        return key

    @staticmethod
    def _resolve_key_or_password(
        key: Optional[bytes],
        password: Optional[str]
    ) -> tuple[Optional[bytes], Optional[str]]:
        """
        Resolve encryption key or password with fallback to environment variable.

        This helper function implements the precedence order for key resolution:
        1. Explicit key parameter (highest priority)
        2. Explicit password parameter
        3. Encryption_SECRET environment variable (fallback)

        Parameters
        ----------
        key : bytes, optional
            Explicit encryption key.
        password : str, optional
            Explicit password.

        Returns
        -------
        tuple[Optional[bytes], Optional[str]]
            A tuple of (resolved_key, resolved_password). Only one will be non-None.

        Raises
        ------
        ValueError
            If no key, password, or environment variable is available.
        """
        # Explicit key has highest priority
        if key is not None:
            return (key, None)

        # Explicit password has second priority
        if password is not None:
            return (None, password)

        # Check environment variable as fallback
        env_key = os.environ.get('Encryption_SECRET')
        if env_key is not None:
            resolved_key = env_key.encode() if isinstance(env_key, str) else env_key
            return (resolved_key, None)

        raise ValueError(
            "Either 'key' or 'password' must be provided, or set the "
            "'Encryption_SECRET' environment variable."
        )

    @staticmethod
    def _derive_key_from_password(password: str, salt: bytes) -> bytes:
        """
        Derive a Fernet-compatible key from a password using PBKDF2.

        Parameters
        ----------
        password : str
            The password to derive the key from.
        salt : bytes
            Salt for key derivation (must be 16 bytes).

        Returns
        -------
        bytes
            A 32-byte URL-safe base64-encoded Fernet key.

        Notes
        -----
        Uses PBKDF2-HMAC-SHA256 with 480,000 iterations for strong key derivation.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=Encryptor._PBKDF2_ITERATIONS,
        )
        key_bytes = kdf.derive(password.encode('utf-8'))
        # Fernet expects a URL-safe base64-encoded key
        return base64.urlsafe_b64encode(key_bytes)

    @staticmethod
    def encrypt_bytes(
        data: bytes,
        key: Optional[bytes] = None,
        password: Optional[str] = None
    ) -> bytes:
        """
        Encrypt raw bytes using either a key or password.

        Parameters
        ----------
        data : bytes
            The raw bytes to encrypt.
        key : bytes, optional
            A Fernet key (32-byte URL-safe base64-encoded). If provided,
            password is ignored.
        password : str, optional
            A password to derive the encryption key from. Only used if
            key is not provided.

        Returns
        -------
        bytes
            Encrypted data. For password-based encryption, the output format is:
            [16-byte salt][encrypted data]. For key-based encryption, only
            the encrypted data is returned.

        Raises
        ------
        ValueError
            If neither key nor password is provided and no environment variable
            is set, or if data is not bytes.

        Notes
        -----
        If neither key nor password is provided, the method will check for the
        environment variable 'Encryption_SECRET' and use it as the encryption key.

        Examples
        --------
        With key:
            >>> key = Encryptor.generate_key()
            >>> encrypted = Encryptor.encrypt_bytes(b"secret", key=key)

        With password:
            >>> encrypted = Encryptor.encrypt_bytes(b"secret", password="pass123")

        With environment variable:
            >>> import os
            >>> os.environ['Encryption_SECRET'] = Encryptor.generate_key().decode()
            >>> encrypted = Encryptor.encrypt_bytes(b"secret")  # Uses env var
        """
        if not isinstance(data, bytes):
            raise ValueError("Data must be bytes.")

        key, password = Encryptor._resolve_key_or_password(key, password)

        if key is not None:
            fernet = Fernet(key)
            return fernet.encrypt(data)

        assert password is not None, "Password must be provided when key is not specified"
        salt = os.urandom(Encryptor._SALT_SIZE)
        derived_key = Encryptor._derive_key_from_password(password, salt)
        fernet = Fernet(derived_key)
        encrypted_data = fernet.encrypt(data)

        return salt + encrypted_data

    @staticmethod
    def decrypt_bytes(
        encrypted_data: bytes,
        key: Optional[bytes] = None,
        password: Optional[str] = None
    ) -> bytes:
        """
        Decrypt bytes that were encrypted with encrypt_bytes.

        Parameters
        ----------
        encrypted_data : bytes
            The encrypted data to decrypt.
        key : bytes, optional
            The Fernet key used for encryption. If provided, password is ignored.
        password : str, optional
            The password used for encryption. Only used if key is not provided.

        Returns
        -------
        bytes
            The decrypted raw bytes.

        Raises
        ------
        ValueError
            If neither key nor password is provided and no environment variable
            is set, if the data is corrupted, or if the wrong key/password is used.

        Notes
        -----
        If neither key nor password is provided, the method will check for the
        environment variable 'Encryption_SECRET' and use it as the decryption key.

        Examples
        --------
        With key:
            >>> decrypted = Encryptor.decrypt_bytes(encrypted_data, key=key)

        With password:
            >>> decrypted = Encryptor.decrypt_bytes(encrypted_data, password="pass123")

        With environment variable:
            >>> import os
            >>> os.environ['Encryption_SECRET'] = key.decode()
            >>> decrypted = Encryptor.decrypt_bytes(encrypted_data)  # Uses env var
        """
        if not isinstance(encrypted_data, bytes):
            raise ValueError("Encrypted data must be bytes.")

        key, password = Encryptor._resolve_key_or_password(key, password)

        if key is not None:
            fernet = Fernet(key)
            return fernet.decrypt(encrypted_data)

        if len(encrypted_data) < Encryptor._SALT_SIZE:
            raise ValueError("Encrypted data is too short to contain salt.")

        salt = encrypted_data[:Encryptor._SALT_SIZE]
        ciphertext = encrypted_data[Encryptor._SALT_SIZE:]

        assert password is not None, "Password must be provided when key is not specified"
        derived_key = Encryptor._derive_key_from_password(password, salt)
        fernet = Fernet(derived_key)

        return fernet.decrypt(ciphertext)

    @staticmethod
    def encrypt_object(
        obj: Any,
        key: Optional[bytes] = None,
        password: Optional[str] = None
    ) -> bytes:
        """
        Encrypt an arbitrary Python object.

        The object is first serialized using XSer, then encrypted. XSer provides
        multi-format serialization with support for numpy arrays, datetime objects,
        and a resilient fallback chain (JSON/YAML -> CBOR -> Pickle).

        Parameters
        ----------
        obj : Any
            The Python object to encrypt. Must be serializable by XSer.
        key : bytes, optional
            A Fernet key for encryption. If provided, password is ignored.
        password : str, optional
            A password to derive the encryption key from. Only used if key is not provided.

        Returns
        -------
        bytes
            Encrypted serialized object data.

        Raises
        ------
        ValueError
            If neither key nor password is provided, or if serialization fails.

        Examples
        --------
        >>> data = {"name": "Alice", "age": 30, "items": [1, 2, 3]}
        >>> encrypted = Encryptor.encrypt_object(data, password="secret")
        >>> decrypted = Encryptor.decrypt_object(encrypted, password="secret")
        >>> assert data == decrypted

        With numpy arrays:
        >>> import numpy as np
        >>> data = {"array": np.array([1, 2, 3]), "value": 42}
        >>> encrypted = Encryptor.encrypt_object(data, password="secret")
        >>> decrypted = Encryptor.decrypt_object(encrypted, password="secret")

        Notes
        -----
        XSer provides:
        - Better support for numpy arrays and scientific data types
        - Multi-format fallback (JSON/YAML compatible -> CBOR -> Pickle)
        - DateTime, UUID, Path, Decimal support
        - Configurable CLASS_ALLOWLIST for security
        """
        # Use XSer serialization
        serialized = XSer.to_hdf5_attr(obj)
        return Encryptor.encrypt_bytes(serialized, key=key, password=password)

    @staticmethod
    def decrypt_object(
        encrypted_data: bytes,
        key: Optional[bytes] = None,
        password: Optional[str] = None
    ) -> Any:
        """
        Decrypt and deserialize a Python object encrypted with encrypt_object.

        The data is decrypted and then deserialized using XSer, which automatically
        handles various data types including numpy arrays, datetime objects, and more.

        Parameters
        ----------
        encrypted_data : bytes
            The encrypted object data.
        key : bytes, optional
            The Fernet key used for encryption. If provided, password is ignored.
        password : str, optional
            The password used for encryption. Only used if key is not provided.

        Returns
        -------
        Any
            The decrypted and deserialized Python object.

        Raises
        ------
        ValueError
            If neither key nor password is provided, or if decryption/deserialization fails.

        Examples
        --------
        >>> encrypted = Encryptor.encrypt_object([1, 2, 3], password="secret")
        >>> decrypted = Encryptor.decrypt_object(encrypted, password="secret")
        >>> print(decrypted)
        [1, 2, 3]

        Security Warning
        ----------------
        Only decrypt objects from trusted sources. Consider setting XSer.CLASS_ALLOWLIST
        to restrict which classes can be imported during deserialization.
        """
        decrypted_bytes = Encryptor.decrypt_bytes(encrypted_data, key=key, password=password)
        return XSer.from_hdf5_attr(decrypted_bytes)

class CryptoYAML:
    """
    Encrypted YAML file with signature verification for project secrets.

    This class provides a convenient interface for managing encrypted YAML
    configuration files with cryptographic signatures. It uses SignedFile
    for storage and Encryptor for encryption, providing both confidentiality
    and integrity guarantees.

    Features
    --------
    - Automatic encryption and signature verification
    - Support for key files, explicit keys, passwords, and environment variables
    - Dictionary-like interface for accessing secrets
    - Automatic file creation if it doesn't exist

    Parameters
    ----------
    filepath : Union[str, Path]
        Path to the encrypted YAML file.
    key : bytes, optional
        Explicit encryption key. Takes precedence over keyfile and environment.
    keyfile : Union[str, Path], optional
        Path to a key file. If the file exists, the key is loaded; otherwise,
        a new key is generated and saved. Only used if key is not provided.
    password : str, optional
        Password for encryption. Only used if neither key nor keyfile is provided.

    Examples
    --------
    Using a key file (recommended):
        >>> secrets = CryptoYAML("secrets.yaml", keyfile="app.key")
        >>> secrets.data["api_key"] = "sk_test_123"
        >>> secrets.data["database_url"] = "postgres://..."
        >>> secrets.write()

    Using explicit key:
        >>> from encrypt import Encryptor
        >>> key = Encryptor.generate_key()
        >>> secrets = CryptoYAML("secrets.yaml", key=key)
        >>> secrets.data["password"] = "secret123"
        >>> secrets.write()

    Using password:
        >>> secrets = CryptoYAML("secrets.yaml", password="my_secure_password")
        >>> secrets.data["token"] = "xyz789"
        >>> secrets.write()

    Using environment variable (Encryption_SECRET):
        >>> import os
        >>> os.environ['Encryption_SECRET'] = Encryptor.generate_key().decode()
        >>> secrets = CryptoYAML("secrets.yaml")  # Uses env var
        >>> secrets.data["secret"] = "value"
        >>> secrets.write()

    Notes
    -----
    - Requires PyYAML package: pip install pyyaml
    - Files are encrypted with Fernet (AES-128-CBC with HMAC)
    - Signatures use HMAC-SHA256 (proves writer identity)
    - The .data attribute is a dictionary containing the secrets
    """

    def __init__(
        self,
        filepath: Union[str, Path],
        key: Optional[bytes] = None,
        keyfile: Optional[Union[str, Path]] = None,
        password: Optional[str] = None
    ):
        """
        Initialize CryptoYAML with encryption settings.

        Raises
        ------
        ValueError
            If no key, keyfile, password, or environment variable is available.
        """
        self.filepath = Path(filepath).expanduser().resolve()

        # Determine encryption key using precedence order
        if key is not None:
            # Explicit key has highest priority
            self.key = key
            self.password = None
        elif keyfile is not None:
            # Load or generate key from file
            self.key = Encryptor.load_or_generate_key(keyfile)
            self.password = None
        elif password is not None:
            # Use password
            self.key = None
            self.password = password
        else:
            # Check environment variable
            env_key = os.environ.get('Encryption_SECRET')
            if env_key is not None:
                self.key = env_key.encode() if isinstance(env_key, str) else env_key
                self.password = None
            else:
                raise ValueError(
                    "Must provide 'key', 'keyfile', 'password', or set the "
                    "'Encryption_SECRET' environment variable."
                )

        # Initialize data by reading file (or creating empty dict)
        self.read()

    def read(self) -> None:
        """
        Read and decrypt data from the encrypted YAML file.

        If the file exists, it is decrypted and parsed as YAML.
        If the file doesn't exist, an empty dictionary is initialized.

        Raises
        ------
        ValueError
            If the file signature is invalid or decryption fails.
        """
        # Late import to avoid circular dependency
        from signature import SignedFile

        if self.filepath.exists():
            # Read and decrypt the signed file
            if self.key is not None:
                encrypted_yaml = SignedFile.read(self.filepath, decryption_key=self.key)
            else:
                encrypted_yaml = SignedFile.read(self.filepath, decryption_password=self.password)

            # Type assertion: SignedFile.read returns bytes when chunk_size is not specified
            assert isinstance(encrypted_yaml, bytes), "Expected bytes from SignedFile.read"

            # Parse YAML
            if encrypted_yaml:
                self.data = yaml.safe_load(encrypted_yaml.decode('utf-8'))
                if self.data is None:
                    self.data = {}
            else:
                self.data = {}
        else:
            # File doesn't exist - initialize empty dict
            self.data = {}

    def write(self) -> None:
        """
        Encrypt and write the current data to the YAML file with signature.

        The data dictionary is serialized to YAML, encrypted, and written
        to disk with a cryptographic signature.

        Raises
        ------
        ValueError
            If encryption fails.
        """
        # Late import to avoid circular dependency
        from signature import SignedFile

        # Serialize data to YAML bytes
        yaml_bytes = yaml.dump(self.data, encoding='utf-8', allow_unicode=True)

        # Write encrypted and signed file
        if self.key is not None:
            SignedFile.write(self.filepath, yaml_bytes, encryption_key=self.key)
        else:
            SignedFile.write(self.filepath, yaml_bytes, encryption_password=self.password)

    def __repr__(self) -> str:
        """Return string representation of CryptoYAML object."""
        return f"CryptoYAML(filepath={self.filepath}, keys={len(self.data)})"
