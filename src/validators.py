
import re

from errors import ValidationError


def validatefeedback_id(feedback_id):
    pattern = re.compile("[0-9a-z]{8}(-[0-9a-z]{4}){3}-[0-9a-z]{12}$")
    if not pattern.match(feedback_id):
        msg = f"Unexpected feedback id format. Expecting i.e.: 1ab8eeec-7f60-4af0-ba16-06ad6f55a8a9, found: {feedback_id}"
        raise ValidationError(msg)
