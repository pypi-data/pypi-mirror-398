from jwk import JWK

class Keystore:
    """
        A wrapper class to contain JWKSets and JWKs that serve
        as a keystore with different trust relationships. The keystore
        is not standardized in any RFC  - the same goes for the web
        of trust and trust management approach that is done here ...

        Trust management works about the same as for OpenPGP. Keys are
        assigned "trust amounts" and optionally different domains for
        which this trust amount is valid. THose trust amounts are assigned
        in signatures of the keys (also non standard). We can also store our
        own self signed keys.

        The trust factor is calculated as a value between 0 and 1
        We can assign by ourself:
         * We fully trust a key (1) - usually because we fully checked
           (Ultimate trust)
         * We marginally trust a key (0.5) - for a quick check
         * We fully trust a key (0.9) - for a deep background identity check
         * We fully distrust a key (0) - this overrides everything else
           when we set this (if someone else distrusts a key by 0 it does
           not influence the chain, one has to set it to 0.0001 or something
           like this to influence the chain via weighting)
        We can also assign a maximum delegate depth in our certification
        so we don't trust signatures that someone else gives or limit
        it via a regular expression to given key IDs or ranges of key
        IDs

        The following parameters manage the trust calculation:

        * A maximum trust depth specifies the maximum length of a delegate
          chain. In case we don't find a path within this length we dont
          trust the key (0)
        * There is a decay factor (that can be increased via a local
          certification setting but never decreased) on how trust decreases
          from hop to hop
        * A single paths trust factor can thus be calculated as
            sum(trust_i * decay^i)

        Example:
            If we (A) certify B with a trust level of 0.9
            B certifies C with trust level of 0.5
            and C certifies D with a trust level of 0.9

            Decay factor is 0.85

            Then the total trust of this chain is:
              0.9 * (0.85**0) * 0.5 * (0.85**1) * 0.9 * (0.85**2)
              thus this would be 0.2487

        To implement this we use a "trust" structure per key that is
        calculated when importing a key into a keystore.


        Out keystore contains the following information per key:

        {
            "key" : <JWK Object>,
            "trust" : <our calculated trust level>,
            "trust_override" : <our manually set trust override for this key>,
            "signatures" : [
                <JWS signatures for this key?>
            ]
        }

    """

    def __init__(self):
        # The keys_by_kid dictionary provides
        # an index into either keys or keysets arrays
        # based on the KID. For each KID there could be
        # multiple entries (in case of collisions) so each
        # entry is a list. Each list can be either a 1-tuple
        # or a 2-tuple (key or keyset+key index)

        self._keys_by_kid = {}

        self._keys = []
        self._keysets = []

    def add(self, key):
        if isinstance(key, JWK):
            self._keys.append({
                "key" : key
            })

            kid = key.get_id()
            if kid is not None:
                if kid not in self._keys_by_kid:
                    self._keys_by_kid[kid] = [ (len(self._keys)-1, ), ]
                else:
                    self._keys_by_kid[kid].append( (len(self._keys)-1,) )
        else:
            raise ValueError("Only JWKs are currently supported")

    def iterate_by_id(self, kid, usage = None, operation = None):
        if kid not in self._keys_by_kid:
            return

        for ent in self._keys_by_kid[kid]:
            if len(ent) == 1:
                k = self._keys[ent[0]]
                if usage is not None:
                    # Check if usage filter applies
                    if (k["key"]._use is not None) and (k["key"]._use != usage):
                        continue

                if operation is not None:
                    if (k["key"]._key_ops is not None) and (operation not in k["key"]._key_ops):
                        continue

                yield k
            else:
                raise NotImplementedError("Currently keysets are not implemented")

    def iterate(self, usage = None, operation = None):
        # Iterate over all keys independent of key ID
        # First start with keys, then do keysets

        for k in self._keys:
            if usage is not None:
                # Check if usage filter applies
                if (k["key"]._use is not None) and (k["key"]._use != usage):
                    continue

            if operation is not None:
                if (k["key"]._key_ops is not None) and (operation not in k["key"]._key_ops):
                    continue

            yield k

    def to_json(self, indent = None, include_private = False):
        pass

    def to_jwk(self, include_private = False):
        pass

    def store(self, filename, include_private = False):
        pass

    @staticmethod
    def load(filename):
        pass

