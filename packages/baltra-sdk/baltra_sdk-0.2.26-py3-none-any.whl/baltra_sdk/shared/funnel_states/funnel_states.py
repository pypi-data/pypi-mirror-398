from dataclasses import dataclass, field
from typing import Dict, List
from enum import Enum

class CandidateFunnelState(str, Enum):
    """Candidate funnel states in the screening pipeline"""
    # Screening pipeline
    SCREENING_IN_PROGRESS = "screening_in_progress"
    SCHEDULED_INTERVIEW = "scheduled_interview"
    INTERVIEW_COMPLETED = "interview_completed"
    INTERVIEWED = "interviewed"
    HIRED = "hired"
    VERIFIED = "verified"
    ONBOARDING = "onboarding"

    # QR registration pipeline
    QR_REGISTRATION_PENDING = "qr_registration_pending"

    # Terminal states (process ended)
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    MISSED_INTERVIEW = "missed_interview"
    REJECTED = "rejected"

    # Phone interview pipeline
    PHONE_INTERVIEW_CITED = "phone_interview_cited"
    PHONE_INTERVIEW = "phone_interview"
    PHONE_INTERVIEW_DEMO = "phone_interview_demo"
    PHONE_INTERVIEW_PASSED = "phone_interview_passed"
    POST_PHONE_SCHEDULED_INTERVIEW = "post_phone_scheduled_interview"

    # Document verification
    DOCUMENT_VERIFICATION = "document_verification"


@dataclass
class FunnelStates:
    """Groups all funnel states into logical buckets for reporting, analytics and pipeline navigation."""
    screening_in_progress: List[CandidateFunnelState] = field(default_factory=lambda: [
        CandidateFunnelState.SCREENING_IN_PROGRESS,
        CandidateFunnelState.SCHEDULED_INTERVIEW,
        CandidateFunnelState.INTERVIEW_COMPLETED,
        CandidateFunnelState.INTERVIEW_SCHEDULED,
        CandidateFunnelState.INTERVIEWED,
        CandidateFunnelState.HIRED,
        CandidateFunnelState.VERIFIED,
        CandidateFunnelState.ONBOARDING,
    ])

    qr_registration_funnel: List[CandidateFunnelState] = field(default_factory=lambda: [
        CandidateFunnelState.QR_REGISTRATION_PENDING,
    ])

    terminal_states: List[CandidateFunnelState] = field(default_factory=lambda: [
        CandidateFunnelState.EXPIRED,
        CandidateFunnelState.CANCELLED,
        CandidateFunnelState.MISSED_INTERVIEW,
        CandidateFunnelState.REJECTED,
    ])

    phone_interview_funnel: List[CandidateFunnelState] = field(default_factory=lambda: [
        CandidateFunnelState.PHONE_INTERVIEW_CITED,
        CandidateFunnelState.PHONE_INTERVIEW,
        CandidateFunnelState.PHONE_INTERVIEW_DEMO,
        CandidateFunnelState.PHONE_INTERVIEW_PASSED,
        CandidateFunnelState.POST_PHONE_SCHEDULED_INTERVIEW,
    ])

    document_verification_funnel: List[CandidateFunnelState] = field(default_factory=lambda: [
        CandidateFunnelState.DOCUMENT_VERIFICATION,
    ])

    @property
    def as_dict(self) -> Dict[str, List[CandidateFunnelState]]:
        """Returns a dictionary representation of the funnel groups."""
        return {
            "screening_in_progress": self.screening_in_progress,
            "terminal_states": self.terminal_states,
            "phone_interview": self.phone_interview_funnel,
            "document_verification": self.document_verification_funnel,
            "qr_registration": self.qr_registration_funnel,
        }

    @property
    def reverse_map(self) -> Dict[CandidateFunnelState, str]:
        """Returns a reverse lookup: state → group name."""
        mapping = {}
        for group, states in self.as_dict.items():
            for s in states:
                mapping[s] = group
        return mapping


if __name__ == "__main__":
    funnel = FunnelStates()
    print(type(CandidateFunnelState.INTERVIEWED.value))   # <class 'str'>
    print(CandidateFunnelState.INTERVIEWED.value)         # "interviewed"
