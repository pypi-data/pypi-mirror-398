import json
import logging
from datetime import datetime, timedelta, date
from baltra_sdk.backend.db.models import MessageTemplates, CompaniesScreening
from baltra_sdk.lambdas.db.sql_utils import (
    get_company_screening_data,
    get_active_roles_text,
    get_active_roles_for_company,
    mark_end_flow_rejected,
    get_candidate_eligible_roles,
    get_candidate_eligible_companies,
    get_available_dates_and_hours,
)
from sqlalchemy.orm import Session
import re


def company_supports_flows(company_id: int, session: Session) -> bool:
    """Check if a company supports WhatsApp Flows (is verified by Meta)."""
    company = session.query(CompaniesScreening).filter_by(company_id=company_id).first()
    return bool(company and company.company_is_verified_by_meta)


def get_keyword_response_from_db(keyword: str, candidate_data: dict, session: Session):
    """
    Fetches a keyword response from the database.
    
    For reschedule_interview keyword:
    - Verified companies (company_is_verified_by_meta=True): uses reschedule_interview template (with Flow support)
    - Unverified companies (company_is_verified_by_meta=False): uses reschedule_interview_list template (interactive list, no Flow)
    """
    company_id = candidate_data.get("company_id")
    supports_flows = company_supports_flows(company_id, session) if company_id else False

    # For reschedule_interview keyword, determine template based on company verification status
    if keyword == "reschedule_interview":
        if not supports_flows:
            # Unverified company: use reschedule_interview_list (interactive list, no Flow)
            logging.info(f"Company {company_id} is NOT verified by Meta - using reschedule_interview_list template")
            message_obj = (
                session.query(MessageTemplates)
                .filter(
                    ((MessageTemplates.keyword == "reschedule_interview_list") | 
                     (MessageTemplates.button_trigger == "reschedule_interview_list"))
                )
                .first()
            )
            # If list version not found, log warning and fall back to regular lookup
            if not message_obj:
                logging.warning(
                    f"reschedule_interview_list template not found for unverified company {company_id}. "
                    f"Falling back to regular reschedule_interview template - this may cause errors!"
                )
                message_obj = (
                    session.query(MessageTemplates)
                    .filter((MessageTemplates.keyword == keyword) | (MessageTemplates.button_trigger == keyword))
                    .first()
                )
        else:
            # Verified company: use reschedule_interview (with Flow support)
            logging.info(f"Company {company_id} IS verified by Meta - using reschedule_interview template (with Flow)")
            message_obj = (
                session.query(MessageTemplates)
                .filter((MessageTemplates.keyword == keyword) | (MessageTemplates.button_trigger == keyword))
                .first()
            )
    else:
        # Regular lookup for all other keywords
        message_obj = (
            session.query(MessageTemplates)
            .filter((MessageTemplates.keyword == keyword) | (MessageTemplates.button_trigger == keyword))
            .first()
        )

    if not message_obj:
        logging.warning(f"No keyword matches for keyword: {keyword} and candidate_data: {candidate_data}")
        return None, None

    message_type = message_obj.type
    text = message_obj.text or ""
    
    if '{roles}' in text:
        roles_str = get_active_roles_text(session, candidate_data.get("company_id"))
    else:
        roles_str = ""
        
    role_value = candidate_data.get("role", "tu futuro empleo")
    if role_value is None:
        role_value = "tu futuro empleo"
        
    name_value = candidate_data.get("first_name", "candidato")
    if name_value is None:
        name_value = "candidato"
        
    text = text.format(
        name=name_value,
        company_name=candidate_data.get("company_name", "tu futuro empresa"),
        roles=roles_str,
        role=role_value,
        interview_date=candidate_data.get("interview_date",""),
        interview_address=candidate_data.get("interview_address",""),
    )
    text = text.replace('\\n', '\n')
    if message_type == "text":
        message_data = get_text_message_input(candidate_data["wa_id"], text)
    elif message_type == "interactive":
        if message_obj.interactive_type == "button":
                message_data = get_button_message_input(
                candidate_data,
                text,
                message_obj.button_keys,
                message_obj.footer_text,
                message_obj.header_type,
                message_obj.header_content
                )
        elif message_obj.interactive_type == "cta_url":
            message_data = get_ctaurl_message_input(
                candidate_data, 
                text, 
                message_obj.parameters, 
                message_obj.footer_text, 
                message_obj.header_type, 
                message_obj.header_content)
        elif message_obj.interactive_type == "location_request_message":
            message_data = get_location_message(candidate_data, text)

        elif message_obj.interactive_type == "list":
            message_data = get_list_message_input(
                candidate_data,
                text,
                message_obj.flow_cta,
                message_obj.list_section_title,
                message_obj.list_options,
                message_obj.footer_text,
                message_obj.header_type,
                message_obj.header_content
            )
    elif message_type == "roles_list":
        message_data = build_roles_list_message(candidate_data, message_obj, text, session)

    elif message_type == "eligibility_roles_list":
        message_data = build_eligibility_roles_list_message(candidate_data, message_obj, text, session)
    
    elif message_type == "eligibility_companies_list":
        message_data = build_eligibility_companies_list_message(candidate_data, message_obj, text, session)

    elif message_type == "education_list":
        message_data = build_academic_grade_message(candidate_data, message_obj, text)

    elif message_type == "rehire_list":
        message_data = build_rehire_list_message(candidate_data, message_obj, text)

    elif message_type == "template":
        message_data = get_template_message_input(
            message_obj.template,
            candidate_data,
            message_obj.variables,
            message_obj.button_keys,
            message_obj.header_type,
            message_obj.header_content,
            message_obj.url_keys,
            message_obj.header_base,
            message_obj.flow_keys,
            message_obj.flow_action_data
        )
    elif message_type == "reschedule_appointment":
        message_data = get_template_reschedule_appointment(
            template_name=message_obj.template,
            candidate_data=candidate_data,
            message_obj=message_obj,
            session=session
        )

    elif message_type == "generic_template_flow":
        message_data = get_generic_template_message_with_flow(
            template_name=message_obj.template,
            candidate_data=candidate_data,
            message_obj=message_obj
        )

    elif message_type == "document":
        message_data = get_document_message_input(
            candidate_data, message_obj.document_link, 
            text, 
            message_obj.filename
            )
    elif message_type == "appointment_scheduling":
        #Only send appointment scheduling flow if the user was not rejected
        if candidate_data["funnel_state"] == "screening_in_progress":
            message_data = appointment_booking_flow(
                candidate_data,
                message_obj.flow_name,
                message_obj.header_content,
                text,
                message_obj.footer_text,
                message_obj.flow_cta,
                session
            )
        else:
            text = "✅ ¡Listo! Esa fue la última pregunta\n📩 Nos pondremos en contacto contigo pronto para contarte si tenemos alguna vacante que se ajuste a tu perfil."
            mark_end_flow_rejected(session, candidate_data["candidate_id"])
            message_data = get_text_message_input(candidate_data["wa_id"], text)
    elif message_type == "request_documents":
        message_data = request_documents_flow(
            candidate_data,
            message_obj.flow_name,
            message_obj.header_content,
            text,
            message_obj.footer_text,
            message_obj.flow_cta
        )
    
    else:
        logging.warning(f"Invalid message type: {message_type} for message_obj: {message_obj}")
        return None, None

    return text, message_data

