from unittest import TestCase
from heaserver.service.uritemplate import tvars


class URITemplateVarsTestCase(TestCase):
    def test_one_variable(self) -> None:
        """
        Checks if the route /organizations/{id}/members correctly captures an id in the given URL when it is
        present.
        """
        self.assertEqual({'id': 'qwertyuiop'},
                         tvars('/organizations/{id}/members', '/organizations/qwertyuiop/members'))

    def test_one_variable_not_present(self) -> None:
        """
        Checks if the route /organizations/{id}/members correctly does not capture an id in the given URL when it is
        not present.
        """
        self.assertEqual({}, tvars('/organizations/{id}/members', '/organizations/'))

    def test_two_variables_both_present(self) -> None:
        """
        Checks if the route /volumes/{volume_id}/organizations/{id} correctly captures a volume id and an id in the
        given URL when both are present.
        """
        self.assertEqual({'volume_id': 'asdfghjkl', 'id': 'qwertyuiop'},
                         tvars('/volumes/{volume_id}/organizations/{id}',
                               '/volumes/asdfghjkl/organizations/qwertyuiop'))

    def test_two_variables_one_present(self) -> None:
        """
        Checks if the route /volumes/{volume_id}/organizations/{id} correctly only captures a volume in the given URL
        when the volume_id is present but the id is not.
        """
        self.assertEqual({'volume_id': 'asdfghjkl'},
                         tvars('/volumes/{volume_id}/organizations/{id}',
                               '/volumes/asdfghjkl/organizations/'))

    def test_no_variables(self) -> None:
        """Checks if the route /foo/bar/spam correctly captures nothing when the URL is identical."""
        self.assertEqual({}, tvars('/foo/bar/spam', '/foo/bar/spam'))

    def test_decoding_spaces(self) -> None:
        """
        Checks if the route /foo/{var}/spam correctly captures a variable and decodes it when necessary.
        """
        self.assertEqual({'var': 'a value with spaces'},
                         tvars('/foo/{var}/spam', '/foo/a%20value%20with%20spaces/spam'))

    def test_decoding_slashes(self) -> None:
        """
        Checks if the route /foo/{var}/spam correctly captures a variable and decodes it when necessary.
        """
        self.assertEqual({'var': 'a/value/with/slashes'},
                         tvars('/foo/{var}/spam', '/foo/a%2Fvalue%2Fwith%2Fslashes/spam'))

    def test_decoding_pipes(self) -> None:
        """
        Checks if the route /foo/{var}/spam correctly captures a variable and decodes it when necessary.
        """
        self.assertEqual({'var': 'a|value|with|pipes'},
                         tvars('/foo/{var}/spam', '/foo/a%7Cvalue%7Cwith%7Cpipes/spam'))
