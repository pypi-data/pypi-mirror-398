from typing import NamedTuple, TypedDict


class ElementFields(TypedDict):
    # need to use annotations because of '-'
    __annotations__ = {
        "next-hop": str,
        "as-path": str,
        "communities": list[str],
        "prefix": str,
    }


class BGPElement(NamedTuple):
    """Compatible with pybgpstream.BGPElem"""

    type: str
    collector: str
    time: float
    peer_asn: int
    peer_address: str
    fields: ElementFields

    def __str__(self):
        """Credit to pybgpstream"""
        return "%s|%f|%s|%s|%s|%s|%s|%s|%s|%s|%s" % (
            self.type,
            self.time,
            self.collector,
            self.peer_asn,
            self.peer_address,
            self._maybe_field("prefix"),
            self._maybe_field("next-hop"),
            self._maybe_field("as-path"),
            " ".join(self.fields["communities"])
            if "communities" in self.fields
            else None,
            self._maybe_field("old-state"),
            self._maybe_field("new-state"),
        )

    def _maybe_field(self, field):
        """Credit to pybgpstream"""
        return self.fields[field] if field in self.fields else None