def get_text_message_input(recipient, text):
    """Build a simple text message"""
    text = process_text_for_whatsapp(text)
    message = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
            } 
    return json.dumps(message)

def get_button_message_input(candidate_data: dict, body_text: str, button_pairs: list, footer_text=None, header_type=None, header_content=None):
    """Build an interactive button message"""

    if not button_pairs:
        logging.warning("No buttons defined.")
        return None

    message = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": candidate_data["wa_id"],
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {"id": btn_id, "title": btn_title}
                    }
                    for btn_id, btn_title in button_pairs
                ]
            }
        }
    }

    if footer_text:
        message["interactive"]["footer"] = {"text": footer_text}

    if header_type and header_content:
        message["interactive"]["header"] = {
            "type": header_type,
            header_type: {"link": header_content}
        }

    return json.dumps(message)

def get_list_message_input(candidate_data: dict, text: str, button_text: str, list_section_title: str, list_options: list, footer_text=None, header_type=None, header_content=None):
    """Build an interactive list message"""

    sections = [
        {
            "title": list_section_title or "Opciones",
            "rows": list_options or []
        }
    ]

    message = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": candidate_data["wa_id"],
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {
                "text": text
            },
            "action": {
                "button": button_text,
                "sections": sections
            }
        }
    }

    if footer_text:
        message["interactive"]["footer"] = {"text": footer_text}

    if header_type == "text" and header_content:
        message["interactive"]["header"] = {
            "type": "text",
            "text": header_content
        }

    return json.dumps(message)

