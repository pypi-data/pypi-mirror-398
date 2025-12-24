"""Pydantic models for secret_management."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class MatcherType(F5XCBaseModel):
    """A matcher specifies multiple criteria for matching an input string. The..."""

    exact_values: Optional[list[str]] = None
    regex_values: Optional[list[str]] = None
    transformers: Optional[list[Literal['LOWER_CASE', 'UPPER_CASE', 'BASE64_DECODE', 'NORMALIZE_PATH', 'REMOVE_WHITESPACE', 'URL_DECODE', 'TRIM_LEFT', 'TRIM_RIGHT', 'TRIM']]] = None


class LabelSelectorType(F5XCBaseModel):
    """This type can be used to establish a 'selector reference' from one..."""

    expressions: Optional[list[str]] = None


class GlobalSpecType(F5XCBaseModel):
    """A secret_policy_rule object consists of an unordered list of predicates..."""

    action: Optional[Literal['DENY', 'ALLOW', 'NEXT_POLICY']] = None
    client_name: Optional[str] = None
    client_name_matcher: Optional[MatcherType] = None
    client_selector: Optional[LabelSelectorType] = None


class PolicyInfoType(F5XCBaseModel):
    """policy_information contains the shape and specifications of the secret policy."""

    algo: Optional[Literal['FIRST_MATCH', 'DENY_OVERRIDES', 'ALLOW_OVERRIDES']] = None
    rules: Optional[list[GlobalSpecType]] = None


class PolicyData(F5XCBaseModel):
    """policy_data contains the information about the secret policy and all the..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    policy_id: Optional[str] = None
    policy_info: Optional[PolicyInfoType] = None
    tenant: Optional[str] = None


class GetPolicyDocumentResponse(F5XCBaseModel):
    """Policy Document contains the information about the secret policy and all..."""

    data: Optional[PolicyData] = None


class KeyData(F5XCBaseModel):
    """F5XC Secret Management uses asymmetric cryptography for securing..."""

    key_version: Optional[int] = None
    modulus_base64: Optional[str] = None
    public_exponent_base64: Optional[str] = None
    tenant: Optional[str] = None


class GetPublicKeyResponse(F5XCBaseModel):
    """F5XC Secret Management uses asymmetric cryptography for securing..."""

    data: Optional[KeyData] = None


# Convenience aliases
Spec = GlobalSpecType
