import json
import base64

from jwk import JWK

from Cryptodome.Random import get_random_bytes
from Cryptodome.Cipher import AES
#from Cryptodome.Hash import SHA1, SHA256, SHA384, SHA512, HMAC

def base64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def base64url_decode(data):
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

class JWE:
    def __init__(
        self,

        protected_header = None,
        encrypted_key = None,
        iv = None,
        ciphertext = None,
        auth_tag = None,

        recipients = None,

        payload_raw = None,
        cty = None,
        alg = None,
        enc = None,
        typ = None,

        compact = None
    ):
        self._payload_raw = payload_raw

        self._protected_header = protected_header
        self._encrypted_key = encrypted_key         # Only in compact
        self._iv = iv
        self._ciphertext = ciphertext
        self._auth_tag = auth_tag
        self._recipients = recipients
        self._cty = cty
        self._alg = alg
        self._enc = enc

        self._compact = compact

    def to_json(self, indent = None):
        if self._compact is None:
            return json.dumps({
                "protected" : self._protected_header,
                "recipients" : self._recipients,
                "iv" : self._iv,
                "ciphertext" : self._ciphertext,
                "tag" : self._auth_tag
            }, indent = indent)
        else:
            return self._compact

    def get_payload(self):
        return self._payload_raw

    @staticmethod
    def parse(jdata, keystore = None):
        jdata_ori = jdata
        # Check if it's compact serialziation

        if isinstance(jdata, str):
            parts = jdata.split(".")
            if len(parts) == 5:
                # This is compact serialization
                # Since this works somewhat different than decoding using the JSON serialization
                # we implement this here in parallel

                phdr = json.loads(base64url_decode(parts[0]))
                encrypted_key = base64url_decode(parts[1])
                iv = base64url_decode(parts[2])
                ciphertext = base64url_decode(parts[3])
                tag = base64url_decode(parts[4])

                if "enc" not in phdr:
                    raise ValueError("enc property not defined in protected header, not a JWE")

                if phdr["enc"] not in [ "A128GCM", "A192GCM", "A256GCM" ]:
                    raise ValueError(f"Content encryption algorithm {phdr['enc']} not supported")

                cty = None
                if "cty" in phdr:
                    cty = phdr["cty"]
                alg = None
                if "alg" in phdr:
                    alg = phdr["alg"]
                typ = None
                if "typ" in phdr:
                    typ = phdr["typ"]

                # Locate the correct key either by iterating over all
                # keys available for decryption or by looking up using the KID.
                # If we have no keystore we cannot decrypt ...
                decrypted_payload = None

                if keystore is not None:
                    cek = None
                    if "kid" in phdr:
                        # We search for the keys with the specific KID
                        for k in keystore.iterate_by_id(phdr["kid"], "enc", "decrypt"):
                            curalg = None
                            if "alg" in phdr:
                                curalg = phdr["alg"]
                            try:
                                cek = k["key"].decrypt(encrypted_key, alg = curalg)
                                if cek is not None:
                                    break
                            except Exception as e:
                                print(e)
                                continue
                    else:
                        for k in keystore.iterate("enc", "decrypt"):
                            curalg = None
                            if "alg" in phdr:
                                curalg = phdr["alg"]
                            try:
                                cek = k.decrypt(encrypted_key, alg = curalg)
                                if cek is not None:
                                    break
                            except:
                                continue
 
                if cek is not None:
                    cipher = AES.new(cek, AES.MODE_GCM, nonce = iv)
                    cipher.update(parts[0].encode("utf-8"))
                    decrypted_payload = cipher.decrypt_and_verify(ciphertext, tag)

                if (cty is not None) and (decrypted_payload is not None):
                    if isinstance(decrypted_payload, bytes):
                        decrypted_payload_text = decrypted_payload.decode("utf-8")
                    else:
                        decrypted_payload_text = decrypted_payload

                    if cty == "application/json":
                        decrypted_payload = json.loads(decrypted_payload_text)
                    elif cty == "JWT":
                        from jwt import parse_jwt
                        decrypted_payload = parse_jwt(decrypted_payload_text, keystore)
                    elif cty == "jwk+json":
                        from jwk import JWK
                        decrypted_payload = JWK.from_json(decrypted_payload_text)
                    elif cty == "text/plain":
                        decrypted_payload = decrypted_payload_text

                return JWE(
                    parts[0],
                    parts[1],
                    parts[2],
                    parts[3],
                    parts[4],

                    None,

                    decrypted_payload,

                    cty,
                    alg,
                    phdr["enc"],
                    typ,
                    jdata_ori
                )

        if not isinstance(jdata, dict):
            jdata = json.loads(jdata)

        # Read the protected header ...
        if "protected" not in jdata:
            raise ValueError("Protected header not found")

        phdr = json.loads(base64url_decode(jdata["protected"]))
        if "enc" not in phdr:
            raise ValueError("Protected header has no enc property, not a JWE")

        if phdr["enc"] not in [ "A128GCM", "A192GCM", "A256GCM" ]:
            raise ValueError(f"Content encryption algorithm {phdr['enc']} not supported")

        iv = base64url_decode(jdata["iv"])
        ciphertext = base64url_decode(jdata["ciphertext"])
        tag = base64url_decode(jdata["tag"])

        cty = None
        if "cty" in phdr:
            cty = phdr["cty"]
        alg = None
        if "alg" in phdr:
            alg = phdr["alg"]
        typ = None
        if "typ" in phdr:
            typ = phdr["typ"]

        # Locate the correct key either by iterating over all
        # keys available for decryption or by looking up using the KID.
        # If we have no keystore we cannot decrypt ...
        decrypted_payload = None
        if keystore is not None:
            cek = None
            for recp in jdata["recipients"]:
                curalg = None
                curkid = None
                if "alg" in recp["header"]:
                    curalg = recp["header"]["alg"]
                if "kid" in recp["header"]:
                    curkid = recp["header"]["kid"]

                if curkid is not None:
                    for k in keystore.iterate_by_id(curkid, "enc", "decrypt"):
                        try:
                            cek = k["key"].decrypt(base64url_decode(recp["encrypted_key"]), alg = curalg)
                            if cek is not None:
                                break
                        except Exception as e:
                            print(e)
                            continue
                else:
                    for k in keystore.iterate("enc", "decrypt"):
                        try:
                            cek = k.decrypt(base64url_decode(recp["encrypted_key"]), alg = curalg)
                            if cek is not None:
                                break
                        except:
                            continue

                if cek is not None:
                    break

        if cek is not None:
            cipher = AES.new(cek, AES.MODE_GCM, nonce = iv)
            cipher.update(jdata["protected"].encode("utf-8"))
            decrypted_payload = cipher.decrypt_and_verify(ciphertext, tag)

        if (cty is not None) and (decrypted_payload is not None):
            if isinstance(decrypted_payload, bytes):
                decrypted_payload_text = decrypted_payload.decode("utf-8")
            else:
                decrypted_payload_text = decrypted_payload

            if cty == "application/json":
                decrypted_payload = json.loads(decrypted_payload_text)
            elif cty == "JWT":
                from jwt import parse_jwt
                decrypted_payload = parse_jwt(decrypted_payload_text, keystore)
            elif cty == "jwk+json":
                from jwk import JWK
                decrypted_payload = JWK.from_json(decrypted_payload_text)
            elif cty == "text/plain":
                decrypted_payload = decrypted_payload_text

        return JWE(
            jdata["protected"],
            None,
            jdata["iv"],
            jdata["ciphertext"],
            jdata["tag"],

            jdata["recipients"],

            decrypted_payload,

            cty,
            alg,
            phdr["enc"],
            typ,
            jdata_ori
        )

    @staticmethod
    def create(
        payload,
        recipient_keys,
        cty = None,
        alg = None,
        enc = None,
        compact = False,
        add_kids = True,
        typ = "JWT"
    ):
        # We import here to resolve problems with circular imports
        from jws import JWS

        # Validate parameters
        if not isinstance(recipient_keys, list):
            recipient_keys = [ recipient_keys, ]

        for k in recipient_keys:
            if not isinstance(k, JWK):
                raise ValueError("Recipient keys have to be JWK instances")

        if alg is not None:
            if not isinstance(alg, list):
                alg = [ alg, ]
        else:
            alg = [ ]
            for i in range(len(recipient_keys)):
                alg.append(None)
        if len(alg) != len(recipient_keys):
            raise ValueError("alg is specified but length differs from number of recipient keys")

        if compact and (len(recipient_keys) > 1):
            raise ValueError("Compact serialization is only possible for a single recipient key")
        if len(recipient_keys) == 0:
            raise ValueError("At least one recipient has to be specified")

        if cty is None:
            if isinstance(payload, dict):
                cty = "application/json"
            elif isinstance(payload, JWS) or isinstance(payload, JWE):
                cty = "JWT"
            elif isinstance(payload, str):
                cty = "text/plain"
            elif isinstance(payload, bytes):
                cty = "application/octet-stream"
            elif isinstance(payload, JWK):
                cty = "jwk+json"
            else:
                raise ValueError("Content type not specified and not auto-detectable")

        payload_raw = payload
        if isinstance(payload, dict):
            payload = json.dumps(payload).encode("utf-8")
        elif isinstance(payload, JWS) or isinstance(payload, JWE):
            payload = payload.to_json().encode("utf-8")
        elif isinstance(payload, str):
            payload = payload.encode("utf-8")
        elif isinstance(payload, bytes):
            pass
        elif isinstance(payload, JWK):
            payload = payload.to_json().encode("utf-8")
        else:
            raise ValueError("Payload data type not supported")
 

        # enc can be:
        #   A128CBC-HS256 
        #   A192CBC-HS384
        #   A256CBC-HS512
        #   A128GCM
        #   A192GCM
        #   A256GCM
        #
        # alg can be one of the encryption algorithms supported by they JWK itself.
        # This is also processed by the JWK

        if enc is None:
            # Set our default encryption algorithm
            enc = "A256GCM"
        if enc not in [ "A128GCM", "A192GCM", "A256GCM" ]:
            raise ValueError(f"Content encryption algorithm {enc} not supported")

        encbits = None
        if enc in [ "A128GCM", "A128CBC-HS256" ]:
            encbits = 128
        elif enc in [ "A192GCM", "A192CBC-HS384" ]:
            encbits = 192
        elif enc in [ "A256GCM", "A256CBC-HS512" ]:
            encbits = 256

        for ialg, a in enumerate(alg):
            if a is None:
                alg[ialg] = recipient_keys[ialg].get_enc_alg()


        # Header parameters:
        #   alg
        #   enc
        #   typ = "JWT"
        #   cty: Content type (see above)

        # There is a generic and a per recipient header (in compact serialization
        # they are merged for a single recipient). The generic header includes
        # the "enc" header, "typ" and "cty".
        #
        # The per recipient header includes "alg" and optionally the "kid"
        #
        # For compact serialization we have to include alg in the generic header
        # (since this is added as AAD we cannot change from compact to JSON later on!)


        genheader = {
            "typ" : typ,
            "enc" : enc
        }

        if cty is not None:
            genheader.update({
                "cty" : cty
            })

        if compact:
            genheader.update({
                "alg" : alg[0]
            })
            if add_kids and (recipient_keys[0]._kid is not None):
                genheader.update({
                    "kid" : recipient_keys[0]._kid
                })
        encoded_header = base64url_encode(json.dumps(genheader).encode("utf-8"))

        # Generate random CEK matching bit length of our AES algorithm
        cek = get_random_bytes(encbits // 8)

        # For each recipient encrypt the CEK and add to our recipients array
        recipients = []
        for ik, k in enumerate(recipient_keys):
            newenccek = k.encrypt(cek, alg = alg[ik])
            recipients.append({
                "header" : { "alg" : alg[ik] },
                "encrypted_key" : base64url_encode(newenccek)
            })
            if add_kids and (k._kid is not None):
                recipients[-1]["header"].update({
                    "kid" : k._kid
                })

        # Encrypt AES payload. Include the generic header as AAD; Store IV too ...
        iv = get_random_bytes(12)
        cipher = AES.new(cek, AES.MODE_GCM, nonce=iv)
        cipher.update(encoded_header.encode("utf-8"))
        ciphertext, tag = cipher.encrypt_and_digest(payload)

        # Either build compact serialization or initialize our local structures for JSON
        encoded_iv = base64url_encode(iv)
        encoded_ciphertext = base64url_encode(ciphertext)
        encoded_tag = base64url_encode(tag)

        if compact:
            # Store data for compact serialization
            compact_serialization = f"{encoded_header}.{recipients[0]['encrypted_key']}.{encoded_iv}.{encoded_ciphertext}.{encoded_tag}"
            return JWE(
                encoded_header,
                recipients[0]['encrypted_key'],
                encoded_iv,
                encoded_ciphertext,
                encoded_tag,
                recipients,

                payload_raw,

                cty,
                alg,
                enc,
                typ,

                compact_serialization
            )
        else:
            return JWE(
                encoded_header,
                recipients[0]['encrypted_key'],
                encoded_iv,
                encoded_ciphertext,
                encoded_tag,
                recipients,

                payload_raw,

                cty,
                alg,
                enc,
                typ
            )