def get_ctaurl_message_input(candidate_data, body_text, parameters, footer_text=None, header_type=None, header_content=None):
    """Get a CTA URL interactive message"""
    message = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": candidate_data['wa_id'],
        "type": "interactive",
        "interactive": {
            "type": "cta_url",
            "body": {"text": body_text},
            "footer": {"text": footer_text},
            "action": {
                "name": "cta_url",
                "parameters": parameters
            }

        }
    }
    
    if footer_text:
        message["interactive"]["footer"] = {"text": footer_text}

    #Add header if needed
    if header_type and header_content:
        message["interactive"]["header"] = {
            "type": header_type,
            header_type: header_content
    }
    
    return json.dumps(message)

def get_template_message_input(
        template_name, candidate_data, variables=None, button_keys=None, 
        header_type=None, header_content=None, url_keys=None,
        header_base=None, flow_keys=None, flow_action_data=None):
    """Build a WhatsApp template message with dynamic components."""
    
    message = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": candidate_data["wa_id"],
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": "es_MX"
            },
            "components": []
        }
    }

    if header_type == 'image':
        try:
            if header_base:
                link = header_base
                if header_content:
                    link = link.format(candidate_data[header_content])
            else:
                link = candidate_data[header_content]

            header_component = {
                "type": "header",
                "parameters": [
                    {
                        "type": header_type,
                        header_type: {"link": link}
                    }
                ]
            }
            message["template"]["components"].append(header_component)

        except KeyError as e:
            logging.error(f"KeyError: Missing key '{e.args[0]}' in candidate_data for wa_id={candidate_data.get('wa_id')}")
        except Exception as e:
            logging.error(f"Unexpected error building header image: {e}")


    if variables:
        body_component = {
            "type": "body",
            "parameters": []
        }

        for placeholder, field in variables.items():
            body_component["parameters"].append({
                "type": "text",
                "text": candidate_data.get(field, "-")
            })
        
        message["template"]["components"].append(body_component)

    if url_keys:
        for index, url in enumerate(url_keys):
            url_component = {
                "type": "button",
                "sub_type": "url",
                "index": str(index),
                "parameters": [
                    {
                        "type": "text",
                        "text": candidate_data[url]
                    }
                ]
            }
            message["template"]["components"].append(url_component)
    
    if button_keys:
        offset = len(url_keys) if url_keys else 0
        for index, key in enumerate(button_keys):
            button_component = {
                "type": "button",
                "sub_type": "quick_reply",
                "index": str(index + offset),
                "parameters": [
                    {
                        "type": "payload",
                        "payload": key[0]
                    }
                ]
            }
            message["template"]["components"].append(button_component)
    

    if flow_keys:
        for index, flow_key in enumerate(flow_keys):
            action_dict = {"flow_token": generate_flow_token(flow_key)}
            
            if flow_action_data and index < len(flow_action_data):
                raw_data = flow_action_data[index]
                action_dict["flow_action_data"] = {
                    custom_key: candidate_data.get(field_name, "")
                    for custom_key, field_name in raw_data.items()
                }

            flow_component = {
                "type": "button",
                "sub_type": "flow",
                "index": str(index),
                "parameters": [{"type": "action", 
                                "action": action_dict
                                }
                                ]
            }
            message["template"]["components"].append(flow_component)
    return json.dumps(message)

def get_location_message(candidate_data, text):
    """Get a location request interactive message"""

    message = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": candidate_data["wa_id"],
        "type": "interactive",
        "interactive": {
            "type": "location_request_message",
            "body": {
                "text": text
            },
            "action": {
                "name": "send_location"
            }

        }
    }
    return json.dumps(message)

