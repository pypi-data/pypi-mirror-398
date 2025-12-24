import hashlib
import hmac
import os
import struct
import sys
import tempfile
import base64
from pathlib import Path
from typing import Iterable, BinaryIO, Union, Optional, Iterator, Any, Tuple

# Support both package-relative and direct imports
try:
    from .encrypt import Encryptor
    from .serialization import XSer, XSER_MAGIC
except ImportError:
    from encrypt import Encryptor
    from serialization import XSer, XSER_MAGIC

class SignedFile:
    """
    Atomic file writer with cryptographic integrity verification.

    This class provides utilities for writing and reading files with embedded
    cryptographic signatures. Files are written atomically with a self-describing
    64-byte footer containing metadata and a SHA-256 digest for integrity verification.

    Footer Structure
    ----------------
    The footer is 64 bytes (big-endian) with the following layout:
        - magic (8 bytes): File signature marker (b"SIGFILE1")
        - version (1 byte): Format version number (currently 1)
        - algo_id (1 byte): Hash algorithm identifier (1 = SHA-256, 2 = HMAC-SHA256)
        - data_len (8 bytes): Unsigned 64-bit payload length in bytes
        - digest (32 bytes): SHA-256 hash OR HMAC-SHA256 of the payload
        - tail (8 bytes): Footer terminator (b"ENDSIG!!")
        - flags (1 byte): Bit flags (bit 0: is_encrypted)
        - reserved (5 bytes): Reserved for future use (zeros)

    Authenticated Encryption
    ------------------------
    For encrypted files (flags bit 0 = 1):
        - algo_id is set to 2 (HMAC-SHA256)
        - digest is an HMAC-SHA256 computed with a key derived from the encryption key
        - Only holders of the encryption key can verify authenticity
        - This proves the identity of the writer and prevents decryption of tampered data

    Notes
    -----
    All write operations are atomic, ensuring that files are either fully written
    or not written at all. This prevents partial writes in case of system failures.
    The footer format is fixed at 64 bytes to enable efficient seeking and validation.
    """

    # Footer binary format specification (64 bytes total, big-endian byte order)
    _FOOTER_FMT = ">8sBBQ32s8sBI1s"  # Added I for header_len, reduced padding to 1s
    _FOOTER_SIZE = struct.calcsize(_FOOTER_FMT)

    # Footer field constants
    _MAGIC = b"SIGFILE1"
    _TAIL = b"ENDSIG!!"
    _VERSION = 1
    _ALGO_SHA256 = 1
    _ALGO_HMAC_SHA256 = 2

    # Flag bits
    _FLAG_ENCRYPTED = 0x01

    @staticmethod
    def _fsync_file(file_descriptor: int) -> None:
        """
        Flush file data to disk in a platform-independent way.

        Parameters
        ----------
        file_descriptor : int
            File descriptor to sync.

        Notes
        -----
        On Windows, this uses ctypes to call FlushFileBuffers.
        On Unix-like systems, this uses os.fsync.
        """
        if sys.platform == 'win32':
            # Windows-specific fsync using ctypes
            try:
                import ctypes
                import msvcrt

                # Get Windows file handle from file descriptor
                handle = msvcrt.get_osfhandle(file_descriptor)

                # Call FlushFileBuffers
                if ctypes.windll.kernel32.FlushFileBuffers(handle) == 0:
                    raise OSError("FlushFileBuffers failed")
            except (ImportError, AttributeError, OSError):
                # Fallback to standard fsync (may not work on all Windows versions)
                os.fsync(file_descriptor)
        else:
            # Unix-like systems
            os.fsync(file_descriptor)

    @staticmethod
    def _fsync_directory(directory_path: Path) -> None:
        """
        Flush directory metadata to disk in a platform-independent way.

        Parameters
        ----------
        directory_path : Path
            Directory path to sync.

        Notes
        -----
        On Windows, directory fsync is not supported and is skipped.
        On Unix-like systems, this opens the directory and calls fsync.
        This ensures that directory entries are persisted after file operations.
        """
        if sys.platform == 'win32':
            # Windows doesn't support directory fsync
            # Windows file system semantics are different - metadata updates
            # are generally synchronous, so this operation is not needed
            return

        try:
            # Unix-like systems: open directory and fsync
            dir_fd = os.open(str(directory_path), os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except (OSError, AttributeError):
            # Some filesystems or systems may not support this
            pass

    @staticmethod
    def _iter_chunks(data: Union[bytes, bytearray, memoryview, Iterable[bytes], BinaryIO], chunk_size: int = 1024 * 1024):
        """
        Generate byte chunks from various input data types.

        Parameters
        ----------
        data : Union[bytes, bytearray, memoryview, Iterable[bytes], BinaryIO]
            Input data to be chunked. Can be raw bytes, a file-like object,
            or an iterable of byte chunks.
        chunk_size : int, optional
            Size of chunks to read from file-like objects in bytes.
            Default is 1 MiB (1024 * 1024 bytes).

        Yields
        ------
        bytes
            Successive chunks of the input data.

        Raises
        ------
        TypeError
            If the input iterable yields non-bytes-like objects.

        Notes
        -----
        This method handles three input types:
        1. Bytes-like objects: yields the entire object as a single chunk
        2. File-like objects: reads and yields chunks of specified size
        3. Iterables: validates and yields each element as bytes
        """
        if isinstance(data, (bytes, bytearray, memoryview)):
            yield bytes(data)
            return

        # Handle file-like objects with a read() method
        read = getattr(data, "read", None)
        if callable(read):
            while True:
                chunk = data.read(chunk_size) # type: ignore[arg-type]
                if not chunk:
                    break
                yield chunk
            return

        # Handle iterables of byte chunks
        for chunk in data:  # type: ignore[assignment]
            if not isinstance(chunk, (bytes, bytearray, memoryview)):
                raise TypeError("Iterable must yield bytes-like chunks.")
            yield bytes(chunk)

    @staticmethod
    def _derive_hmac_key(encryption_key: Optional[bytes] = None, encryption_password: Optional[str] = None) -> bytes:
        """
        Derive an HMAC key from encryption key or password.

        Parameters
        ----------
        encryption_key : bytes, optional
            Fernet encryption key. If provided, password is ignored.
        encryption_password : str, optional
            Password for encryption. Only used if key is not provided.

        Returns
        -------
        bytes
            32-byte HMAC key derived from the encryption credentials.

        Notes
        -----
        For key-based encryption, the HMAC key is derived by hashing the Fernet key.
        For password-based encryption, the HMAC key is derived by hashing the password.
        This ensures the HMAC is cryptographically bound to the encryption credentials.
        """
        if encryption_key is not None:
            # Derive HMAC key from Fernet key
            return hashlib.sha256(b"HMAC_KEY:" + encryption_key).digest()
        elif encryption_password is not None:
            # Derive HMAC key from password
            return hashlib.sha256(b"HMAC_KEY:" + encryption_password.encode('utf-8')).digest()
        else:
            raise ValueError("Either encryption_key or encryption_password must be provided")

    @staticmethod
    def _pack_footer(payload_len: int, digest: bytes, is_encrypted: bool = False, header_len: int = 0) -> bytes:
        """
        Serialize footer metadata and digest into binary format.

        Parameters
        ----------
        payload_len : int
            Length of the file payload in bytes (excluding footer).
        digest : bytes
            SHA-256 hash or HMAC-SHA256 of the payload (32 bytes).
        is_encrypted : bool, optional
            Whether the file is encrypted (default False).
        header_len : int, optional
            Length of the header in bytes (default 0).

        Returns
        -------
        bytes
            64-byte binary footer structure.
        """
        algo_id = SignedFile._ALGO_HMAC_SHA256 if is_encrypted else SignedFile._ALGO_SHA256
        flags = SignedFile._FLAG_ENCRYPTED if is_encrypted else 0

        return struct.pack(
            SignedFile._FOOTER_FMT,
            SignedFile._MAGIC,
            SignedFile._VERSION,
            algo_id,
            payload_len,
            digest,
            SignedFile._TAIL,
            flags,
            header_len,
            b"\x00",  # 1 byte padding
        )

    @staticmethod
    def _unpack_footer(buf: bytes) -> Tuple[int, bytes, bool, int, int]:
        """
        Deserialize and validate footer from binary format.

        Parameters
        ----------
        buf : bytes
            64-byte binary footer data.

        Returns
        -------
        tuple[int, bytes, bool, int, int]
            A tuple containing:
            - data_len (int): Length of the payload in bytes
            - digest (bytes): SHA-256 hash or HMAC-SHA256 of the payload
            - is_encrypted (bool): Whether the file is encrypted
            - algo_id (int): Algorithm identifier (1=SHA-256, 2=HMAC-SHA256)
            - header_len (int): Length of the header in bytes

        Raises
        ------
        ValueError
            If the footer magic bytes or tail are incorrect, indicating the file
            is not a valid SignedFile, or if the version or algorithm ID are unsupported.
        """
        magic, version, algo, data_len, digest, tail, flags, header_len, _ = struct.unpack(SignedFile._FOOTER_FMT, buf)

        if magic != SignedFile._MAGIC or tail != SignedFile._TAIL:
            raise ValueError("Footer magic/tail mismatch; not a SignedFile.")
        if version != SignedFile._VERSION:
            raise ValueError(f"Unsupported footer version: {version}.")
        if algo not in (SignedFile._ALGO_SHA256, SignedFile._ALGO_HMAC_SHA256):
            raise ValueError(f"Unsupported digest algorithm id: {algo}.")

        is_encrypted = bool(flags & SignedFile._FLAG_ENCRYPTED)

        return data_len, digest, is_encrypted, algo, header_len

    @staticmethod
    def write(
        path: Union[str, Path],
        data: Union[bytes, bytearray, memoryview, Iterable[bytes], BinaryIO, Any],
        encryption_key: Optional[bytes] = None,
        encryption_password: Optional[str] = None,
        signature_as_comment: bool = False,
        header: Optional[Any] = None
    ) -> None:
        """
        Atomically write data to a file with cryptographic integrity footer.

        This method writes data to the specified path with an embedded SHA-256
        signature footer. The write is atomic, meaning the file will either be
        completely written or not written at all, preventing partial writes
        during system failures.

        Automatically detects whether data is bytes or a Python object. If it's
        a Python object (not bytes-like), it will be serialized using XSer before
        writing, allowing transparent storage of complex objects like dicts with
        numpy arrays, datetime objects, etc.

        Optionally encrypts the data before writing, with signature verification
        performed on the encrypted payload. This ensures integrity verification
        can occur before decryption, proving authenticity without exposing data.

        Parameters
        ----------
        path : Union[str, Path]
            Destination file path where the signed data will be written.
        data : Union[bytes, bytearray, memoryview, Iterable[bytes], BinaryIO, Any]
            Data to write. Can be raw bytes, a file-like object, an iterable
            yielding byte chunks, or any Python object (which will be serialized
            with XSer automatically).
        encryption_key : bytes, optional
            Fernet encryption key for encrypting the data. If provided,
            encryption_password is ignored.
        encryption_password : str, optional
            Password for encrypting the data. Only used if encryption_key
            is not provided.
        signature_as_comment : bool, optional
            If True, prepend the signature footer with '# ' to make it a comment.
            This allows files (like CSV) to be read by standard tools that ignore
            comments, while still maintaining integrity verification. Only works
            for non-encrypted files. Default is False.
        header : Any, optional
            Optional header data to prepend to the file. Can be any Python object
            (will be serialized with XSer). When signature_as_comment=True, the
            header is formatted as a comment line. The header size is tracked in
            the footer for proper separation. Default is None.

        Returns
        -------
        None

        Notes
        -----
        The write process follows these steps:
        1. Detect if data is bytes or a Python object
        2. If object, serialize with XSer (supports numpy, datetime, etc.)
        3. Create a temporary file in the same directory as the target
        4. Optionally encrypt the data
        5. Write data chunks while computing SHA-256 hash
        6. Append the integrity footer (digest of encrypted data if encrypted)
        7. Sync file contents to disk (fsync)
        8. Atomically replace the target file
        9. Sync directory entry to disk (platform-dependent)

        The atomic replacement (step 8) ensures that readers will never see
        a partially written file.

        When encryption is used, the SHA-256 digest in the footer covers the
        encrypted payload, allowing signature verification before decryption.

        Examples
        --------
        Write raw bytes (unencrypted signed file):
            >>> SignedFile.write("data.bin", b"hello world")

        Write Python object (automatically serialized):
            >>> data = {"users": ["alice", "bob"], "count": 42}
            >>> SignedFile.write("data.bin", data)

        Write Python object with numpy array:
            >>> import numpy as np
            >>> data = {"array": np.array([1, 2, 3]), "value": 42}
            >>> SignedFile.write("data.bin", data)

        Write encrypted signed file with key:
            >>> key = Encryptor.generate_key()
            >>> SignedFile.write("data.bin", b"secret", encryption_key=key)

        Write encrypted Python object with password:
            >>> data = {"secret": "value"}
            >>> SignedFile.write("data.bin", data, encryption_password="pass123")

        Write CSV with commented signature (readable by standard CSV readers):
            >>> import pandas as pd
            >>> df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
            >>> csv_data = df.to_csv(index=False).encode()
            >>> SignedFile.write("data.csv", csv_data, signature_as_comment=True)
            >>> # Can be read by pandas: pd.read_csv("data.csv") - ignores comment line

        Write with metadata header:
            >>> metadata = {"created": datetime.now(), "version": "1.0"}
            >>> SignedFile.write("data.bin", data, header=metadata)
            >>> data, meta = SignedFile.read("data.bin", return_header=True)
        """
        path = Path(path)

        # Process header if provided
        header_bytes = b""
        header_len = 0
        if header is not None:
            # Serialize header with XSer
            header_bytes = XSer.to_hdf5_attr(header)
            header_len = len(header_bytes)

        # Detect if data is bytes-like or a Python object
        is_bytes_like = isinstance(data, (bytes, bytearray, memoryview))
        is_iterable_bytes = False

        # Check if it's an iterable of bytes or a file-like object
        if not is_bytes_like:
            # Check for file-like object (has read method)
            if hasattr(data, 'read') and callable(getattr(data, 'read')):
                is_iterable_bytes = True
            # Check if it's an iterable (but not string)
            elif hasattr(data, '__iter__') and not isinstance(data, (str, bytes)):
                try:
                    # Peek at first element if possible
                    iter_data = iter(data)
                    first = next(iter_data, None)
                    if first is not None and isinstance(first, (bytes, bytearray, memoryview)):
                        is_iterable_bytes = True
                        # Reconstruct the iterable with the first element
                        data = [first] + list(iter_data)
                except (TypeError, StopIteration):
                    pass

        # Convert data to bytes
        if is_bytes_like or is_iterable_bytes:
            # Raw bytes or bytes iterable - use as is
            data_bytes = b"".join(SignedFile._iter_chunks(data)) # type: ignore[arg-type]
        else:
            # Python object - serialize with XSer
            data_bytes = XSer.to_hdf5_attr(data)

        # Payload is data only (header is stored separately)
        payload_bytes = data_bytes
        payload_len = len(payload_bytes)

        # Determine if encryption is enabled
        is_encrypted = encryption_key is not None or encryption_password is not None

        # Validate signature_as_comment usage
        if signature_as_comment and is_encrypted:
            raise ValueError(
                "signature_as_comment cannot be used with encrypted files. "
                "Encrypted files are not human-readable regardless of comment format."
            )

        # Encrypt payload if encryption key or password provided
        if is_encrypted:
            payload_bytes = Encryptor.encrypt_bytes(
                payload_bytes,
                key=encryption_key,
                password=encryption_password
            )
            payload_len = len(payload_bytes)

        # Compute digest (HMAC for encrypted files, SHA-256 for unencrypted)
        if is_encrypted:
            # For encrypted files, compute HMAC with key derived from encryption credentials
            hmac_key = SignedFile._derive_hmac_key(encryption_key, encryption_password)
            digest = hmac.new(hmac_key, payload_bytes, hashlib.sha256).digest()
        else:
            # For unencrypted files, compute regular SHA-256 hash
            digest = hashlib.sha256(payload_bytes).digest()

        # Create temporary file in the same directory to ensure atomic replacement
        # across filesystems (os.replace requires same filesystem)
        with tempfile.NamedTemporaryFile("wb", dir=str(path.parent), delete=False) as tf:
            tmp_name = tf.name

            # Write header if present
            if header_len > 0:
                if signature_as_comment:
                    # Write as base64-encoded comment
                    tf.write(b"# HEADER: ")
                    encoded_header = base64.b64encode(header_bytes)
                    tf.write(encoded_header)
                    tf.write(b"\n")
                else:
                    # Write as binary before payload
                    tf.write(header_bytes)

            # Write (possibly encrypted) payload
            tf.write(payload_bytes)

            # Write footer with appropriate digest and header length
            footer = SignedFile._pack_footer(payload_len, digest, is_encrypted, header_len)

            # If signature_as_comment is enabled, base64-encode and format as comment
            # This ensures the signature is printable ASCII on a single line
            if signature_as_comment:
                # Ensure we're on a new line
                tf.write(b"\n")
                tf.write(b"# SIGNATURE: ")
                # Base64-encode the footer to make it printable ASCII
                encoded_footer = base64.b64encode(footer)
                tf.write(encoded_footer)
                tf.write(b"\n")
            else:
                tf.write(footer)
            tf.flush()
            SignedFile._fsync_file(tf.fileno())

        # Perform atomic file replacement and sync directory metadata
        os.replace(tmp_name, path)
        SignedFile._fsync_directory(path.parent)

    @staticmethod
    def _read_footer(path: Path) -> Tuple[bytes, int, bool, int]:
        """
        Read and detect footer from file, handling both regular and commented signatures.

        Returns
        -------
        tuple[bytes, int, bool, int]
            A tuple of (footer_bytes, footer_start_offset, is_commented, header_offset)
            header_offset is the position where header ends (or 0 if no header)
        """
        size = path.stat().st_size

        if size < SignedFile._FOOTER_SIZE:
            raise ValueError("File too small to contain a valid footer.")

        with path.open("rb") as f:
            # Try reading commented signature (base64-encoded)
            # Format: "# HEADER: <base64>\n[data]\n# SIGNATURE: <base64>\n"
            # Read last portion of file to check for commented signature
            read_size = min(size, SignedFile._FOOTER_SIZE * 2 + 200)  # Extra space for comment
            f.seek(size - read_size, os.SEEK_SET)
            tail = f.read(read_size)

            # Look for "# SIGNATURE: " marker
            sig_marker = b"# SIGNATURE: "
            header_offset = 0

            if sig_marker in tail:
                # Find the marker position
                marker_pos = tail.rfind(sig_marker)
                # Extract everything after the marker until the final newline
                after_marker = tail[marker_pos + len(sig_marker):]
                # Remove trailing newline if present
                if after_marker.endswith(b'\n'):
                    after_marker = after_marker[:-1]

                # Decode base64
                try:
                    footer = base64.b64decode(after_marker)
                    # Calculate the data length (everything before "\n# SIGNATURE:")
                    comment_start = size - read_size + marker_pos - 1  # -1 for the \n before #

                    # Check if there's a header at the beginning of the file
                    f.seek(0, os.SEEK_SET)
                    first_line = f.read(200)  # Read enough to check for header
                    header_marker = b"# HEADER: "
                    if first_line.startswith(header_marker):
                        # Find end of first line
                        newline_pos = first_line.find(b'\n')
                        if newline_pos > 0:
                            header_offset = newline_pos + 1  # Position after the header line

                    return footer, comment_start, True, header_offset
                except Exception:
                    pass  # Not a valid base64-encoded signature, fall through

            # Not commented, read regular footer
            f.seek(size - SignedFile._FOOTER_SIZE, os.SEEK_SET)
            footer = f.read(SignedFile._FOOTER_SIZE)
            return footer, size - SignedFile._FOOTER_SIZE, False, 0

    @staticmethod
    def is_signed(path: Union[str, Path]) -> bool:
        """
        Check if a file has a valid SignedFile signature footer.

        This method performs a quick check by reading only the footer bytes
        and validating the structure. It does NOT verify the cryptographic
        signature or read the file contents.

        Parameters
        ----------
        path : Union[str, Path]
            Path to the file to check.

        Returns
        -------
        bool
            True if the file has a valid SignedFile footer structure,
            False otherwise (including if file doesn't exist or is too small).
        """
        try:
            path = Path(path)
            footer, _, _, _ = SignedFile._read_footer(path)
            SignedFile._unpack_footer(footer)  # Validates magic, version, algo
            return True
        except Exception:
            return False

    @staticmethod
    def verify(
        path: Union[str, Path],
        decryption_key: Optional[bytes] = None,
        decryption_password: Optional[str] = None
    ) -> bool:
        """
        Verify the cryptographic integrity and authenticity of a signed file.

        This method validates the file footer structure, checks that the recorded
        payload length matches the actual file size, and verifies the digest
        (SHA-256 for unencrypted files, HMAC-SHA256 for encrypted files).

        For encrypted files, you MUST provide the decryption_key or decryption_password
        to verify authenticity. This proves the identity of the writer, as only someone
        with the correct encryption credentials could have created a valid HMAC.

        Parameters
        ----------
        path : Union[str, Path]
            Path to the signed file to verify.
        decryption_key : bytes, optional
            Fernet decryption key for encrypted files. Required for encrypted files.
        decryption_password : str, optional
            Password for encrypted files. Required if decryption_key not provided
            and file is encrypted.

        Returns
        -------
        bool
            True if all integrity checks pass.

        Raises
        ------
        ValueError
            If any integrity check fails, including:
            - File is too small to contain a valid footer
            - Footer structure is invalid
            - Recorded payload length doesn't match file size
            - Digest/HMAC mismatch (corruption, tampering, or wrong key)
            - Unexpected end-of-file during validation
            - File is encrypted but no decryption credentials provided

        Notes
        -----
        For unencrypted files, this method reads the entire file payload to compute
        the SHA-256 hash, which may be slow for very large files.

        For encrypted files, this method computes an HMAC using the encryption key,
        proving that only someone with the correct key could have created this file.
        This provides both integrity and authenticity verification.

        Examples
        --------
        Verify unencrypted file:
            >>> SignedFile.verify("data.bin")

        Verify encrypted file with key:
            >>> key = Encryptor.generate_key()
            >>> SignedFile.verify("encrypted.bin", decryption_key=key)

        Verify encrypted file with password:
            >>> SignedFile.verify("encrypted.bin", decryption_password="pass123")
        """
        path = Path(path)

        # Read footer (handles both commented and regular footers)
        footer, footer_offset, is_commented, header_file_offset = SignedFile._read_footer(path)
        data_len, expect_digest, is_encrypted, _, header_len = SignedFile._unpack_footer(footer)

        size = path.stat().st_size

        # For commented headers, adjust the footer offset
        actual_data_start = header_file_offset if (is_commented and header_len > 0) else 0

        # Verify that the recorded payload length matches the actual file size
        # In non-commented mode: file has header + payload + footer
        # In commented mode: header is a comment line before payload
        if is_commented:
            expected_payload_len = footer_offset - actual_data_start
        else:
            # For non-commented: payload starts after header
            expected_payload_len = footer_offset - header_len

        if data_len != expected_payload_len:
            raise ValueError("Recorded payload length does not match file size.")

        # For encrypted files, require decryption credentials
        if is_encrypted and decryption_key is None and decryption_password is None:
            raise ValueError(
                "File is encrypted. Verification requires decryption_key or "
                "decryption_password to prove authenticity."
            )

        # Calculate where payload data starts (after header if present)
        if is_commented:
            payload_start = actual_data_start
        else:
            payload_start = header_len

        with path.open("rb") as f:
            # Read payload data (skip header)
            f.seek(payload_start, os.SEEK_SET)
            payload_data = f.read(data_len)
            if len(payload_data) != data_len:
                raise ValueError("Unexpected EOF while reading payload.")

        # Compute and verify digest based on file type
        if is_encrypted:
            # For encrypted files, verify HMAC (proves authenticity via encryption key)
            hmac_key = SignedFile._derive_hmac_key(decryption_key, decryption_password)
            computed_digest = hmac.new(hmac_key, payload_data, hashlib.sha256).digest()
        else:
            # For unencrypted files, verify SHA-256 hash
            computed_digest = hashlib.sha256(payload_data).digest()

        # Verify the computed digest matches the expected digest
        if computed_digest != expect_digest:
            if is_encrypted:
                raise ValueError(
                    "HMAC mismatch; file is corrupted, tampered, or wrong "
                    "encryption key/password provided."
                )
            else:
                raise ValueError("Digest mismatch; file is corrupted or tampered.")

        return True
    
    @staticmethod
    def read(
        path: Union[str, Path],
        verify: bool = True,
        allow_unsigned: bool = False,
        chunk_size: Optional[int] = None,
        decryption_key: Optional[bytes] = None,
        decryption_password: Optional[str] = None,
        return_header: bool = False
    ) -> Union[bytes, Iterator[bytes], Any, Tuple[Any, Any]]:
        """
        Read payload data from a signed or unsigned file, with optional decryption.

        This method reads the payload data from a file, optionally verifying its
        cryptographic signature and decrypting the content. It supports both complete
        reads and chunked streaming reads for memory-efficient processing of large files.

        When both verification and decryption are enabled, verification occurs BEFORE
        decryption. This ensures the encrypted payload's integrity and authenticity
        are confirmed before exposing the decrypted data.

        Parameters
        ----------
        path : Union[str, Path]
            Path to the file to read.
        verify : bool, optional
            If True (default), verify the SHA-256 signature for signed files.
            If False, skip verification but still parse the footer if present.
        allow_unsigned : bool, optional
            If True, allow reading files without valid signatures.
            If False (default), raise ValueError for unsigned or invalid files.
        chunk_size : int, optional
            If specified, return an iterator yielding chunks of this size in bytes
            instead of loading the entire file into memory. Useful for large files.
            Note: When decryption is enabled, chunk_size is ignored and the full
            decrypted data is returned as bytes.
        decryption_key : bytes, optional
            Fernet decryption key for decrypting the data. If provided,
            decryption_password is ignored.
        decryption_password : str, optional
            Password for decrypting the data. Only used if decryption_key
            is not provided.
        return_header : bool, optional
            If True, return a tuple of (data, header). If False (default), return
            only the data. If no header exists, header will be None.

        Returns
        -------
        Union[bytes, Iterator[bytes], Any, Tuple[Any, Any]]
            If return_header=False (default):
                Returns the data (deserialized if XSer, otherwise bytes/iterator)
            If return_header=True:
                Returns tuple of (data, header) where header is None if no header exists

            Data can be:
            - Deserialized Python object if XSer-encoded
            - Complete payload as bytes (if chunk_size is None or decryption enabled)
            - Iterator yielding byte chunks (if chunk_size specified and no decryption)

        Raises
        ------
        ValueError
            If any of the following conditions occur:
            - File is too small to contain a footer and allow_unsigned is False
            - Footer is invalid and allow_unsigned is False
            - Payload length doesn't match file size and allow_unsigned is False
            - SHA-256 verification fails when verify is True
            - Unexpected end-of-file during reading
            - Decryption fails (wrong key/password or corrupted data)

        Notes
        -----
        The method automatically detects whether a file is signed by attempting
        to parse the footer. For unsigned files, it reads the entire file content.
        For signed files, it reads only the payload, excluding the footer.

        When using chunk_size WITHOUT decryption, verification (if enabled) occurs
        after all chunks have been yielded. Any integrity errors will be raised as
        the iterator is exhausted, not during iteration.

        When decryption is enabled:
        1. The encrypted payload is read
        2. Signature verification occurs (if verify=True)
        3. Only after verification succeeds, the payload is decrypted
        4. Decrypted data is returned

        This ensures you never decrypt tampered or corrupted data.

        Examples
        --------
        Read entire file with verification (bytes):
            >>> data = SignedFile.read("signed.dat")

        Read Python object (automatically deserialized):
            >>> obj = SignedFile.read("data.bin")  # Returns dict/list/etc if XSer-encoded

        Read and decrypt with key:
            >>> key = Encryptor.generate_key()
            >>> data = SignedFile.read("encrypted.dat", decryption_key=key)

        Read and decrypt with password:
            >>> data = SignedFile.read("encrypted.dat", decryption_password="pass123")

        Read and decrypt Python object:
            >>> key = Encryptor.generate_key()
            >>> obj = SignedFile.read("encrypted_obj.bin", decryption_key=key)

        Read file in 1MB chunks (no decryption, raw bytes only):
            >>> for chunk in SignedFile.read("large.dat", chunk_size=1024*1024):
            ...     process(chunk)

        Read unsigned file:
            >>> data = SignedFile.read("unsigned.txt", allow_unsigned=True)
        """
        path = Path(path)
        size = path.stat().st_size

        # Attempt to parse footer and determine if the file is signed
        is_signed = False
        data_len = size
        expect_digest = None
        file_is_encrypted = False
        is_commented = False
        header_len = 0
        read_header = None
        header_file_offset = 0

        # Try to read footer (handles both commented and regular)
        if size >= SignedFile._FOOTER_SIZE:
            try:
                footer, footer_offset, is_commented, header_file_offset = SignedFile._read_footer(path)
                data_len, expect_digest, file_is_encrypted, _, header_len = SignedFile._unpack_footer(footer)

                # For commented headers, adjust the footer offset
                actual_data_start = header_file_offset if (is_commented and header_len > 0) else 0

                # Calculate expected payload length
                # In non-commented mode: file has header + payload + footer
                # In commented mode: header is a comment line before payload
                if is_commented:
                    expected_payload_len = footer_offset - actual_data_start
                else:
                    # For non-commented: payload starts after header
                    expected_payload_len = footer_offset - header_len

                # Validate that payload length matches file structure
                if data_len == expected_payload_len:
                    is_signed = True
                elif not allow_unsigned:
                    raise ValueError("Recorded payload length does not match file size.")

                # Read header if present
                if return_header and is_signed and header_len > 0:
                    with path.open("rb") as f:
                        if is_commented:
                            # Header is base64-encoded as a comment line
                            # Format: # HEADER: <base64>\n
                            first_line = f.readline()
                            if first_line.startswith(b"# HEADER: "):
                                encoded_header = first_line[10:].rstrip(b"\n")
                                header_bytes = base64.b64decode(encoded_header)
                                read_header = XSer.from_hdf5_attr(header_bytes)
                        else:
                            # Header is at the start of the file (before payload)
                            header_bytes = f.read(header_len)
                            if len(header_bytes) == header_len:
                                read_header = XSer.from_hdf5_attr(header_bytes)

            except ValueError:
                if not allow_unsigned:
                    raise
        elif not allow_unsigned:
            raise ValueError("File too small to contain a valid footer.")

        # Determine if decryption is requested
        needs_decryption = decryption_key is not None or decryption_password is not None

        # For encrypted files, require decryption credentials for verification
        if verify and is_signed and file_is_encrypted and not needs_decryption:
            raise ValueError(
                "File is encrypted. Verification requires decryption_key or "
                "decryption_password to prove authenticity before reading."
            )

        # Calculate where payload data starts (after header if present)
        payload_start = 0
        if is_signed and header_len > 0:
            if is_commented:
                # Header is a comment line, payload starts after it
                assert isinstance(header_file_offset, int)
                payload_start = header_file_offset
            else:
                # Header is binary before payload
                payload_start = header_len

        # Read file data (unified handling for signed and unsigned files)
        # Note: Chunked reading is not supported with decryption or encrypted files
        if chunk_size is not None and not needs_decryption and not file_is_encrypted:
            # Return iterator for memory-efficient chunked reading (unencrypted files only)
            def _read_chunks():
                hasher = hashlib.sha256() if (verify and is_signed) else None
                with path.open("rb") as f:
                    f.seek(payload_start)
                    remaining = data_len
                    while remaining > 0:
                        to_read = min(chunk_size, remaining)
                        chunk = f.read(to_read)
                        if not chunk:
                            raise ValueError("Unexpected EOF while reading payload.")
                        if hasher:
                            hasher.update(chunk)
                        remaining -= len(chunk)
                        yield chunk

                    # Verify integrity after all chunks have been read
                    if hasher and expect_digest:
                        if hasher.digest() != expect_digest:
                            raise ValueError("Digest mismatch; file is corrupted or tampered.")

            if return_header:
                raise ValueError("return_header=True is not supported with chunk_size (chunked reading)")
            return _read_chunks()
        else:
            # Read entire payload into memory
            with path.open("rb") as f:
                f.seek(payload_start)
                data = f.read(data_len)
                if len(data) != data_len:
                    raise ValueError("Unexpected EOF while reading payload.")

            # Verify integrity BEFORE decryption if requested and file is signed
            # This ensures we only decrypt authenticated data
            if verify and is_signed:
                # Call verify() to handle all verification logic
                # This eliminates code duplication
                SignedFile.verify(path, decryption_key=decryption_key, decryption_password=decryption_password)

            # Decrypt data if file is encrypted and decryption requested
            if file_is_encrypted and needs_decryption:
                data = Encryptor.decrypt_bytes(
                    data,
                    key=decryption_key,
                    password=decryption_password
                )
            elif file_is_encrypted and not needs_decryption:
                # File is encrypted but no decryption requested - return encrypted data
                pass

            # Check if data is XSer-encoded and deserialize if so
            if len(data) >= len(XSER_MAGIC) and data[:len(XSER_MAGIC)] == XSER_MAGIC:
                try:
                    deserialized_data = XSer.from_hdf5_attr(data)
                    if return_header:
                        return deserialized_data, read_header
                    return deserialized_data
                except (ValueError, RuntimeError):
                    # Failed to deserialize, return raw bytes
                    pass

            if return_header:
                return data, read_header
            return data



# ============================================================================
# Usage Examples
# ============================================================================
#
# Write a signed file:
#     SignedFile.write("example.bin", b"hello world")
#
# Read and verify a signed file:
#     data = SignedFile.read("example.bin")
#
# Read without verification:
#     data = SignedFile.read("example.bin", verify=False)
#
# Read unsigned file:
#     data = SignedFile.read("plain.txt", allow_unsigned=True)
#
# Read large file in chunks:
#     for chunk in SignedFile.read("large.dat", chunk_size=1024*1024):
#         process(chunk)
#
# Verify integrity explicitly:
#     try:
#         SignedFile.verify("example.bin")
#         print("File integrity verified successfully")
#     except ValueError as e:
#         print(f"Integrity check failed: {e}")
#
# Write encrypted signed file with key:
#     key = Encryptor.generate_key()
#     SignedFile.write("secret.bin", b"confidential data", encryption_key=key)
#
# Write encrypted signed file with password:
#     SignedFile.write("secret.bin", b"confidential data", encryption_password="my_password")
#
# Read and decrypt with verification (key-based):
#     key = Encryptor.generate_key()
#     data = SignedFile.read("secret.bin", decryption_key=key)
#
# Read and decrypt with verification (password-based):
#     data = SignedFile.read("secret.bin", decryption_password="my_password")
#
# Verify encrypted file (requires encryption key - proves authenticity):
#     try:
#         key = Encryptor.generate_key()
#         SignedFile.verify("secret.bin", decryption_key=key)
#         print("Encrypted file HMAC verified - proves writer identity")
#     except ValueError as e:
#         print(f"HMAC verification failed: {e}")
#
# Security workflow - verify authenticity with key before decrypt:
#     try:
#         key = Encryptor.generate_key()
#
#         # First verify the HMAC (proves identity of writer via encryption key)
#         SignedFile.verify("secret.bin", decryption_key=key)
#         print("HMAC valid - writer identity verified")
#
#         # Then decrypt (read() verifies HMAC again automatically)
#         data = SignedFile.read("secret.bin", decryption_key=key)
#         print("Data decrypted successfully")
#     except ValueError as e:
#         print(f"Security check failed: {e}")
#
# Why this matters - wrong key detection:
#     key1 = Encryptor.generate_key()
#     key2 = Encryptor.generate_key()
#
#     # Write with key1
#     SignedFile.write("secret.bin", b"data", encryption_key=key1)
#
#     # Try to verify with key2 - will fail (proves only key1 holder created this)
#     try:
#         SignedFile.verify("secret.bin", decryption_key=key2)
#     except ValueError:
#         print("Wrong key detected - authenticity proof failed")
#
#     # Only key1 holder can verify and decrypt
#     SignedFile.verify("secret.bin", decryption_key=key1)  # Success!
#     data = SignedFile.read("secret.bin", decryption_key=key1)  # Success!