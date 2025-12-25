import json
import base64

from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import PKCS1_v1_5, PKCS1_OAEP #, AES
from Cryptodome.Signature import pss, pkcs1_15 as pkcs1_15_sig
from Cryptodome.Hash import SHA1, SHA256, SHA384, SHA512, HMAC
from Cryptodome.Random import get_random_bytes

def base64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def base64url_decode(data):
    padding = '=' * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)

class JWK:
    def __init__(
        self,
        kty,

        use = None,
        key_ops = None,
        alg = None,
        kid = None
    ):
        if kty not in [ "EC", "RSA", "oct" ]:
            raise ValueError(f"Unsupported key type {kty}, only supporting EC, RSA and oct")

#        if (use is not None) and (key_ops is not None):
#            raise ValueError("Only use or key_ops can be used at the same time")

        if (use is not None) and (use not in [ "sig", "enc" ]):
            raise ValueError(f"Unsupported usage {use}, supported values are sig and enc")

        if (key_ops is not None):
            if not isinstance(key_ops, list):
                raise ValueError("key_ops has to be a list")
            for kop in key_ops:
                if kop not in [
                    "sign",
                    "verify",
                    "encrypt",
                    "decrypt",
                    "wrapKey",
                    "unwrapKey",
                    "deriveKey",
                    "deriveBits"
                ]:
                    raise ValueError(f"Unsupported key operation {kop}")

        self._kty       = kty

        self._use       = use
        self._key_ops   = key_ops
        self._alg       = alg
        self._kid       = kid

    def get_id(self):
        return self._kid

    def encrypt(self, payload, alg = None):
        if self._use is not None:
            if self._use != "enc":
                raise ValueError("Encryption is not the intended key use for this key")
        if self._key_ops is not None:
            if "encrypt" not in self._key_ops:
                raise ValueError("Encryption is not the intended key operation with this key")

        return self._encrypt(payload, alg)
 
    def decrypt(self, payload, alg = None):
        if self._use is not None:
            if self._use != "enc":
                raise ValueError("Decryption is not the intended key use for this key")
        if self._key_ops is not None:
            if "decrypt" not in self._key_ops:
                raise ValueError("Decryption is not the intended key operation with this key")

        return self._decrypt(payload, alg)

    def sign(self, payload, alg = None):
        # First check use or key_ops to check if we can be used for signature ...
        if self._use is not None:
            if self._use != "sig":
                raise ValueError("Signature is not the intended key use for this key")

        if self._key_ops is not None:
            # Check if "sign" is an allowed key operation
            if "sign" not in self._key_ops:
                raise ValueError("Signing is not an allowed key operation with this key")

        # Call the implementation
        return self._sign(payload, alg = alg)

    def verify(self, payload, signature, alg = None):
        # Verify the given payload against the passed signature using this key
        if self._use is not None:
            if self._use != "sig":
                raise ValueError("Signature is not the intended key use for this key")
        if self._key_ops is not None:
            if "verify" not in self._key_ops:
                raise ValueError("Signature verification is not the intended key use for this key")

        # Call the implementation
        return self._verify(payload, signature, alg = alg)

    def to_json(self, indent = None):
        raise NotImplementedError("JSON serialization is not implemented by this class")

    @staticmethod
    def from_json(jdata):
        # We check which algorithm is specified in the JWK
        if not isinstance(jdata, dict):
            jdata = json.loads(jdata)

        if jdata["kty"] == "RSA":
            return JWK_RSA.from_json(jdata)
        elif jdata["kty"] == "oct":
            return JWK_Shared.from_json(jdata)
        else:
            raise ValueError(f"Unknown key type {jdata['kty']}")

