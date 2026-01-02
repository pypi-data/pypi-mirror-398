"""
Courier Namespace - Email delivery via Postmark.

Provides email sending using Postmark templates.
"""
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..start import Dominus


class CourierNamespace:
    """
    Email delivery namespace.

    All email operations go through /api/courier/* endpoints.
    Uses Postmark for transactional email delivery.

    Usage:
        # Send welcome email
        result = await dominus.courier.send(
            template_alias="welcome",
            to="user@example.com",
            from_email="noreply@myapp.com",
            model={
                "name": "John Smith",
                "product_name": "My App"
            }
        )

        # Send with tracking tag
        result = await dominus.courier.send(
            template_alias="password-reset",
            to="user@example.com",
            from_email="noreply@myapp.com",
            model={"reset_link": "https://..."},
            tag="password-reset"
        )
    """

    def __init__(self, client: "Dominus"):
        self._client = client

    async def send(
        self,
        template_alias: str,
        to: str,
        from_email: str,
        model: Dict[str, Any],
        tag: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email using Postmark template.

        Args:
            template_alias: Template alias in Postmark (e.g., "welcome", "password-reset")
            to: Recipient email address
            from_email: Sender email address (must be verified in Postmark)
            model: Template model variables (dict of key-value pairs)
            tag: Optional tag for tracking/filtering in Postmark
            reply_to: Optional reply-to address

        Returns:
            Dict with:
                - to: Recipient email
                - message_id: Postmark message UUID
                - submitted_at: Timestamp

        Example:
            result = await dominus.courier.send(
                template_alias="welcome",
                to="john@example.com",
                from_email="hello@myapp.com",
                model={
                    "name": "John",
                    "company_name": "My App",
                    "action_url": "https://myapp.com/verify?token=abc123"
                },
                tag="welcome"
            )
            print(f"Email sent: {result['message_id']}")
        """
        body = {
            "template_alias": template_alias,
            "to": to,
            "from": from_email,
            "model": model
        }

        if tag:
            body["tag"] = tag
        if reply_to:
            body["reply_to"] = reply_to

        return await self._client._request(
            endpoint="/api/courier/send",
            body=body
        )

    # Convenience methods for common templates

    async def send_welcome(
        self,
        to: str,
        from_email: str,
        name: str,
        product_name: str,
        action_url: Optional[str] = None,
        **extra_model
    ) -> Dict[str, Any]:
        """
        Send welcome email.

        Args:
            to: Recipient email
            from_email: Sender email
            name: User's name
            product_name: Your product/app name
            action_url: Optional action button URL
            **extra_model: Additional template variables

        Returns:
            Send result dict
        """
        model = {
            "name": name,
            "product_name": product_name,
            **extra_model
        }
        if action_url:
            model["action_url"] = action_url

        return await self.send(
            template_alias="welcome",
            to=to,
            from_email=from_email,
            model=model,
            tag="welcome"
        )

    async def send_password_reset(
        self,
        to: str,
        from_email: str,
        name: str,
        reset_url: str,
        product_name: str,
        **extra_model
    ) -> Dict[str, Any]:
        """
        Send password reset email.

        Args:
            to: Recipient email
            from_email: Sender email
            name: User's name
            reset_url: Password reset link
            product_name: Your product/app name
            **extra_model: Additional template variables

        Returns:
            Send result dict
        """
        return await self.send(
            template_alias="password-reset",
            to=to,
            from_email=from_email,
            model={
                "name": name,
                "action_url": reset_url,
                "product_name": product_name,
                **extra_model
            },
            tag="password-reset"
        )

    async def send_email_verification(
        self,
        to: str,
        from_email: str,
        name: str,
        verify_url: str,
        product_name: str,
        **extra_model
    ) -> Dict[str, Any]:
        """
        Send email verification email.

        Args:
            to: Recipient email
            from_email: Sender email
            name: User's name
            verify_url: Email verification link
            product_name: Your product/app name
            **extra_model: Additional template variables

        Returns:
            Send result dict
        """
        return await self.send(
            template_alias="email-verification",
            to=to,
            from_email=from_email,
            model={
                "name": name,
                "action_url": verify_url,
                "product_name": product_name,
                **extra_model
            },
            tag="email-verification"
        )

    async def send_invitation(
        self,
        to: str,
        from_email: str,
        name: str,
        invite_url: str,
        inviter_name: str,
        product_name: str,
        **extra_model
    ) -> Dict[str, Any]:
        """
        Send user invitation email.

        Args:
            to: Recipient email
            from_email: Sender email
            name: Invitee's name
            invite_url: Invitation accept link
            inviter_name: Name of person who invited
            product_name: Your product/app name
            **extra_model: Additional template variables

        Returns:
            Send result dict
        """
        return await self.send(
            template_alias="invitation",
            to=to,
            from_email=from_email,
            model={
                "name": name,
                "action_url": invite_url,
                "inviter_name": inviter_name,
                "product_name": product_name,
                **extra_model
            },
            tag="invitation"
        )
