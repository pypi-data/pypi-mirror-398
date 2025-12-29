def send_email(body:str, to_email:str, from_email: str = "me") -> str:
    """Send Email to someone.

    Args:
        from_email (str): The sender
        to_email (str): The receiver email
        body (str): The body of email

    Returns:
        The string to say hello.

    """
    
    return f"Email has been sent to {to_email}"
