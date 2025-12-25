"""Helper"""

# flake8: noqa: E402
# -*- coding: utf-8 -*-
# (c) 2025 BeyondTrust Inc.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


def get_authentication_parameters():
    """
    Get common authentication parameters definition

    Returns:
        dict: Common parameters definition
    """
    params = dict(
        api_url=dict(type="str", required=True),
        client_id=dict(type="str", required=True, no_log=True),
        client_secret=dict(type="str", required=True, no_log=True),
        api_version=dict(type="str", required=True),
    )

    return params