class JWK_Shared(JWK):
    def __init__(
        self,
        secret,
        use = None,
        key_ops = None,
        alg = None,
        kid = None
    ):
        super().__init__(
            kty = "oct",
            use = use,
            key_ops = key_ops,
            alg = alg,
            kid = kid
        )

        self._secret = secret

        self._alg_sig_default = "HS256"

    def get_sign_alg(self):
        if self._alg is not None:
            return self._alg
        else:
            return self._alg_sig_default

    def to_json(self, indent = None):
        jwk = {
            "kty" :     self._kty,
            "k" :       base64url_encode(self._secret),
            "use":      self._use,
            "key_ops":  self._key_ops,
            "alg":      self._alg,
            "kid":      self._kid
        }

        return json.dumps(jwk, indent=indent)

    def _sign(self, payload, alg = None):
        # "alg" for shared secrets can be:
        #   HS256       SHA256
        #   HS384       SHA384
        #   HS512       SHA512

        if alg is None:
            # If there is an algorithm specified for this key we strictly use
            # that one if its not overriden during the signature request

            if self._alg is not None:
                alg = self._alg
            else:
                alg = self._alg_sig_default
        else:
            # We have an alg. override - we just use that one
            pass

        if alg not in [ "HS256", "HS384", "HS512" ]:
            raise ValueError(f"Unknown algorithm {alg} for Shared key")

        # Use and key_ops is checked by base class sign() function

        if alg == "HS256":
            # HS256
            h = HMAC.new(self._secret, digestmod=SHA256) 
            h.update(payload)
            sig = h.digest()
            return sig
        elif alg == "HS384":
            # HS384
            h = HMAC.new(self._secret, digestmod=SHA384) 
            h.update(payload)
            sig = h.digest()
            return sig
        elif alg == "HS512":
            # HS512
            h = HMAC.new(self._secret, digestmod=SHA512) 
            h.update(payload)
            sig = h.digest()
            return sig
        else:
            raise ValueError(f"Alg parameter contains unknown algorithm {self._alg}")

    def _verify(self, payload, signature, alg = None):
        from jws import JWSValidation
        # "alg" for RSA can be:
        #   HS256       SHA256
        #   HS384       SHA384
        #   HS512       SHA512

        if alg is None:
            # If there is an algorithm specified for this key we strictly use
            # that one if its not overriden during the signature request

            if self._alg is not None:
                alg = self._alg
            else:
                alg = self._alg_sig_default
        else:
            # We have an alg. override - we just use that one
            pass

        if alg not in [ "HS256", "HS385", "HS512" ]:
            return JWSValidation.INVALID

        if alg == "HS256":
            h = HMAC.new(self._secret, digestmod=SHA256) 
            h.update(payload)
            try:
                h.verify(signature)
                return JWSValidation.VALID
            except ValueError:
                return JWSValidation.INVALID
        elif alg == "HS384":
            h = HMAC.new(self._secret, digestmod=SHA384) 
            h.update(payload)
            try:
                h.verify(signature)
                return JWSValidation.VALID
            except ValueError:
                return JWSValidation.INVALID
        elif alg == "HS512":
            h = HMAC.new(self._secret, digestmod=SHA512) 
            h.update(payload)
            try:
                h.verify(signature)
                return JWSValidation.VALID
            except ValueError:
                return JWSValidation.INVALID
        else:
            return JWSValidation.INVALID

    @staticmethod
    def from_json(jsondata):
        if not isinstance(jsondata, dict):
            jsondata = json.loads(jsondata)

        if ("kty" not in jsondata) or ("k" not in jsondata) or (("use" not in jsondata) and ("key_ops" not in jsondata)):
            raise ValueError("Invalid JSON object for octet key (missing kty, k, use or key_ops)")
        if jsondata["kty"].upper() != "OCT":
            raise ValueError(f"Key type {jsondata['kty']} is not Octet, cannot parse Octet object")

        # Recover key object if possible

        use = None
        key_ops = None
        alg = None
        kid = None

        if "use" in jsondata:
            use = jsondata["use"]
        if "key_ops" in jsondata:
            key_ops = jsondata["key_ops"]
        if "alg" in jsondata:
            alg = jsondata["alg"]
        if "kid" in jsondata:
            kid = jsondata["kid"]

        secret = base64url_decode(jsondata["k"])

        return JWK_Shared(secret, use, key_ops, alg, kid)

    @staticmethod
    def create(
        secret = None,
        key_id = None,
        use = None,
        key_ops = None,
        alg = None
    ):
        if (use is not None) and (key_ops is not None):
            raise ValueError("Either use or key_ops has to be specified, not both")

        if (use is not None) and (use not in [ "sig", "enc" ]):
            raise ValueError(f"Unsupported usage {use}, supported values are sig and enc")

        if (key_ops is not None):
            if not isinstance(key_ops, list):
                raise ValueError("key_ops has to be a list")
            for kop in key_ops:
                if kop not in [
                    "sign",
                    "verify",
                    "encrypt",
                    "decrypt",
                    "wrapKey",
                    "unwrapKey",
                    "deriveKey",
                    "deriveBits"
                ]:
                    raise ValueError(f"Unsupported key operation {kop}")

        # If no shared secret is specified we create one
        if secret is None:
            secret = get_random_bytes(32)

        # And create the class instance ...
        res = JWK_Shared(
            secret,
            use = use,
            key_ops = key_ops,
            kid = key_id,
            alg = alg
        )

        return res
    

