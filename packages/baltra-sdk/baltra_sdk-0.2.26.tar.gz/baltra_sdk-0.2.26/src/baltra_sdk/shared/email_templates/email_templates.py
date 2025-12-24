from enum import Enum


class EmailTemplate(str, Enum):
    """Enum for email template types used across the system."""
    
    # HR Manager templates
    PULSE_FILTER_ONLY = "pulse_filter_only"
    PULSE_FILTER_AI = "pulse_filter_ai"
    
    # Interview reminder templates
    INTERVIEW_REMINDER_SAME_DAY = "interview_reminder_same_day"
    INTERVIEW_REMINDER_NEXT_DAY = "interview_reminder_next_day"
    INTERVIEW_REMINDER_PASSED = "interview_reminder_passed"
    
    # Add more templates as needed
    # CANDIDATE_WELCOME = "candidate_welcome"
    # INTERVIEW_CONFIRMATION = "interview_confirmation"

