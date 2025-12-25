"""
Header constants for the Open ID Connect standard claims, and additional claims specific to HEA, that are set by the
HEA reverse proxy. The standard claim headers are prefixed by OIDC_CLAIM_.

Definitions of the standard claims may be found at
https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims. This document also specifies requirements
for using additional claims, which HEA follows.

The following constants contain the names of the claim headers:
SUB: the sub claim.
AUD: the aud (audience) claim.
CLAIM_HEADERS: a tuple containing all of the claim header names.
"""

SUB = 'OIDC_CLAIM_sub'  # currently logged in user ("subject")
AUD = 'OIDC_CLAIM_aud'  # intended user
AZP = 'OIDC_CLAIM_azp'  # client id
ISS = 'OIDC_CLAIM_iss'  # OIDC provider URL
ACCESS_TOKEN = 'OIDC_access_token'  # access token used to authenticate the user
EMAIL = 'OIDC_CLAIM_email'  # email claim
NAME = 'OIDC_CLAIM_name'  # name claim
FAMILY_NAME = 'OIDC_CLAIM_family_name'  # family name claim
GIVEN_NAME = 'OIDC_CLAIM_given_name'  # given name claim
SESSION_STATE = 'OIDC_CLAIM_session_state'  # session state value returned by the OIDC provider
PREFERRED_USERNAME = 'OIDC_CLAIM_preferred_username'  # preferred username claim

CLAIM_HEADERS = (SUB, AUD, AZP, ISS, ACCESS_TOKEN, EMAIL, NAME, FAMILY_NAME, GIVEN_NAME, SESSION_STATE, PREFERRED_USERNAME)