def get_document_message_input(candidate_data, document_link, text, filename):
    """Get a document message input"""

    text = process_text_for_whatsapp(text)
    message = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": candidate_data["wa_id"],
            "type": "document",
            "document": {
                "link": document_link, 
                "caption": text,
                "filename": filename}
            } 
    return json.dumps(message)

def appointment_booking_flow(candidate_data, flow_name, header, text, footer, flow_CTA, session: Session):
    company_id = candidate_data.get("company_id")
    company_data = get_company_screening_data(session, company_id)

    if not company_data:
        raise ValueError(f"No screening configuration found for company_id {company_id}")
    
    interview_address = company_data.get("interview_address_json", {})

    utc_now = datetime.now()
    mexico_now = utc_now - timedelta(hours=6)

    tomorrow = mexico_now.date() + timedelta(days=1)
    start_date = tomorrow.strftime('%Y-%m-%d')
    search_end_date = (tomorrow + timedelta(days=7)).strftime('%Y-%m-%d')

    all_hours = company_data["interview_hours"]
    max_capacity = company_data.get("max_interviews_per_slot")
    interview_days = company_data.get("interview_days", [])
    unavailable_dates = company_data.get("unavailable_dates", [])

    # Per-date availability (max 4 days for WhatsApp Flow)
    available_dates = get_available_dates_and_hours(
        session,
        company_id,
        start_date,
        search_end_date,
        all_hours,
        max_capacity,
        interview_days,
        unavailable_dates,
        max_days=4,
    )

    # Limit end_date to the last available date returned
    if available_dates:
        end_date = available_dates[-1]["date"]
    else:
        end_date = start_date

    # Build flow data with date_N and hours_N (per-date hours, already flagged with enabled)
    flow_data = {
        "start_date": start_date,
        "end_date": end_date,
        "dirección": interview_address.get("location_1", "No disponible"),
        "unavailable_dates": unavailable_dates,
        "include_days": interview_days,
    }
    for i, date_info in enumerate(available_dates, start=1):
        flow_data[f"date_{i}"] = date_info["date"]
        flow_data[f"hours_{i}"] = date_info["hours"]

    message = {
        "recipient_type": "individual",
        "messaging_product": "whatsapp",
        "to": candidate_data["wa_id"],
        "type": "interactive",
        "interactive": {
            "type": "flow",
            "header": {
                "type": "text",
                "text": header
            },
            "body": {
                "text": text
            },
            "footer": {
                "text": footer
            },
            "action": {
                "name": "flow",
                "parameters": {
                    "flow_message_version": "3",
                    "flow_token": generate_flow_token("appointment_booking", 1),
                    "flow_name": flow_name,
                    "mode": "published",
                    "flow_cta": flow_CTA,
                    "flow_action": "navigate",
                    "flow_action_payload": {
                        "screen": "FECHA",
                        "data": flow_data,
                    }
                }
            }
        }
    }

    return json.dumps(message)

