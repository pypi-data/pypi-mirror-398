"""
This package contains JSON schema files for HEA. Currently, there are files for Web Service Transition Language (WSTL),
Collection+JSON, and simple JSON objects. These schemas are available to users of HEA as constants in the
heaserver.service.jsonschema package. Validators for these schemas may be found in the
heaserver.service.jsonschemavalidator package.

For developers of these schemas, HEA JSON schema files are expected to have the following constraints:
* They must be stored in this package.
* They must not have an $id field
* $refs must be of the form "file:filename.json".
"""
