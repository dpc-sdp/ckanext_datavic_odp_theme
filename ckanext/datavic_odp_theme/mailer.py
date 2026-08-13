from __future__ import annotations

from typing import Any, Optional

import ckan.lib.mailer as ckan_mailer
import ckan.plugins.toolkit as tk
from ckan import model


def _base_vars(user: model.User) -> dict[str, Any]:
    return {
        "reset_link": ckan_mailer.get_reset_link(user),
        "site_title": tk.config.get("ckan.site_title"),
        "site_url": tk.config.get("ckan.site_url"),
        "user_name": user.name,
    }


def _subject(template: str, site_title: Optional[str]) -> str:
    # First line only - guards against the {% trans %} trailing newline
    # becoming a header-injection vector (matches core behaviour).
    return tk.render(template, {"site_title": site_title}).split("\n")[0]


def send_reset_link(user: model.User) -> None:
    """As ckan.lib.mailer.send_reset_link, plus an HTML alternative."""
    ckan_mailer.create_reset_key(user)          # must precede get_reset_link
    extra_vars = _base_vars(user)

    ckan_mailer.mail_user(
        user,
        _subject("emails/reset_password_subject.txt", extra_vars["site_title"]),
        tk.render("emails/reset_password.txt", extra_vars),
        body_html=tk.render("emails/reset_password.html", extra_vars),
    )


def send_invite(
    user: model.User,
    group_dict: Optional[dict[str, Any]] = None,
    role: Optional[str] = None,
) -> None:
    """As ckan.lib.mailer.send_invite, plus an HTML alternative."""
    ckan_mailer.create_reset_key(user)
    extra_vars = _base_vars(user)

    if role:
        extra_vars["role_name"] = tk.h.roles_translated().get(role, tk._(role))
    if group_dict:
        extra_vars["group_type"] = (
            tk._("organization") if group_dict["is_organization"] else tk._("group")
        )
        extra_vars["group_title"] = group_dict.get("title")

    ckan_mailer.mail_user(
        user,
        _subject("emails/invite_user_subject.txt", extra_vars["site_title"]),
        tk.render("emails/invite_user.txt", extra_vars),
        body_html=tk.render("emails/invite_user.html", extra_vars),
    )