class JWK_RSA(JWK):
    def __init__(
        self,
        bits,
        key,
        use = None,
        key_ops = None,
        alg = None,
        kid = None
    ):
        super().__init__(
            kty = "RSA",
            use = use,
            key_ops = key_ops,
            alg = alg,
            kid = kid
        )

        # GEneric information
        self._bits =            bits    # Number of bits

        # The key itself
        self._key =             key

        self._alg_sig_default = "PS256"
        self._alg_enc_default = "RSA-OAEP-256"

    def get_sign_alg(self):
        if self._alg is not None:
            return self._alg
        else:
            return self._alg_sig_default

    def get_enc_alg(self):
        if self._alg is not None:
            return self._alg
        else:
            return self._alg_enc_default

    def _verify(self, payload, signature, alg = None):
        from jws import JWSValidation
        # "alg" for RSA can be:
        #   PS256       PSS, SHA256
        #   PS384       PSS, SHA384
        #   PS512       PSS, SHA512
        #
        #   RS256       PKCS1-v1.5, SHA256
        #   RS384       PKCS1-v1.5, SHA384
        #   RS512       PKCS1-v1.5, SHA512
        if self._bits < 2048:
            return JWSValidation.INVALID
            #raise ValueError("A minimum key size of 2048 bits is required for signatures")

        if alg is None:
            # If there is an algorithm specified for this key we strictly use
            # that one if its not overriden during the signature request

            if self._alg is not None:
                alg = self._alg
            else:
                alg = self._alg_sig_default
        else:
            # We have an alg. override - we just use that one
            pass

        if alg not in [ "PS256", "PS385", "PS512", "RS256", "RS384", "RS512" ]:
            return JWSValidation.INVALID
            #raise ValueError(f"Unknown algorithm {alg} for RSA key")

        # Use and key_ops is checked by base class verify() function

        if alg == "PS256":
            # SHA256, PSS
            h = SHA256.new(payload)
            try:
                pss.new(self._key).verify(h, signature)
                return JWSValidation.VALID
            except ValueError:
                return JWSValidation.INVALID
        elif alg == "PS384":
            # SHA384, PSS
            h = SHA384.new(payload)
            try:
                pss.new(self._key).verify(h, signature)
                return JWSValidation.VALID
            except ValueError:
                return JWSValidation.INVALID
        elif alg == "PS512":
            # SHA512, PSS
            h = SHA512.new(payload)
            try:
                pss.new(self._key).verify(h, signature)
                return JWSValidation.VALID
            except ValueError:
                return JWSValidation.INVALID
        elif alg == "RS256":
            # SHA256, PKCS#1 v1.5
            h = SHA256.new(payload)
            try:
                pkcs1_15_sig.new(self._key).verify(h, signature)
                return JWSValidation.VALID
            except:
                return JWSValidation.INVALID
        elif alg == "RS384":
            # SHA384, PKCS#1 v1.5
            h = SHA384.new(payload)
            try:
                pkcs1_15_sig.new(self._key).verify(h, signature)
                return JWSValidation.VALID
            except:
                return JWSValidation.INVALID
        elif alg == "RS512":
            # SHA512, PKCS#1 v1.5
            h = SHA512.new(payload)
            try:
                pkcs1_15_sig.new(self._key).verify(h, signature)
                return JWSValidation.VALID
            except:
                return JWSValidation.INVALID
        else:
            return JWSValidation.INVALID
            #raise ValueError(f"Alg parameter contains unknown algorithm {self._alg}")

    def _sign(self, payload, alg = None):
        # "alg" for RSA can be:
        #   PS256       PSS, SHA256
        #   PS384       PSS, SHA384
        #   PS512       PSS, SHA512
        #
        #   RS256       PKCS1-v1.5, SHA256
        #   RS384       PKCS1-v1.5, SHA384
        #   RS512       PKCS1-v1.5, SHA512
        if self._bits < 2048:
            raise ValueError("A minimum key size of 2048 bits is required for signature")

        if alg is None:
            # If there is an algorithm specified for this key we strictly use
            # that one if its not overriden during the signature request

            if self._alg is not None:
                alg = self._alg
            else:
                alg = self._alg_sig_default
        else:
            # We have an alg. override - we just use that one
            pass

        if alg not in [ "PS256", "PS385", "PS512", "RS256", "RS384", "RS512" ]:
            raise ValueError(f"Unknown algorithm {alg} for RSA key")

        # Use and key_ops is checked by base class sign() function

        if alg == "PS256":
            # SHA256, PSS
            h = SHA256.new(payload)
            sig = pss.new(self._key).sign(h)
            return sig
        elif alg == "PS384":
            # SHA384, PSS
            h = SHA384.new(payload)
            sig = pss.new(self._key).sign(h)
            return sig
        elif alg == "PS512":
            # SHA512, PSS
            h = SHA512.new(payload)
            sig = pss.new(self._key).sign(h)
            return sig
        elif alg == "RS256":
            # SHA256, PSS
            h = SHA256.new(payload)
            sig = pkcs1_15_sig.new(self._key).sign(h)
            return sig
        elif alg == "RS384":
            # SHA384, PSS
            h = SHA384.new(payload)
            sig = pkcs1_15_sig.new(self._key).sign(h)
            return sig
        elif alg == "RS512":
            # SHA512, PSS
            h = SHA512.new(payload)
            sig = pkcs1_15_sig.new(self._key).sign(h)
            return sig
        else:
            raise ValueError(f"Alg parameter contains unknown algorithm {self._alg}")

    def _encrypt(self, payload, alg = None):
        # "alg" parameter can be:
        #   RSA1_5
        #   RSA-OAEP            SHA1 (?!?!insane)
        #   RSA-OAEP-256        SHA256

        if alg is None:
            # If there is an algorithm specified for this key we strictly use
            # that one if its not overriden during the signature request

            if self._alg is not None:
                alg = self._alg
            else:
                alg = self._alg_enc_default
        else:
            # We have an alg. override - we just use that one
            pass

        if alg not in ["RSA1_5", "RSA-OAEP-256", "RSA-OAEP"]:
            raise ValueError(f"Algorithm {alg} is not supported for encryption with RSA")

        if alg == "RSA-OAEP-256":
            cipher = PKCS1_OAEP.new(self._key.publickey(), hashAlgo=SHA256)
            enc = cipher.encrypt(payload)
            return enc
        elif alg == "RSA-OAEP":
            cipher = PKCS1_OAEP.new(self._key.publickey(), hashAlgo=SHA1)
            enc = cipher.encrypt(payload)
            return enc
        elif alg == "RSA1_5":
            cipher = PKCS1_v1_5.new(self._key.publickey())
            enc = cipher.encrypt(payload)
            return enc
        else:
            raise ValueError(f"Invalid algorithm parameter {alg}")

    def _decrypt(self, payload, alg = None):
        # "alg" parameter can be:
        #   RSA1_5
        #   RSA-OAEP            SHA1 (?!?!insane)
        #   RSA-OAEP-256        SHA256

        if alg is None:
            # If there is an algorithm specified for this key we strictly use
            # that one if its not overriden during the signature request

            if self._alg is not None:
                alg = self._alg
            else:
                alg = self._alg_enc_default
        else:
            # We have an alg. override - we just use that one
            pass

        if alg not in ["RSA1_5", "RSA-OAEP-256", "RSA-OAEP"]:
            raise ValueError(f"Algorithm {alg} is not supported for encryption with RSA")

        if alg == "RSA-OAEP-256":
            cipher = PKCS1_OAEP.new(self._key, hashAlgo=SHA256)
            enc = None
            try:
                enc = cipher.decrypt(payload)
            except:
                enc = None
            return enc
        elif alg == "RSA-OAEP":
            cipher = PKCS1_OAEP.new(self._key, hashAlgo=SHA1)
            enc = None
            try:
                enc = cipher.decrypt(payload)
            except:
                enc = None
            return enc
        elif alg == "RSA1_5":
            cipher = PKCS1_v1_5.new(self._key)
            enc = None
            try:
                enc = cipher.decrypt(payload)
            except:
                enc = None
            return enc
        else:
            raise ValueError(f"Invalid algorithm parameter {alg}")
 
    def to_json(self, indent = None):
        pubkey = self._key.publickey()

        jwk = {
            "kty" :     self._kty,
            "n":        base64url_encode(pubkey.n.to_bytes((pubkey.n.bit_length() + 7) // 8, byteorder='big')),
            "e":        base64url_encode(pubkey.e.to_bytes((pubkey.e.bit_length() + 7) // 8, byteorder='big')),
            "use":      self._use,
            "key_ops":  self._key_ops,
            "alg":      self._alg,
            "kid":      self._kid
        }

        if self._key.has_private():
            jwk.update({
                "d" : base64url_encode(self._key.d.to_bytes((self._key.d.bit_length() + 7) // 8, byteorder='big')),
                "p" : base64url_encode(self._key.p.to_bytes((self._key.p.bit_length() + 7) // 8, byteorder='big')),
                "q" : base64url_encode(self._key.q.to_bytes((self._key.q.bit_length() + 7) // 8, byteorder='big')),
                "dp" : base64url_encode(self._key.dp.to_bytes((self._key.dp.bit_length() + 7) // 8, byteorder='big')),
                "dq" : base64url_encode(self._key.dq.to_bytes((self._key.dq.bit_length() + 7) // 8, byteorder='big')),
                "qi" : base64url_encode(self._key.invq.to_bytes((self._key.invq.bit_length() + 7) // 8, byteorder='big'))
            })

        return json.dumps(jwk, indent=indent)

    @staticmethod
    def from_json(jsondata):
        if not isinstance(jsondata, dict):
            jsondata = json.loads(jsondata)

        if ("kty" not in jsondata) or ("n" not in jsondata) or ("e" not in jsondata) or (("use" not in jsondata) and ("key_ops" not in jsondata)):
            raise ValueError("Invalid JSON object for RSA key (missing kty, n, d, use or key_ops)")
        if jsondata["kty"].upper() != "RSA":
            raise ValueError(f"Key type {jsondata['kty']} is not RSA, cannot parse RSA object")

        # Recover key object if possible

        if ("n" in jsondata) and ("e" in jsondata) and ("d" not in jsondata):
            # Only a public key
            n = int.from_bytes(base64url_decode(jsondata["n"]), byteorder='big')
            e = int.from_bytes(base64url_decode(jsondata["e"]), byteorder='big')
            key = RSA.construct((n, e))
        elif ("n" in jsondata) and ("e" in jsondata) and ("d" in jsondata):
            n = int.from_bytes(base64url_decode(jsondata["n"]), byteorder='big')
            e = int.from_bytes(base64url_decode(jsondata["e"]), byteorder='big')
            d = int.from_bytes(base64url_decode(jsondata["d"]), byteorder='big')
            key = RSA.construct((n, e, d))
        else:
            raise ValueError("Missing components to construct RSA key")

        # "use" and "key_ops" will be checked by the constructor
        bits = key.publickey().n.bit_length()

        use = None
        key_ops = None
        alg = None
        kid = None

        if "use" in jsondata:
            use = jsondata["use"]
        if "key_ops" in jsondata:
            key_ops = jsondata["key_ops"]
        if "alg" in jsondata:
            alg = jsondata["alg"]
        if "kid" in jsondata:
            kid = jsondata["kid"]

        return JWK_RSA(bits, key, use, key_ops, alg, kid)
       

    @staticmethod
    def create(
        bits = 4096,
        key_id = None,
        use = None,
        key_ops = None,
        alg = None
    ):
        bits = int(bits)
        if bits < 1024:
            raise ValueError("RSA key size has to be at least 1024 bits")

        if (use is not None) and (key_ops is not None):
            raise ValueError("Either use or key_ops has to be specified, not both")

        if (use is not None) and (use not in [ "sig", "enc" ]):
            raise ValueError(f"Unsupported usage {use}, supported values are sig and enc")

        if (key_ops is not None):
            if not isinstance(key_ops, list):
                raise ValueError("key_ops has to be a list")
            for kop in key_ops:
                if kop not in [
                    "sign",
                    "verify",
                    "encrypt",
                    "decrypt",
                    "wrapKey",
                    "unwrapKey",
                    "deriveKey",
                    "deriveBits"
                ]:
                    raise ValueError(f"Unsupported key operation {kop}")

        # Actually generate key
        key = RSA.generate(bits)

        # And create the class instance ...
        res = JWK_RSA(
            bits,
            key,
            use = use,
            key_ops = key_ops,
            kid = key_id,
            alg = alg
        )

        return res
