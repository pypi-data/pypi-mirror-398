"""
The representor package contains modules that transform data between WeSTL and
a RESTful API output format, and a factory for getting an object that outputs
in the format with a specified mime type. Each representor module implements a
different output format and implements the following:

(required) MIME_TYPE: the format's mime type.

(optional) async def formats(wstl_obj, coll_url, dumps=heaobject.root.json_dumps): formats a
run-time WeSTL document into the output format. This function may not be
implemented for input formats that do not support data output.

(optional) async def parses(request): parses an HTTP request containing form
fields into a dict with NVP (name-value pair JSON). This function may not be
implemented for representor formats that do not support data input. If
implemented, representor modules are expected to output a dictionary in which
the key-value pairs are in the same order as the form fields are submitted in
HTTP request.


The representor concept comes from:
Amundsen, Mike. RESTful Web Clients. Sebastopol, CA: O'Reilly Media, Inc., 2017.

Use the package as follows:
>>> from heaserver.service.representor import factory
>>> foo = factory.from_accept_header('application/json')  # For Accept headers
>>> type(foo).__name__
'NVPJSON'
>>> bar = factory.from_content_type_header('application/x-www-form-urlencoded')
>>> type(bar).__name__
'XWWWFormURLEncoded'
"""
