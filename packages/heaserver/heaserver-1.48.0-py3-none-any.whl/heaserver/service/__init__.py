"""
HEA Server Framework is a framework library for creating HEA microservices.

Types of microservices

The registry microservice manages a listing of all microservices that the current instance of HEA knows about.

Trash microservices serve items that have been marked for permanent deletion but have not been permanently deleted yet.
The registry service may have at most one trash microservice registered for a given desktop object type, file system
type, and file system name combination. Desktop object types with no registered trash microservice are assumed not to
have a trash and are deleted permanently.

Class in this package and all microservices have the following conventions for object attributes:
* Private attributes' names are prefixed with a double underscore.
* Protected attributes' names are prefixed with a single underscore. "Protected" is defined as accessible only to
the class in which it's defined and subclasses. Python does not enforce protected access, but uses of protected
attributes outside of subclasses may break even in patch releases.

HEA adheres to the following URL conventions:
* access_token is a reserved query parameter. It is an alternative to passing the Bearer token in the request's
Authorization header.
* get requests may accept a data parameter with values true/false/yes/no/t/f/y/n (case insensitive) that controls
whether the desktop object and the requesting user's permissions for it are included in the response. Endpoints may
ignore this parameter.
* Getting a desktop object's contents: append /content to the object's URL. Optionally pass the mode query parameter,
which has two possible values, download (to download the content from a browser) or open (to open the content in a
browser). The default is download.

HEA objects support various operations similar to those in a file system, such as copy, move, delete, and rename. These
operations are not guaranteed to be atomic, and may not be supported by all objects. Here are some expected behaviors:
* Objects may be versioned or unversioned, indicated by the presence of a version attribute. Versioned objects have a
  version history, while unversioned objects do not. Versioned objects support permanently deleting old versions. They
  also support making a selected old version the current version, which moves the selected version to the top of the
  version history, potentially changing the version's version id in the process.
* Copying an object to a different location creates a new object with the same content as the original. For versioned
  objects, only the latest version is copied. Copying an object to the same location must not change the object.
* Moving an object to a different location may change object metadata without physically moving the object, or it may
  create a new object with the same content as the original and deletes the original object. For versioned objects,
  moving an object within a volume also moves all versions of the original object to the new location. Moving an object
  to a different volume only moves the latest version of the object and discards all versions in the original location.
  For volumes that support the Trash, the original object and its versions may be restorable from the Trash.
* Deleting an object may either permanently delete it or move it to the Trash, depending on whether the object's volume
  supports the Trash. All the object's versions must also be moved or permanently deleted. A "move" to the Trash may be
  implemented as an actual move, or the object may stay in the same location, including all its versions for versioned
  objects, but be annotated as deleted. The user must be warned if the object is about to be permanently deleted.
* Renaming an object changes its name, and depending on the underlying file system, may be implemented as a metadata
  change or an actual move. For versioned objects, all versions of the object are renamed.

REST API endpoints that return multiple resources use an undefined order for the returned resources by default. To
specify an order, use the sort query parameter with a value of either asc or desc (ascending or descending,
respectively). The parameter's values are case insensitive. A sort query parameter will apply to an endpoint-specific
default attribute. An endpoint may allow overriding the default attribute with a sort_attr query parameter. To specify
different sort orders for different attributes, an endpoint may support specifying multiple sort query parameters
paired with multiple sort_attr query parameters. For example, `?sort=asc&sort_attr=name&sort=desc&sort_attr=created_at`
sorts the results by name in ascending order and by created_at in descending order. The sort_attr query parameter
values are case-sensitive.

As mentioned in the heaobject documentation, a folder with id "root" denotes the root of a volume or volume-like
object, like an AWS S3 bucket. It is a view of the volume-like object. The root must never be returned by any folder
endpoint. However, there may be requests for the root folder's items or requests for a form template to create or
update objects within the root folder. In the former case, the folder's items can be manipulated by an endpoint. In the
latter case, when getting the form template, return the volume-like object and use the volume-like object's attributes
to populate the form template.

HEA microservices use the standard Python logging module for logging with a custom logger class, ScrubbingLogger, that
scrubs sensitive HEAObject attributes from log messages when they're passed as arguments or in a list or tuple that's
passed as an argument. When passing an HEAObject into a log message, always use the logging module's built-in string
formatting (not f-strings nor string concatenation nor str.format()) and pass the object directly or in a list or
tuple, or scrubbing might not occur.
"""
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
