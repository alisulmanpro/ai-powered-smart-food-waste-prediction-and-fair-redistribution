import enum


class UserRole(enum.StrEnum):
    donor = "donor"
    recipient = "recipient"
    admin = "admin"


class DonationStatus(enum.StrEnum):
    offered = "offered"
    allocated = "allocated"
    accepted = "accepted"
    collected = "collected"
    missed = "missed"
    expired = "expired"
    cancelled = "cancelled"


class AllocationStatus(enum.StrEnum):
    recommended = "recommended"
    approved = "approved"
    overridden = "overridden"
    accepted = "accepted"
    declined = "declined"
    timed_out = "timed_out"