def get_template_reschedule_appointment(template_name, candidate_data, message_obj, session: Session):
    """Build a WhatsApp template message for rescheduling appointments."""

    message = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": candidate_data["wa_id"],
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": "es_MX"
            },
            "components": []
        }
    }

    if message_obj.variables:
        body_component = {
            "type": "body",
            "parameters": []
        }
        for _, field in message_obj.variables.items():
            body_component["parameters"].append({
                "type": "text",
                "text": candidate_data.get(field, "")
            })
        message["template"]["components"].append(body_component)


    company_id = candidate_data.get("company_id")
    company_data = get_company_screening_data(session, company_id)
    interview_address = company_data.get("interview_address_json", {})

    utc_now = datetime.now()
    mexico_now = utc_now - timedelta(hours=6)
    tomorrow = mexico_now.date() + timedelta(days=1)
    start_date = tomorrow.strftime('%Y-%m-%d')
    search_end_date = (tomorrow + timedelta(days=7)).strftime('%Y-%m-%d')

    all_hours = company_data["interview_hours"]
    max_capacity = company_data.get("max_interviews_per_slot")
    interview_days = company_data.get("interview_days", [])
    unavailable_dates = company_data.get("unavailable_dates", [])

    available_dates = get_available_dates_and_hours(
        session,
        company_id,
        start_date,
        search_end_date,
        all_hours,
        max_capacity,
        interview_days,
        unavailable_dates,
        max_days=4,
    )

    if available_dates:
        end_date = available_dates[-1]["date"]
    else:
        end_date = start_date

    flow_action_data = {
        "start_date": start_date,
        "end_date": end_date,
        "dirección": interview_address.get("location_1", "No disponible"),
        "unavailable_dates": unavailable_dates,
        "include_days": interview_days,
    }
    for i, date_info in enumerate(available_dates, start=1):
        flow_action_data[f"date_{i}"] = date_info["date"]
        flow_action_data[f"hours_{i}"] = date_info["hours"]

    flow_token = generate_flow_token(message_obj.flow_keys[0])
    flow_button = {
        "type": "button",
        "sub_type": "flow",
        "index": "0",
        "parameters": [
            {
                "type": "action",
                "action": {
                    "flow_token": flow_token,
                    "flow_action_data": flow_action_data
                }
            }
        ]
    }

    message["template"]["components"].append(flow_button)
    logging.info(f'Message Structure: {json.dumps(message)}')
    return json.dumps(message)

#Flow to request documents
def request_documents_flow(candidate_data, flow_name, header, text, footer, flow_CTA):

    message = {
        "recipient_type": "individual",
        "messaging_product": "whatsapp",
        "to": candidate_data["wa_id"],
        "type": "interactive",
        "interactive": {
            "type": "flow",
            "header": {
                "type": "text",
                "text": header
            },
            "body": {
                "text": text
            },
            "footer": {
                "text": footer
            },
            "action": {
                "name": "flow",
                "parameters": {
                    "flow_message_version": "3",
                    "flow_token": generate_flow_token(flow_name, 1),
                    "flow_name": flow_name,
                    "mode": "published",
                    "flow_cta": flow_CTA,
                    "flow_action": "navigate",
                    "flow_action_payload": {
                        "screen": "RFC"
                    }
                }
            }
        }
    }

    return json.dumps(message)

def build_roles_list_message(candidate_data, message_obj, text, session: Session):
    """Builds a WhatsApp interactive list message showing active roles for the candidate's company."""
    company_id = candidate_data.get("company_id")
    if not company_id:
        logging.error("Missing company_id in candidate_data")
        return None

    roles = get_active_roles_for_company(session, company_id)
    if not roles:
        logging.warning(f"No active roles found for company {company_id}")
        return None

    list_options = [
        {
            "id": f"role_id${role['role_id']}",
            "title": role["role_name"],
            "description": role.get("shift", "")
        }
        for role in roles
    ]

    return get_list_message_input(
        candidate_data,
        text,
        message_obj.flow_cta,
        message_obj.list_section_title,
        list_options,
        message_obj.footer_text,
        message_obj.header_type,
        message_obj.header_content
    )

def build_academic_grade_message(candidate_data, message_obj, text):
    """Builds a WhatsApp interactive list message showing academic grades."""
    academic_grades = [
        "Ninguno",
        "Primaria",
        "Secundaria",
        "Preparatoria",
        "Preparatoria Técnica",
        "Licenciatura"
    ]

    list_options = [
        {
            "id": f"education_level${grade.replace(' ', '_').lower()}",
            "title": grade,
            "description": ""
        }
        for grade in academic_grades
    ]

    return get_list_message_input(
        candidate_data,
        text,
        message_obj.flow_cta,
        message_obj.list_section_title,
        list_options,
        message_obj.footer_text,
        message_obj.header_type,
        message_obj.header_content
    )

