import os
import platform

"""
Shared Gmail token helpers. We lean on the MediCafe config/logging loaders as the
authoritative source of environment state so every entry point (CLI, MediLink app,
error reporter, etc.) resolves tokens/credentials consistently.
"""

from MediCafe.core_utils import get_shared_config_loader, extract_medilink_config
from MediCafe.MediLink_ConfigLoader import load_configuration
from MediLink.gmail_oauth_utils import (
    get_access_token_with_refresh,
    clear_token_cache as oauth_clear_token_cache,
    save_token_file as oauth_save_token_file,
)

DEFAULT_TOKEN_FILENAME = 'token.json'
# XP deployment lives on a fixed drive layout (F:\Medibot\...) so we keep the original
# absolute fallback rather than trying to infer relative paths at runtime.
DEFAULT_CREDENTIALS_RELATIVE = os.path.join('json', 'credentials.json')
XP_CREDENTIALS_PATH = r'F:\Medibot\json\credentials.json'


def _fallback_log(message, level="INFO"):
    try:
        print("[{}] {}".format(level, message))
    except Exception:
        pass


def _resolve_log(log):
    if callable(log):
        return log
    try:
        loader = get_shared_config_loader()
        if loader and hasattr(loader, 'log') and callable(loader.log):
            return loader.log
    except Exception:
        pass
    return _fallback_log


def _ensure_medi_config(medi_config):
    if isinstance(medi_config, dict) and medi_config:
        return medi_config
    try:
        config, _ = load_configuration()
        return extract_medilink_config(config)
    except Exception:
        return {}


def resolve_token_path(medi_config=None):
    medi = _ensure_medi_config(medi_config)
    try:
        configured = medi.get('gmail_token_path')
        if configured:
            return configured
    except Exception:
        pass
    return DEFAULT_TOKEN_FILENAME


def resolve_credentials_path(medi_config=None, os_name=None, os_version=None):
    medi = _ensure_medi_config(medi_config)
    try:
        configured = medi.get('gmail_credentials_path')
        if configured:
            return configured
    except Exception:
        pass
    if os_name is None:
        os_name = platform.system()
    if os_version is None:
        os_version = platform.release()
    if os_name == 'Windows' and isinstance(os_version, str) and 'XP' in os_version:
        return XP_CREDENTIALS_PATH
    # Non-XP installs keep json/credentials.json next to the tooling even if the absolute
    # project root differs between dev (Win11) and prod (XP). Respect the relative path to
    # avoid baking in dev-only directories.
    return DEFAULT_CREDENTIALS_RELATIVE


def get_token_paths(medi_config=None, os_name=None, os_version=None):
    token_path = resolve_token_path(medi_config)
    credentials_path = resolve_credentials_path(medi_config, os_name=os_name, os_version=os_version)
    return token_path, credentials_path


def get_gmail_access_token(log=None, medi_config=None, os_name=None, os_version=None):
    log_fn = _resolve_log(log)
    token_path, credentials_path = get_token_paths(medi_config, os_name=os_name, os_version=os_version)
    return get_access_token_with_refresh(token_path, credentials_path, log_fn)


def clear_gmail_token_cache(log=None, medi_config=None):
    log_fn = _resolve_log(log)
    token_path = resolve_token_path(medi_config)
    oauth_clear_token_cache(token_path, log_fn)


def save_gmail_token(token_data, log=None, medi_config=None):
    log_fn = _resolve_log(log)
    token_path = resolve_token_path(medi_config)
    return oauth_save_token_file(token_path, token_data, log_fn)
