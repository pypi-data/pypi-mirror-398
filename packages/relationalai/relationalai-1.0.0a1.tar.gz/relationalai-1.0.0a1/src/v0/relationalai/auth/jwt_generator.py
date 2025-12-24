import base64
import hashlib
import jwt
from datetime import timedelta, timezone, datetime
from typing import Union, Optional, TYPE_CHECKING

# warehouse-based snowflake notebooks currently don't have hazmat
crypto_disabled = False
try:
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, load_pem_private_key
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519, ed448
except ModuleNotFoundError:
    crypto_disabled = True
    # Define fallback types/functions when cryptography is not available
    Encoding = PublicFormat = load_pem_private_key = default_backend = rsa = ec = ed25519 = ed448 = None

CLAIM_ISSUER = "iss"
CLAIM_EXPIRY = "exp"
CLAIM_ISSUED_AT = "iat"
CLAIM_SUBJECT = "sub"

# AllowedPrivateKeyTypes is defined to allow for proper typing.
# We need to differentiate between runtime and type-checking contexts, as Python 3.9 can
# not check instance types against Unions.
if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519, ed448
    AllowedPrivateKeyTypes = Union[
        rsa.RSAPrivateKey,
        ec.EllipticCurvePrivateKey,
        ed25519.Ed25519PrivateKey,
        ed448.Ed448PrivateKey,
    ]
else:
    if not crypto_disabled:
        AllowedPrivateKeyTypes = (
            rsa.RSAPrivateKey,
            ec.EllipticCurvePrivateKey,
            ed25519.Ed25519PrivateKey,
            ed448.Ed448PrivateKey,
        )
    else:
        AllowedPrivateKeyTypes = tuple()

class JWTGenerator:
    """
    Manages JWT creation, signing, and automatic renewal with configurable lifetimes.
    """
    
    # Token configuration constants
    DEFAULT_TOKEN_LIFETIME = timedelta(minutes=59)
    DEFAULT_RENEWAL_THRESHOLD = timedelta(minutes=54)
    SIGNING_ALGORITHM = "RS256"

    def __init__(
        self, 
        account: str, 
        username: str, 
        private_key_path: str, 
        key_passphrase: Optional[str] = None,
        token_lifetime: timedelta = DEFAULT_TOKEN_LIFETIME, 
        renewal_threshold: timedelta = DEFAULT_RENEWAL_THRESHOLD
    ):
        """
        Initialize JWT authentication generator.
        
        Args:
            account: Account identifier for authentication
            username: User identifier
            private_key_path: Filesystem path to private key file
            key_passphrase: Optional passphrase for encrypted private keys
            token_lifetime: Duration for which tokens remain valid
            renewal_threshold: Time before expiry to trigger renewal
        """
        
        self.account = account.upper()
        self.username = username.upper()
        self.fully_qualified_user = f"{self.account}.{self.username}"

        self.token_lifetime = token_lifetime
        self.renewal_threshold = renewal_threshold
        self._key_file_path = private_key_path
        self._next_renewal_time = datetime.min
        self._cached_token: Optional[str] = None

        self._private_key = self._load_private_key_from_file(key_passphrase)

    def _load_private_key_from_file(self, passphrase: Optional[str]) -> AllowedPrivateKeyTypes:
        if crypto_disabled or load_pem_private_key is None or default_backend is None:
            raise Exception("Cryptography library is not available. please install the 'cryptography' package to enable JWT support.")
        with open(self._key_file_path, "rb") as key_file:
            key_data = key_file.read()

            try:
                private_key = load_pem_private_key(key_data, None, default_backend())
            except TypeError:
                if passphrase is None:
                    raise ValueError("Private key requires passphrase but none provided")
                encoded_passphrase = passphrase.encode("utf-8")
                private_key = load_pem_private_key(key_data, encoded_passphrase, default_backend())

        if not isinstance(private_key, AllowedPrivateKeyTypes):
            raise TypeError(f"Unsupported private key type: {type(private_key)}")

        return private_key

    def get_or_generate_token(self) -> str:
        """
        Generate or return cached JWT access token.
        Automatically renews token when renewal threshold is reached.
        
        Returns:
            Valid JWT access token
        """
        if crypto_disabled:
            raise Exception("Cryptography library is not available. please install the 'cryptography' package to enable JWT support.")

        current_time = datetime.now(timezone.utc)

        # we have a valid cached token
        if self._cached_token and self._next_renewal_time > current_time:
            return self._cached_token

        # Generate public key fingerprint for issuer field
        key_fingerprint = self._compute_public_key_fingerprint()

        # Construct JWT payload
        token_payload = {
            CLAIM_ISSUER: f"{self.fully_qualified_user}.{key_fingerprint}",
            CLAIM_SUBJECT: self.fully_qualified_user,
            CLAIM_ISSUED_AT: current_time,
            CLAIM_EXPIRY: current_time + self.token_lifetime
        }

        # Sign and encode the token
        signed_token = jwt.encode(
            token_payload, 
            key=self._private_key, 
            algorithm=self.SIGNING_ALGORITHM
        )
        
        # Handle byte string response from older PyJWT versions
        if isinstance(signed_token, bytes):
            signed_token = signed_token.decode('utf-8')
            
        self._cached_token = signed_token
        self._next_renewal_time = current_time + self.renewal_threshold

        return self._cached_token

    def _compute_public_key_fingerprint(self) -> str:
        """
        Compute SHA256 fingerprint of the public key.
        
        Returns:
            Base64-encoded SHA256 fingerprint with 'SHA256:' prefix
        """
        if crypto_disabled or Encoding is None or PublicFormat is None:
            raise Exception("Cryptography library is not available. please install the 'cryptography' package to enable JWT support.")
        
        # Extract public key in DER format
        public_key_der = self._private_key.public_key().public_bytes(
            Encoding.DER, 
            PublicFormat.SubjectPublicKeyInfo
        )

        # Compute SHA256 hash
        hasher = hashlib.sha256()
        hasher.update(public_key_der)
        digest = hasher.digest()

        # Encode as base64 with prefix
        fingerprint = 'SHA256:' + base64.b64encode(digest).decode('utf-8')

        return fingerprint