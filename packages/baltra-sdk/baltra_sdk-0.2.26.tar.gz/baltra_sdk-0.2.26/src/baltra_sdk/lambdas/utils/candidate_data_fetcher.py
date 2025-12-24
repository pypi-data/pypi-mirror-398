import json
import logging
import os
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from baltra_sdk.backend.db.models import (
    CandidateFunnelLog,
    Candidates,
    CompaniesScreening,
    CompanyGroups,
    QuestionSets,
    Roles,
    ScreeningMessages,
    ScreeningQuestions,
    db
)
from baltra_sdk.shared.funnel_states.funnel_states import CandidateFunnelState


class CandidateDataFetcher:
    """Fetches or creates candidate data, initializes thread, and determines current and next screening questions."""

    def __init__(
        self,
        wa_id_user,
        client,
        wa_id_system,
        session: Session,
        expiration_days: Optional[int] = None,
    ):
        self.wa_id_user = wa_id_user
        self.wa_id_system = wa_id_system
        self.client = client
        self.session = session
        self.expiration_days = expiration_days or int(
            os.getenv("SCREENING_EXPIRATION_DAYS", "30")
        )

        self.candidate, self.first_question_flag = self._get_or_create_candidate()
        self.latest_message = self._get_latest_message()
        self.thread_id = self._get_thread_id()
        self.set_id, self.question_id = self._get_set_and_question_id()

    def _get_or_create_candidate(self):
        logging.info(
            f"Get or create candidate for wa_id {self.wa_id_user} and system_wa_id {self.wa_id_system}"
        )
        company_group = (
            self.session.query(CompanyGroups)
            .filter_by(wa_id=self.wa_id_system)
            .first()
        )
        candidate = None

        if company_group:
            candidate = (
                self.session.query(Candidates)
                .filter_by(
                    phone=self.wa_id_user,
                    company_group_id=company_group.group_id,
                )
                .order_by(Candidates.created_at.desc())
                .first()
            )

            if not candidate:
                try:
                    new_candidate = Candidates(
                        phone=self.wa_id_user,
                        company_group_id=company_group.group_id,
                        name="",
                        created_at=datetime.now(),
                        funnel_state=CandidateFunnelState.SCREENING_IN_PROGRESS.value,
                    )
                    self.session.add(new_candidate)
                    self.session.commit()
                    return new_candidate, True
                except Exception as e:
                    logging.error(
                        f"Failed to create candidate for company group {company_group.group_id}: {e}"
                    )
                    self.session.rollback()
                    return None, False
        else:
            company = (
                self.session.query(CompaniesScreening)
                .filter_by(wa_id=self.wa_id_system)
                .first()
            )
            if not company:
                logging.warning(f"No company found for wa_id_system: {self.wa_id_system}")
                return None, False

            candidate = (
                self.session.query(Candidates)
                .filter_by(phone=self.wa_id_user, company_id=company.company_id)
                .order_by(Candidates.created_at.desc())
                .first()
            )

        if candidate:
            logging.info(f"Candidate found: ID {candidate.candidate_id}")

            latest_message = (
                self.session.query(ScreeningMessages)
                .filter_by(candidate_id=candidate.candidate_id)
                .order_by(ScreeningMessages.time_stamp.desc())
                .first()
            )

            if (
                latest_message
                and latest_message.time_stamp
                and (datetime.now() - latest_message.time_stamp).days > self.expiration_days
            ):
                previous_state = candidate.funnel_state or ""
                if previous_state != CandidateFunnelState.EXPIRED.value:
                    try:
                        log_entry = CandidateFunnelLog(
                            candidate_id=candidate.candidate_id,
                            previous_funnel_state=previous_state,
                            new_funnel_state=CandidateFunnelState.EXPIRED.value,
                            changed_at=datetime.now(),
                        )
                        self.session.add(log_entry)
                        self.session.commit()
                        logging.info(
                            f"Logged funnel state change for candidate {candidate.candidate_id}: "
                            f"{previous_state} -> expired"
                        )
                    except Exception as e:
                        logging.error(
                            f"Failed to log funnel state change for candidate {candidate.candidate_id}: {e}"
                        )
                        self.session.rollback()

                candidate.funnel_state = CandidateFunnelState.EXPIRED.value
                self.session.commit()

                try:
                    new_candidate = Candidates(
                        phone=self.wa_id_user,
                        company_id=company.company_id,
                        name="",
                        created_at=datetime.now(),
                        funnel_state=CandidateFunnelState.SCREENING_IN_PROGRESS.value,
                    )
                    self.session.add(new_candidate)
                    self.session.commit()
                    logging.info(
                        f"New candidate created: ID {new_candidate.candidate_id}"
                    )
                    return new_candidate, True
                except Exception as e:
                    logging.error(
                        f"Error creating new candidate after expiration: {e}"
                    )
                    self.session.rollback()
                    return None, False

            return candidate, False

        try:
            new_candidate = Candidates(
                phone=self.wa_id_user,
                company_id=company.company_id,
                name="",
                created_at=datetime.now(),
                funnel_state=CandidateFunnelState.SCREENING_IN_PROGRESS.value,
            )
            self.session.add(new_candidate)
            self.session.commit()
            first_question_flag = True
            logging.info(f"Created new candidate with wa_id: {self.wa_id_user}")
            return new_candidate, first_question_flag
        except Exception as e:
            logging.error(f"Error creating new candidate: {e}")
            self.session.rollback()
            return None, False

    def _get_latest_message(self):
        if not self.candidate:
            logging.warning("No candidate available when fetching latest message.")
            return None
        return (
            self.session.query(ScreeningMessages)
            .filter_by(candidate_id=self.candidate.candidate_id)
            .order_by(ScreeningMessages.time_stamp.desc())
            .first()
        )

    def _get_thread_id(self):
        if self.latest_message and self.latest_message.thread_id:
            logging.debug(f"Using existing thread ID: {self.latest_message.thread_id}")
            return self.latest_message.thread_id
        try:
            thread = self.client.beta.threads.create()
            logging.debug(f"New Thread Created: {thread.id}")
            return thread.id
        except Exception as e:
            logging.error(f"Error creating thread: {e}")
            return None

    def _get_set_and_question_id(self):
        if self.latest_message:
            return (
                self.latest_message.set_id or 1,
                self.latest_message.question_id or 1,
            )

        if self.candidate.company_id:
            logging.info(
                "No previous messages found, fetching first question from active set."
            )
            set_obj = (
                self.session.query(QuestionSets)
                .filter_by(
                    company_id=self.candidate.company_id,
                    is_active=True,
                    general_set=True,
                )
                .order_by(QuestionSets.created_at.desc())
                .first()
            )

            if not set_obj:
                logging.warning(
                    f"No active question set found for company {self.candidate.company_id}"
                )
                return 1, 1

            first_question = (
                self.session.query(ScreeningQuestions)
                .filter_by(set_id=set_obj.set_id, position=1, is_active=True)
                .first()
            )
            if not first_question:
                logging.warning(
                    f"No question with position=1 found in set {set_obj.set_id}"
                )
                return set_obj.set_id, 1
        elif self.candidate.company_group_id:
            logging.info(
                "Candidate belongs to a company group, fetching first question from active group set."
            )
            set_obj = (
                self.session.query(QuestionSets)
                .filter_by(group_id=self.candidate.company_group_id, is_active=True)
                .order_by(QuestionSets.created_at.desc())
                .first()
            )

            if not set_obj:
                logging.warning(
                    f"No active group question set found for group {self.candidate.company_group_id}"
                )
                return 1, 1

            logging.info(
                f"Active group question set selected: set_id {set_obj.set_id}"
            )
            first_question = (
                self.session.query(ScreeningQuestions)
                .filter_by(set_id=set_obj.set_id, position=1, is_active=True)
                .first()
            )

            if not first_question:
                logging.warning(
                    f"No question with position=1 found in group set {set_obj.set_id}"
                )
                return set_obj.set_id, 1

        return set_obj.set_id, first_question.question_id

    def _get_current_and_next_question(self):
        current = (
            self.session.query(ScreeningQuestions)
            .filter_by(question_id=self.question_id)
            .first()
        )

        if not current:
            logging.warning(f"No question found with ID: {self.question_id}")
            return None, None, None, None, None, None, None, None

        next_q = (
            self.session.query(ScreeningQuestions)
            .filter_by(
                set_id=self.set_id,
                position=current.position + 1,
                is_active=True,
            )
            .first()
        )

        if next_q:
            logging.debug(f"Next question found: position {next_q.position}")
            return (
                current.question,
                current.response_type,
                current.position,
                current.end_interview_answer,
                current.example_answer,
                next_q.question,
                next_q.response_type,
                next_q.question_id,
            )
        else:
            logging.info(
                f"No next question found after position {current.position} in set {self.set_id}"
            )
            return (
                current.question,
                current.response_type,
                current.position,
                current.end_interview_answer,
                current.example_answer,
                None,
                None,
                None,
            )

    def _get_company_context(self):
        """Gets company context based on candidate's company_id. If no company_id, falls back to company_groups info."""
        if self.candidate.company_id:
            company = (
                self.session.query(CompaniesScreening)
                .filter_by(company_id=self.candidate.company_id)
                .first()
            )
            if company:
                return (
                    company.name,
                    company.description,
                    company.address,
                    company.benefits,
                    company.general_faq,
                    company.classifier_assistant_id,
                    company.general_purpose_assistant_id,
                    company.maps_link_json or {},
                    company.interview_address_json or {},
                    company.interview_days,
                    company.interview_hours,
                    company.hr_contact,
                )

        if self.candidate.company_group_id:
            group = (
                self.session.query(CompanyGroups)
                .filter_by(group_id=self.candidate.company_group_id)
                .first()
            )
            if group:
                return (
                    group.name,
                    group.description,
                    None,
                    None,
                    None,
                    "asst_2niF2rxOV8L5xjZveofoXoAg",
                    "asst_0iKgCxWeDc5gpQnTQJAbM0MA",
                    {},
                    {},
                    None,
                    None,
                    None,
                )

        return "", "", "", "", "", "", "", {}, {}, None, None, None

    def _get_role_context(self):
        if self.candidate.role_id:
            role = (
                self.session.query(Roles)
                .filter_by(role_id=self.candidate.role_id)
                .first()
            )
            if role:
                role_info_str = (
                    str(role.role_info) if role.role_info else "Sin información adicional"
                )
                return f"- {role.role_name}: {role_info_str}"
            else:
                return "No se encontró información del rol asignado"
        else:
            roles = (
                self.session.query(Roles)
                .filter_by(company_id=self.candidate.company_id)
                .all()
            )
            if roles:
                role_descriptions = []
                for role in roles:
                    role_info_str = (
                        str(role.role_info)
                        if role.role_info
                        else "Sin información adicional"
                    )
                    role_descriptions.append(f"- {role.role_name}: {role_info_str}")
                return (
                    "El candidato aún no ha seleccionado un rol. A continuación se muestra información "
                    "de todos los roles disponibles en la empresa:\n"
                    + "\n".join(role_descriptions)
                )
            return "No se encontraron roles para esta empresa"

    def _get_next_set_data(self):
        """Determines the next question set based on the candidate's role or company group."""
        role_set_id = None
        next_set_first_question = None
        next_set_first_question_id = None
        next_set_first_question_type = None
        role = None

        current_set_obj = (
            self.session.query(QuestionSets)
            .filter_by(set_id=self.set_id)
            .first()
        )

        if (
            current_set_obj
            and current_set_obj.group_id
            and not current_set_obj.company_id
            and self.candidate.company_id
        ):
            logging.info(
                "[CandidateDataFetcher] Candidate finished company_group set "
                f"{self.set_id}, assigning company general set as next set."
            )

            general_set_obj = (
                self.session.query(QuestionSets)
                .filter_by(company_id=self.candidate.company_id, general_set=True)
                .first()
            )

            if general_set_obj:
                first_question = (
                    self.session.query(ScreeningQuestions)
                    .filter_by(
                        set_id=general_set_obj.set_id,
                        position=1,
                        is_active=True,
                    )
                    .first()
                )

                return (
                    first_question.set_id if first_question else None,
                    first_question.question if first_question else None,
                    first_question.question_id if first_question else None,
                    first_question.response_type if first_question else None,
                    None,
                )

        current_set = (
            self.session.query(QuestionSets.general_set)
            .filter_by(set_id=self.set_id)
            .scalar()
        )
        if current_set is False:
            return (
                role_set_id,
                next_set_first_question,
                next_set_first_question_id,
                next_set_first_question_type,
                role,
            )

        if self.candidate.role_id:
            role = (
                self.session.query(Roles)
                .filter_by(role_id=self.candidate.role_id)
                .first()
            )
        else:
            role = (
                self.session.query(Roles)
                .filter_by(company_id=self.candidate.company_id, default_role=True)
                .first()
            )
            # Update the role_id in candidates for the default role
            if role and not self.candidate.role_id:
                try:
                    self.candidate.role_id = role.role_id
                    self.session.commit()
                    logging.info(f"Assigned and saved role_id={role.role_id} (default) to candidate {self.candidate.candidate_id}.")
                except Exception as e:
                    logging.error(f"Failed to save default role_id for candidate {self.candidate.candidate_id}: {e}")
                    self.session.rollback()

        if role and role.set_id:
            role_set_id = role.set_id

            first_question = (
                self.session.query(ScreeningQuestions)
                .filter_by(set_id=role_set_id, position=1, is_active=True)
                .first()
            )

            if first_question:
                next_set_first_question = first_question.question
                next_set_first_question_id = first_question.question_id
                next_set_first_question_type = first_question.response_type

        return (
            role_set_id,
            next_set_first_question,
            next_set_first_question_id,
            next_set_first_question_type,
            role,
        )

    def get_data(self):
        if not self.candidate or not self.thread_id:
            logging.warning("Missing candidate or thread ID during data fetch.")
            return None

        (
            current_question,
            current_response_type,
            current_position,
            end_interview_answer,
            example_answer,
            next_question,
            next_question_response_type,
            next_question_id,
        ) = self._get_current_and_next_question()

        (
            role_set_id,
            next_set_first_question,
            next_set_first_question_id,
            next_set_first_question_type,
            role,
        ) = self._get_next_set_data()

        (
            company_name,
            company_description,
            company_address,
            company_benefits,
            company_general_faq,
            classifier_assistant_id,
            general_purpose_assistant_id,
            maps_link_json,
            interview_address_json,
            interview_days,
            interview_hours,
            hr_contact,
        ) = self._get_company_context()

        interview_date_str = (
            self.candidate.interview_date_time.strftime("%d/%m/%Y %I:%M %p")
            if self.candidate.interview_date_time
            else ""
        )

        return {
            "wa_id": self.wa_id_user,
            "candidate_id": self.candidate.candidate_id,
            "first_name": self.candidate.name,
            "flow_state": self.candidate.flow_state,
            "first_question_flag": self.first_question_flag,
            "company_group_id": self.candidate.company_group_id,
            "company_id": self.candidate.company_id,
            "company_name": company_name,
            "thread_id": self.thread_id,
            "classifier_assistant_id": classifier_assistant_id,
            "general_purpose_assistant_id": general_purpose_assistant_id,
            "set_id": self.set_id,
            "next_set_id": role_set_id,
            "question_id": self.question_id,
            "current_question": current_question,
            "current_response_type": current_response_type,
            "current_position": current_position,
            "end_interview_answer": end_interview_answer,
            "example_answer": example_answer,
            "next_question": next_question,
            "next_question_response_type": next_question_response_type,
            "next_question_id": next_question_id,
            "next_set_first_question": next_set_first_question,
            "next_set_first_question_id": next_set_first_question_id,
            "next_set_first_question_type": next_set_first_question_type,
            "company_context": json.dumps(
                {
                    "Descripción": company_description,
                    "Ubicación_Vacante": company_address,
                    "Beneficios": company_benefits,
                    "Preguntas_Frecuentes": company_general_faq,
                    "Dias_Entrevista": interview_days,
                    "Horarios_Entrevista": interview_hours,
                    "hr_contact": hr_contact
                    if self.candidate.funnel_state == CandidateFunnelState.SCHEDULED_INTERVIEW.value
                    else None,
                },
                ensure_ascii=False,
            ),
            "role": self.candidate.role.role_name if self.candidate.role else None,
            "role_context": self._get_role_context(),
            "travel_time_minutes": getattr(self.candidate, "travel_time_minutes", None),
            "funnel_state": self.candidate.funnel_state,
            "end_flow_rejected": self.candidate.end_flow_rejected,
            "interview_date": interview_date_str,
            "interview_address": self.candidate.interview_address,
            "eligible_roles": self.candidate.eligible_roles or [],
            "maps_link_json": maps_link_json,
            "interview_address_json": interview_address_json,
        }

