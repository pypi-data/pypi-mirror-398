import json
import base64

from enum import Enum

from jwk import JWK
from jwt import parse_jwt

def base64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def base64url_decode(data):
    padding = '=' * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)

class JWSValidation(Enum):
    UNKNOWN = 0
    VALID = 1
    SIGNED = 2
    INVALID = 3

class JWS:
    def __init__(
        self,
        payload,
        payload_encoded,
        payloadtype,
        headers,
        headers_unsigned,
        signatures,
        validstate,
        compact
    ):
        self._payload = payload
        self._payload_encoded = payload_encoded
        self._payloadtype = payloadtype
        self._signatures = signatures
        self._validstate = validstate
        self._headers = headers
        self._headers_unsigned = headers_unsigned
        self._compact = compact

    @staticmethod
    def create(
        payload,
        signaturekeys,
        payloadtype = "JWT",
        payloadcontenttype = None,
        compact = False,
        add_kids = True,
        alg = None
    ):
        # To resolve circulat imports we import JWE here
        from jwe import JWE

        if isinstance(signaturekeys, list):
            # Validate if we have multiple signatures (only supports JSON serialization)
            for sk in signaturekeys:
                if not isinstance(sk, JWK):
                    raise ValueError("Signature key has to be a JWK instance")
        else:
            if not isinstance(signaturekeys, JWK):
                raise ValueError("Signature key has to be a JWK instance")
            signaturekeys = [ signaturekeys, ]

        if alg is not None:
            if not isinstance(alg, list):
                alg = [ alg, ]

            if len(alg) != len(signaturekeys):
                raise ValueError("Algorithm list length does not match signature key list length")

        # Create signature for our payload
        payload_raw = payload

        if isinstance(payload, dict):
            # JSON serialize ...
            payload = base64url_encode(json.dumps(payload).encode("utf-8"))
            if payloadcontenttype is not False:
                payloadcontenttype = "application/json"
        elif isinstance(payload, str):
            payload = base64url_encode(payload.encode("utf-8"))
            if payloadcontenttype is not False:
                payloadcontenttype = "text/plain"
        elif isinstance(payload, bytes):
            payload = base64url_encode(payload)
            if payloadcontenttype is not False:
                payloadcontenttype = "application/octet-stream"
        # ToDo: Add JWS, JWK
        elif isinstance(payload, JWS):
            payload = base64url_encode(payload.to_json().encode("utf-8"))
            if payloadcontenttype is not False:
                payloadcontenttype = "JWT"
        elif isinstance(payload, JWE):
            payload = base64url_encode(payload.to_json().encode("utf-8"))
            if payloadcontenttype is not False:
                payloadcontenttype = "JWT"
        elif isinstance(payload, JWK):
            payload = base64url_encode(payload.to_json().encode("utf-8"))
            if payloadcontenttype is not False:
                payloadcontenttype = "jwk+json"
        else:
            raise ValueError("Data type of payload not supported (not dict, str, bytes)")

        headers = []
        unsigned_headers = []
        for isk, sk in enumerate(signaturekeys):
            newhead = {
                "alg" : sk.get_sign_alg(),
                "typ" : payloadtype
            }
            if alg is not None:
                if alg[isk] is not None:
                    newhead["alg"] = alg[isk]

            if add_kids and (sk._kid is not None):
                newhead.update({
                    "kid" : sk._kid
                })
            if (payloadcontenttype is not None) and (payloadcontenttype is not False):
                newhead.update({
                    "cty" : payloadcontenttype
                })

            # Currently we don't use the unsigned headers any more so we add None
            unsigned_headers.append(None)
            headers.append(base64url_encode((json.dumps(newhead)).encode('utf-8')))

        # Actual signing

        signatures = []
        validstate = []
        for isk, sk in enumerate(signaturekeys):
            dts = f"{headers[isk]}.{payload}".encode("utf-8")
            curalg = None
            if alg is not None:
                curalg = alg[isk]
            sig = sk.sign(dts, alg = curalg)
            signatures.append(base64url_encode(sig))
            validstate.append(JWSValidation.SIGNED)

        return JWS(
            payload_raw,
            payload,
            payloadtype,
            headers,
            unsigned_headers,
            signatures,
            validstate,
            compact
        )

    def get_payload(self):
        return self._payload

    def add_signature(
        self,
        key,
        add_kids = True,
        alg = None
    ):
        if not isinstance(key, JWK):
            raise ValueError("Signature key has to be a JWK instance")

        if self._compact:
            raise ValueError("Compact JWS can only contain a single signature")

        # Determine cty and typ values from other headers
        
        typ = self._payloadtype
        cty = None
        for h in self._headers:
            if "cty" in h:
                cty = h["cty"]
                break

        # Create new header (optionally including kid) matching the new key
        newhead = {
            "alg" : key.get_sign_alg(),
            "typ" : typ
        }
        if alg is not None:
            newhead["alg"] = alg
        if cty is not None:
            newhead["cty"] = cty
        if add_kids and (key._kid is not None):
            newhead["kid"] = key._kid

        # Actually generate the signature
        header_enc = base64url_encode((json.dumps(newhead)).encode('utf-8'))
        dts = f"{header_enc}.{self._payload_encoded}".encode("utf-8")
        sig = base64url_encode(key.sign(dts, alg = alg))
        #    validstate.append(JWSValidation.SIGNED)

        # Add signature and new protected header as well as validstate to list
        self._headers.append(header_enc)
        self._signatures.append(sig)
        self._validstate.append(JWSValidation.SIGNED)
        self._headers_unsigned.append(None)

    def __repr__(self):
        cp = self._compact
        self._compact = False
        res = self.to_json(indent = 4)
        self._compact = cp
        return res

    def to_json(self, indent = None):
        if self._compact and (len(self._signatures) != 1):
            raise ValueError("Compact serialization is only possible with exactly one key")

        if self._compact:
            # This method also pushes compact serialization
            return f"{self._headers[0]}.{self._payload_encoded}.{self._signatures[0]}"

        res = {
            "payload" : self._payload_encoded,
            "signatures" : [
            ]
        }

        for isk in range(len(self._headers)):
            res["signatures"].append({
                "protected" : self._headers[isk],
                "signature" : self._signatures[isk]
            })
            if self._headers_unsigned[isk] is not None:
                res["signatures"][-1].update({
                    "header" : self._headers_unsigned[isk]
                })

        return json.dumps(res, indent = indent)

    @staticmethod
    def parse(data, keystore = None):
        # Parse a JWS either in compact or in JSON form ...

        # We just try to decode the JSON - if this does not work we try to deserialize
        # the compact serialization.

        jsondata = None
        compact = False

        try:
            jsondata = json.loads(data)
        except:
            jsondata = None

        if jsondata is None:
            # We try to parse a compact serialization - and pack it into a JSON structure for further processing ...
            parts = data.split(".")
            if len(parts) != 3:
                raise ValueError("The supplied data is neither JSON nor a compact JWS serialization")
            # Parts[0]: Protected header
            # Parts[1]: Payload
            # Parts[2]: Signature
            jsondata = {
                "payload" : parts[1],
                "signatures" : [
                    {
                        "protected" : parts[0],
                        "signature" : parts[2]
                    }
                ]
            }
            compact = True

        # Try to parse the serialization and try to validate all signatures
        # using the supplied JWKs and JWKSets

        sigs = []
        valids = []
        pheaders = []
        upheaders = []
        cty = None
        typ = None

        for s in jsondata["signatures"]:
            if "header" in s:
                upheaders.append(s["header"])
            else:
                upheaders.append(None)

            pheaders.append(s["protected"])
            sigs.append(s["signature"])
            valids.append(JWSValidation.UNKNOWN)

            # Add content of protected header to cty and typ
            # (use first occurance - check if this is ok)

            phdr = json.loads(base64url_decode(s["protected"]).decode("utf-8"))
            if ("cty" in phdr) and (cty is None):
                cty = phdr["cty"]
            if ("typ" in phdr) and (typ is None):
                typ = phdr["typ"]

            # We now try to verify the signature using the JWKs and
            # JWKSets we have passed as keystore

            if keystore is not None:
                # If we have a key ID try to verify only with the specified
                # keys (Note / ToDo: This may introduce a timing attack into which
                # keys we know - mitigate that ...)

                # ToDo: We also have to calculate the trust levels ...

                sigValid = False

                if "kid" in phdr:
                    # We only use the key ID to locate the key
                    for k in keystore.iterate_by_id(phdr["kid"], "sig", "verify"):
                        curalg = None
                        if "alg" in phdr:
                            curalg = phdr["alg"]
                        verres = k["key"].verify(f"{s['protected']}.{jsondata['payload']}".encode("utf-8"), base64url_decode(s['signature']), curalg)
                        if verres == JWSValidation.VALID:
                            sigValid = True
                else:
                    # We have to walk all keys to see if they match ...
                    for k in keystore.iterate("sig", "verify"):
                        curalg = None
                        if "alg" in phdr:
                            curalg = phdr["alg"]
                        verres = k["key"].verify(f"{s['protected']}.{jsondata['payload']}".encode("utf-8"), base64url_decode(s['signature']), curalg)
                        if verres == JWSValidation.VALID:
                            sigValid = True

                if sigValid:
                    valids[-1] = JWSValidation.VALID
                else:
                    valids[-1] = JWSValidation.INVALID


        payloadparsed = None
        if (cty == "application/json") or (cty == "text/json"):
            payloadparsed = json.loads(base64url_decode(jsondata["payload"]))
        if (cty == "JWT"):
            payloadparsed = parse_jwt(base64url_decode(jsondata["payload"]), keystore)
        if cty == "jwk+json":
            payloadparsed = JWK.from_json(base64url_decode(jsondata["payload"]))
        # ToDo: Parse other types

        return JWS(
            payloadparsed,
            jsondata["payload"],
            typ,
            pheaders,
            upheaders,
            sigs,
            valids,
            compact
        )
 