def build_eligibility_roles_list_message(candidate_data, message_obj, text, session: Session):
    """Builds a WhatsApp interactive list message showing eligible roles for the candidate."""
    candidate_id = candidate_data.get("candidate_id")
    if not candidate_id:
        logging.error("Missing candidate_id in candidate_data")
        return None

    # Get eligible role IDs
    eligible_role_ids = get_candidate_eligible_roles(session, candidate_id)
    if not eligible_role_ids:
        logging.warning(f"No eligible roles found for candidate {candidate_id}")
        return None

    company_id = candidate_data.get("company_id")
    all_roles = get_active_roles_for_company(session, company_id)
    eligible_roles = [role for role in all_roles if role["role_id"] in eligible_role_ids]

    if not eligible_roles:
        logging.warning(f"No matching active roles found for eligible role IDs {eligible_role_ids}")
        return None

    list_options = [
        {
            "id": f"role_id${role['role_id']}",
            "title": role["role_name"],
            "description": role.get("shift", "") 
        }
        for role in eligible_roles
    ]

    if len(eligible_roles) > 1:
        list_options.append({
            "id": "no_preference",
            "title": "No tengo preferencia",
            "description": "Cualquiera de estos puestos me interesa"
        })

    return get_list_message_input(
        candidate_data,
        text,
        message_obj.flow_cta,
        message_obj.list_section_title,
        list_options,
        message_obj.footer_text,
        message_obj.header_type,
        message_obj.header_content
    )

def build_eligibility_companies_list_message(candidate_data, message_obj, text, session: Session):
    """Builds a WhatsApp interactive list message showing eligible companies for the candidate."""
    candidate_id = candidate_data.get("candidate_id")
    if not candidate_id:
        logging.error("Missing candidate_id in candidate_data")
        return None

    eligible_companies = get_candidate_eligible_companies(session, candidate_id)  
    if not eligible_companies:
        logging.warning(f"No eligible companies found for candidate {candidate_id}")
        return None

    list_options = [
        {
            "id": f"company_id${company['company_id']}",
            "title": company["name"],
            "description": company.get("address", "")
        }
        for company in eligible_companies
    ]

    return get_list_message_input(
        candidate_data,
        text,
        message_obj.flow_cta,
        message_obj.list_section_title,
        list_options,
        message_obj.footer_text,
        message_obj.header_type,
        message_obj.header_content
    )

def build_rehire_list_message(candidate_data, message_obj, text):
    """Builds a WhatsApp interactive list message asking if the candidate has worked here before."""
    list_options = [
        {
            "id": "worked_here$true",
            "title": "Si",
            "description": ""
        },
        {
            "id": "worked_here$false",
            "title": "No",
            "description": ""
        }
    ]

    return get_list_message_input(
        candidate_data,
        text,
        message_obj.flow_cta,
        message_obj.list_section_title,
        list_options,
        message_obj.footer_text,
        message_obj.header_type,
        message_obj.header_content
    )

def get_generic_template_message_with_flow(template_name, candidate_data, message_obj):
    """Builds a WhatsApp template message with a flow button."""
    message = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": candidate_data["wa_id"],
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": "es_MX"
            },
            "components": []
        }
    }

    if message_obj and getattr(message_obj, "variables", None):
        body_component = {
            "type": "body",
            "parameters": []
        }
        for _, field in message_obj.variables.items():
            body_component["parameters"].append({
                "type": "text",
                "text": candidate_data.get(field, "")
            })
        message["template"]["components"].append(body_component)

    flow_token = generate_flow_token(message_obj.flow_keys[0])
    flow_button = {
        "type": "button",
        "sub_type": "flow",
        "index": "0",
        "parameters": [
            {
                "type": "action",
                "action": {
                    "flow_token": flow_token
                }
            }
        ]
    }
    message["template"]["components"].append(flow_button)

    logging.info(f'Message Structure: {json.dumps(message)}')
    return json.dumps(message)

def generate_flow_token(flow_type, expiration_days=7):
    """Generates a unique flow token with an expiration date."""
    expiration_date = datetime.now() + timedelta(days=expiration_days)
    token_data = {
        "flow_type": flow_type,
        "expiration_date": expiration_date.isoformat()  # Store expiration date as ISO format string
    }
    return json.dumps(token_data)

def process_text_for_whatsapp(text):
    pattern = r"\【.*?\】"
    text = re.sub(pattern, "", text).strip()

    pattern = r"\*\*(.*?)\*\*"
    replacement = r"*\1*"
    whatsapp_style_text = re.sub(pattern, replacement, text)
    whatsapp_style_text = whatsapp_style_text.replace('\\n', '\n')

    return whatsapp_style_text

