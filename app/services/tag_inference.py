def infer_tag_from_text(text: str) -> str | None:
    """
    Infers the document tag based on the content of the text.
    Prioritizes detecting Forms/Templates, then Guidelines, then Notifications/Circulars.
    """
    text_lower = text.lower()

    # Priority 1: Forms, Templates, Checklists
    # These are often actionable documents or templates to be filled
    form_keywords = [
        "form", "template", "checklist", "affidavit", "annexure", 
        "application for", "declaration", "format of"
    ]
    if any(keyword in text_lower for keyword in form_keywords):
        return "FORMS"

    # Priority 2: Guidelines, Rules, Procedures
    # Documents that describe how to do something or set rules
    guideline_keywords = [
        "guideline", "procedure", "standard operating procedure", "sop",
        "manual", "rule", "regulation", "direction"
    ]
    if any(keyword in text_lower for keyword in guideline_keywords):
        return "GUIDELINES"

    # Priority 3: Notifications, Circulars, Orders
    # Official communications, updates, or legal notices
    notification_keywords = [
        "notification", "circular", "public notice", "order", "memorandum", 
        "office order", "notice", "amendment"
    ]
    if any(keyword in text_lower for keyword in notification_keywords):
        return "NOTIFICATIONS"

    return "OTHERS"
