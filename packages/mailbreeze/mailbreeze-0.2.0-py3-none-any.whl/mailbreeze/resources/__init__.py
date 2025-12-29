"""Resource classes for MailBreeze API."""

from mailbreeze.resources.attachments import Attachments
from mailbreeze.resources.automations import Automations, Enrollments
from mailbreeze.resources.base import BaseResource
from mailbreeze.resources.contacts import Contacts
from mailbreeze.resources.emails import Emails
from mailbreeze.resources.lists import Lists
from mailbreeze.resources.verification import Verification

__all__ = [
    "Attachments",
    "Automations",
    "BaseResource",
    "Contacts",
    "Emails",
    "Enrollments",
    "Lists",
    "Verification",
]
