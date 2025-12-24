"""Data models for Pulse8 Matrix API responses."""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from enum import IntEnum


class APIModel(BaseModel):
    class Config:
        populate_by_name = True
        alias_generator = lambda x: ''.join(word.capitalize() for word in x.split('_'))


class Revision(APIModel):
    """Board revision information."""
    main: int
    top: int
    ir: int


class SystemDetails(APIModel):
    """System details response."""
    result: bool
    model: str
    version: str
    serial: str
    mac: str = Field(alias="MAC")
    vid: str = Field(alias="VID")
    board_rev: int
    revision: Revision
    locale: str
    status_message: str
    status: int


class VideoFeatures(APIModel):
    """Video feature information."""
    scrambling: bool
    ir: Optional[Dict[str, Any]] = None
    input: Dict[str, Any]
    output: Dict[str, Any]


class AudioFeatures(APIModel):
    """Audio feature information."""
    arc: Optional[Dict[str, Any]] = None
    routing: bool
    dsp: Optional[bool] = None
    input: Dict[str, Any]
    output: Dict[str, Any]


class SystemFeatures(APIModel):
    """System features response."""
    result: bool
    upd_interval: int
    cec: Optional[bool] = None
    cec_switching: bool = Field(alias="CEC_Switching")
    cec_logging: int = Field(alias="CEC_Logging")
    cec_usage: int = Field(alias="CEC_Usage")
    pdu: bool = Field(alias="PDU")
    sky: bool = Field(alias="Sky")
    hdbaset: bool = Field(alias="HDBaseT")
    hdbt_upgrade: bool
    mx_remote: bool
    video: VideoFeatures
    audio: AudioFeatures
    backlight_led: Optional[str] = None
    status_led: Optional[str] = None


class PortStatus(IntEnum):
    """Enum for port status codes."""
    OK = 0
    MODULE_FAULT = 1
    WARNING = 2
    NO_SIGNAL = 3
    MODULE_NOT_PRESENT = 4


class Port(APIModel):
    """Port information."""
    bay: int
    mode: str
    type: str
    status: PortStatus
    name: str
    receive_from: Optional[int] = None
    rc_type: Optional[int] = Field(None, alias="rcType")


class PortListResponse(APIModel):
    """Port list response."""
    result: bool
    ports: List[Port]


class OverrideEDIDDetails(APIModel):
    """Override EDID details."""
    address: str
    setting: int


class LinkQualityDetails(APIModel):
    """Link quality details."""
    channel_a: float
    channel_b: float
    channel_c: float
    channel_d: float
    errors_channel_a: float
    errors_channel_b: float
    errors_channel_c: float
    errors_channel_d: float
    status: int
    tmds: int = Field(alias="TMDS")
    ber: int = Field(alias="BER")
    total_ber: int = Field(alias="TotalBER")
    errors_control: Optional[int] = Field(None, alias="ErrorsControl")
    errors_crc: Optional[int] = Field(None, alias="ErrorsCRC")
    errors_data: Optional[int] = Field(None, alias="ErrorsData")
    errors_tmds: Optional[int] = Field(None, alias="ErrorsTMDS")
    errors_video: Optional[int] = Field(None, alias="ErrorsVideo")


class BasePortDetails(APIModel):
    """Base model for detailed port information."""
    result: bool
    bay: int
    mode: str
    type: str
    status: PortStatus
    name: str
    status_message: str
    hpd: Optional[int] = Field(None, alias="HPD")
    has_signal: Optional[bool] = None
    video_signal: Optional[str] = None
    signal: Optional[str] = None

    @property
    def status_description(self) -> str:
        """Return a human-readable description of the port's status."""
        if self.status == PortStatus.NO_SIGNAL:
            if self.type == 'AUDIO IN':
                return 'Audio Only'
            return 'No HDMI Signal'
        if self.status == PortStatus.MODULE_NOT_PRESENT:
            return f"{self.mode} Not Present"
        if self.status == PortStatus.MODULE_FAULT:
            return f"{self.mode} is Faulty"
        if self.status == PortStatus.OK:
            return "OK"
        if self.status == PortStatus.WARNING:
            return "Warning"
        return self.status_message # Fallback


class InputPortDetails(BasePortDetails):
    """Detailed input port information."""
    transmission_nodes: Optional[List[int]] = None
    hdcp: Optional[int] = Field(None, alias="HDCP")
    remote: Optional[int] = None
    remote_status: Optional[str] = None
    remote_online: Optional[int] = None
    config_remote: Optional[int] = None
    allowed_sinks: Optional[List[int]] = None
    edid_profile: Optional[int] = None


class OutputPortDetails(BasePortDetails):
    """Detailed output port information."""
    receive_from: Optional[int] = None
    allowed_sources: Optional[List[int]] = None
    sink_state: Optional[int] = None
    link_status: Optional[str] = None
    poe: Optional[bool] = Field(None, alias="POE")
    firmware_version: Optional[str] = None
    firmware_version_available: Optional[bool] = None
    support_sb: Optional[bool] = None
    hdbt_vendor: Optional[int] = Field(None, alias="HDBT_Vendor")
    description: Optional[str] = None
    fw_bank: Optional[int] = None
    cec_passthrough: Optional[bool] = None
    physical_address: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[int] = None
    monitor_name: Optional[str] = None
    serial: Optional[int] = None
    manufactured: Optional[str] = None
    edid_read: Optional[bool] = None
    override_edid: Optional[OverrideEDIDDetails] = Field(None, alias="OverrideEDID")
    estimated_cable_length: Optional[int] = None
    link_quality: Optional[LinkQualityDetails] = None


class SetPortResponse(APIModel):
    """Response from setting a port connection."""
    result: bool
    message: str
