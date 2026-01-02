import datetime
import importlib
import shutil
from pydantic import BaseModel, Field, DirectoryPath, field_validator, model_validator
from typing import Literal
from ipaddress import IPv4Address, IPv6Address


class FilterOptions(BaseModel):
    """A unified model for the available filter options."""

    origin_asn: int | None = Field(
        default=None, description="Filter by the origin AS number."
    )
    prefix: str | None = Field(
        default=None, description="Filter by an exact prefix match."
    )
    prefix_super: str | None = Field(
        default=None,
        description="Filter by the exact prefix and its more general super-prefixes.",
    )
    prefix_sub: str | None = Field(
        default=None,
        description="Filter by the exact prefix and its more specific sub-prefixes.",
    )
    prefix_super_sub: str | None = Field(
        default=None,
        description="Filter by the exact prefix and both its super- and sub-prefixes.",
    )
    peer_ip: str | IPv4Address | IPv6Address | None = Field(
        default=None, description="Filter by the IP address of a single BGP peer."
    )
    peer_ips: list[str | IPv4Address | IPv6Address] | None = Field(
        default=None, description="Filter by a list of BGP peer IP addresses."
    )
    peer_asn: int | None = Field(
        default=None, description="Filter by the AS number of the BGP peer."
    )
    update_type: Literal["withdraw", "announce"] | None = Field(
        default=None, description="Filter by the BGP update message type."
    )
    as_path: str | None = Field(
        default=None, description="Filter by a regular expression matching the AS path."
    )
    ip_version: Literal[4, 6] | None = Field(
        default=None, description="Filter by ip version."
    )


class BGPStreamConfig(BaseModel):
    """Unified BGPStream config, compatible with BGPKIT and pybgpstream"""

    start_time: datetime.datetime = Field(description="Start of the stream")
    end_time: datetime.datetime = Field(description="End of the stream")
    collectors: list[str] = Field(description="List of collectors to get data from")
    data_types: list[Literal["ribs", "updates"]] = Field(
        description="List of archives files to consider (`ribs` or `updates`)"
    )

    filters: FilterOptions | None = Field(default=None, description="Optional filters")

    @field_validator("start_time", "end_time")
    @classmethod
    def normalize_to_utc(cls, dt: datetime.datetime) -> datetime.datetime:
        # if naive datetime (not timezone-aware) assume it's UTC
        if dt.tzinfo is None:
            return dt.replace(tzinfo=datetime.timezone.utc)
        # if timezone-aware, convert to utc
        else:
            return dt.astimezone(datetime.timezone.utc)


class PyBGPKITStreamConfig(BaseModel):
    """Unified BGPStream config and parameters related to PyBGPKIT implementation (all optional)"""

    bgpstream_config: BGPStreamConfig

    max_concurrent_downloads: int | None = Field(
        default=10, description="Maximum concurrent downloads of archive files."
    )

    cache_dir: DirectoryPath | None = Field(
        default=None,
        description="Specifies the directory for caching downloaded files.",
    )

    ram_fetch: bool | None = Field(
        default=True,
        description=(
            "If caching is disabled, fetch temp files in shared RAM memory (/dev/shml) or normal disc temp dir (/tmp)."
            "Default (True) improve perfomance and reduce disk wear, at the expense of increased RAM usage."
        ),
    )

    chunk_time: datetime.timedelta | None = Field(
        default=datetime.timedelta(hours=2),
        description=(
            "Interval for the fetch/parse cycles (benefits: avoid long prefetch time + periodic temps cleanup when caching is disabled)."
            "Slower value means less RAM/disk used at the cost of performance."
        ),
    )

    parser: Literal["pybgpkit", "bgpkit", "pybgpstream", "bgpdump"] = Field(
        default="pybgpkit",
        description=(
            "MRT files parser. Default `pybgpkit` is installed but slow, the others are system dependencies."
        ),
    )

    @field_validator("parser")
    @classmethod
    def check_parser_available(cls, parser: str) -> str:
        if parser == "pybgpkit":
            if importlib.util.find_spec("bgpkit") is None:
                raise ValueError(
                    "pybgpkit is not installed. Install with: pip install pybgpkit"
                )

        elif parser == "pybgpstream":
            if importlib.util.find_spec("pybgpstream") is None:
                raise ValueError(
                    "pybgpstream is not installed. "
                    "Install with: pip install pybgpstream (ensure system dependencies are met)"
                )

        elif parser == "bgpdump":
            if shutil.which("bgpdump") is None:
                raise ValueError(
                    "bgpdump binary not found in PATH. "
                    "Install with: sudo apt-get install bgpdump"
                )

        elif parser == "bgpkit":
            if shutil.which("bgpkit-parser") is None:
                raise ValueError(
                    "bgpkit binary not found in PATH. "
                    "Install from: https://github.com/bgpkit/bgpkit-parser "
                    "or use cargo: cargo install bgpkit-parser"
                )

        # Return the parser value if validation passes
        return parser
    
    @model_validator(mode='before')
    @classmethod
    def nest_bgpstream_params(cls, data: dict) -> dict:
        """Allow to define a flat config"""
        # If the user already provided 'bgpstream_config', do nothing
        if "bgpstream_config" in data:
            return data
        
        # Define which fields belong to the inner BGPStreamConfig
        stream_fields = {"start_time", "end_time", "collectors", "data_types", "filters"}
        
        # Extract those fields from the flat input
        inner_data = {k: data.pop(k) for k in stream_fields if k in data}
        
        # Nest them back into the dictionary
        data["bgpstream_config"] = inner_data
        return data
