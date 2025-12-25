"""Email templates."""


def password_reset_email_template(user_name: str, reset_link: str) -> tuple[str, str]:
    """
    Generate password reset email content.

    Args:
        user_name: User's name
        reset_link: Password reset link

    Returns:
        Tuple of (subject, html_body)
    """
    subject = "Password Reset Request"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .button {{ 
                display: inline-block; 
                padding: 12px 24px; 
                background-color: #007bff; 
                color: #ffffff; 
                text-decoration: none; 
                border-radius: 4px;
                margin: 20px 0;
            }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Password Reset Request</h2>
            <p>Hello {user_name},</p>
            <p>We received a request to reset your password. Click the button below to reset it:</p>
            <a href="{reset_link}" class="button">Reset Password</a>
            <p>Or copy and paste this link into your browser:</p>
            <p><a href="{reset_link}">{reset_link}</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request a password reset, please ignore this email.</p>
            <div class="footer">
                <p>This is an automated email, please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return subject, html


def welcome_email_template(user_name: str) -> tuple[str, str]:
    """
    Generate welcome email content.

    Args:
        user_name: User's name

    Returns:
        Tuple of (subject, html_body)
    """
    subject = "Welcome to Apex!"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Welcome to Apex!</h2>
            <p>Hello {user_name},</p>
            <p>Thank you for signing up! We're excited to have you on board.</p>
            <p>Get started by exploring our features and setting up your profile.</p>
            <div class="footer">
                <p>This is an automated email, please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return subject, html


def email_verification_template(user_name: str, verification_link: str) -> tuple[str, str]:
    """
    Generate email verification content.

    Args:
        user_name: User's name
        verification_link: Email verification link

    Returns:
        Tuple of (subject, html_body)
    """
    subject = "Verify Your Email Address"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .button {{ 
                display: inline-block; 
                padding: 12px 24px; 
                background-color: #28a745; 
                color: #ffffff; 
                text-decoration: none; 
                border-radius: 4px;
                margin: 20px 0;
            }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Verify Your Email Address</h2>
            <p>Hello {user_name},</p>
            <p>Please verify your email address by clicking the button below:</p>
            <a href="{verification_link}" class="button">Verify Email</a>
            <p>Or copy and paste this link into your browser:</p>
            <p><a href="{verification_link}">{verification_link}</a></p>
            <div class="footer">
                <p>This is an automated email, please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return subject, html

