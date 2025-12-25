"""
Properties that are loaded into the aiohttp request context.

HEA_WSTL_BUILDER - A heaserver.service.wstl.RuntimeWeSTLDocumentBuilder instance.
HEA_ATTRIBUTE_ENCRYPTION_KEY - The symmetric key used to encrypt and decrypt sensitive HEAObject attributes. It is
    populated automatically. It is also used at present to decrypt configuration properties, but this could change in
    the future.
"""

HEA_WSTL_BUILDER = 'HEA_wstl_document'
HEA_ATTRIBUTE_ENCRYPTION_KEY = 'HEA_attribute_encryption_key'
