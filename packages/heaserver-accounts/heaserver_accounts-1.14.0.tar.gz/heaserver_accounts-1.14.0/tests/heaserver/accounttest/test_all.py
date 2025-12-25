from .testcase import AWSAccountTestCase
from heaserver.service.testcase.mixin import GetAllMixin, GetOneMixin
from heaserver.service.representor import nvpjson
from heaobject.account import AWSAccount
from heaobject.user import AWS_USER, NONE_USER
from heaobject.source import AWS
from heaobject.root import Share, ShareImpl, Permission
from aiohttp import hdrs


# class TestDeleteAccount(AWSAccountTestCase, DeleteMixin):
#     pass
#
#
class TestGetAccounts(AWSAccountTestCase, GetAllMixin):
    pass


class TestGetAccount(AWSAccountTestCase, GetOneMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._expected_one = [
            {
                "collection": {
                    "href": "http://localhost:8080/awsaccounts/123456789012",
                    "items": [
                            {
                                "data": [
                                    {"display": "False",
                                     "name": "id",
                                     "prompt": "id",
                                     "value": "123456789012"},
                                    {"display": "True",
                                     "index": "0",
                                     "name": "basis",
                                     "prompt": "basis",
                                     "section": "shares",
                                     "value": "USER"},
                                    {"display": "True",
                                     "index": "0",
                                     "name": "basis",
                                     "prompt": "basis",
                                     "section": "user_shares",
                                     "value": "USER"},
                                    {
                                        "display": "True",
                                        "index": "0",
                                        "name": "group",
                                        "prompt": "group",
                                        "section": "shares",
                                        "value": "system|none"
                                    },
                                    {
                                        "display": "True",
                                        "index": "0",
                                        "name": "group",
                                        "prompt": "group",
                                        "section": "user_shares",
                                        "value": "system|none"
                                    },
                                    {
                                        "display": "True",
                                        "index": "0",
                                        "name": "invite",
                                        "prompt": "invite",
                                        "section": "shares",
                                        "value": "None"
                                    },
                                    {
                                        "display": "True",
                                        "index": "0",
                                        "name": "invite",
                                        "prompt": "invite",
                                        "section": "user_shares",
                                        "value": "None"
                                    },
                                    {
                                        "display": "True",
                                        "index": "0",
                                        "name": "permissions",
                                        "prompt": "permissions",
                                        "section": "shares",
                                        "value": ["VIEWER"]
                                    },
                                    {
                                        "display": "True",
                                        "index": "0",
                                        "name": "permissions",
                                        "prompt": "permissions",
                                        "section": "user_shares",
                                        "value": ["VIEWER"]
                                    },
                                    {
                                        "display": "True",
                                        "index": "0",
                                        "name": "type",
                                        "prompt": "type",
                                        "section": "shares",
                                        "value": "heaobject.root.ShareImpl"
                                    },
                                    {
                                        "display": "True",
                                        "index": "0",
                                        "name": "type",
                                        "prompt": "type",
                                        "section": "user_shares",
                                        "value": "heaobject.root.ShareImpl"
                                    },
                                    {
                                        "display": "True",
                                        "index": "0",
                                        "name": "type_display_name",
                                        "prompt": "type_display_name",
                                        "section": "shares",
                                        "value": "Share"
                                    },
                                    {
                                        "display": "True",
                                        "index": "0",
                                        "name": "type_display_name",
                                        "prompt": "type_display_name",
                                        "section": "user_shares",
                                        "value": "Share"
                                    },
                                    {
                                        "display": "True",
                                        "index": "0",
                                        "name": "user",
                                        "prompt": "user",
                                        "section": "shares",
                                        "value": "system|none"
                                    },
                                    {
                                        "display": "True",
                                        "index": "0",
                                        "name": "user",
                                        "prompt": "user",
                                        "section": "user_shares",
                                        "value": "system|none"
                                    },
                                    {
                                        "display": "True",
                                        "name": "alternate_contact_name",
                                        "prompt": "alternate_contact_name",
                                        "value": "None"
                                    },
                                    {
                                        "display": "True",
                                        "name": "alternate_email_address",
                                        "prompt": "alternate_email_address",
                                        "value": "None"
                                    },
                                    {
                                        "display": "True",
                                        "name": "alternate_phone_number",
                                        "prompt": "alternate_phone_number",
                                        "value": "None"
                                    },
                                    {
                                        "display": "True",
                                        "name": "collaborators",
                                        "prompt": "collaborators",
                                        "value": []
                                    },
                                    {
                                        "display": "True",
                                        "name": "created",
                                        "prompt": "created",
                                        "value": "None"
                                    },
                                    {
                                        "display": "True",
                                        "name": "credential_type_name",
                                        "prompt": "credential_type_name",
                                        "value": "heaobject.keychain.AWSCredentials"
                                    },
                                    {
                                        "display": "True",
                                        "name": "derived_by",
                                        "prompt": "derived_by",
                                        "value": "None"
                                    },
                                    {
                                        "display": "True",
                                        "name": "derived_from",
                                        "prompt": "derived_from",
                                        "value": []
                                    },
                                    {
                                        "display": "True",
                                        "name": "description",
                                        "prompt": "description",
                                        "value": "None"
                                    },
                                    {
                                        "display": "True",
                                        "name": "display_name",
                                        "prompt": "display_name",
                                        "value": "123456789012"
                                    },
                                    {
                                        "display": "True",
                                        "name": "dynamic_permission_supported",
                                        "prompt": "dynamic_permission_supported",
                                        "value": "False"
                                    },
                                    {
                                        "display": "True",
                                        "name": "email_address",
                                        "prompt": "email_address",
                                        "value": "master@example.com"
                                    },
                                    {
                                        "display": "True",
                                        "name": "file_system_name",
                                        "prompt": "file_system_name",
                                        "value": "DEFAULT_FILE_SYSTEM"
                                    },
                                    {
                                        "display": "True",
                                        "name": "file_system_type",
                                        "prompt": "file_system_type",
                                        "value": "heaobject.volume.AWSFileSystem"
                                    },
                                    {
                                        "display": "True",
                                        "name": "full_name",
                                        "prompt": "full_name",
                                        "value": "None"
                                    },
                                    {
                                        "display": "True",
                                        "name": "group_shares",
                                        "prompt": "group_shares",
                                        "value": []
                                    },
                                    {
                                        "display": "True",
                                        "name": "instance_id",
                                        "prompt": "instance_id",
                                        "value": "heaobject.account.AWSAccount^123456789012"
                                    },
                                    {
                                        "display": "True",
                                        "name": "invites",
                                        "prompt": "invites",
                                        "value": []
                                    },
                                    {
                                        "display": "True",
                                        "name": "mime_type",
                                        "prompt": "mime_type",
                                        "value": "application/x.awsaccount"
                                    },
                                    {
                                        "display": "True",
                                        "name": "modified",
                                        "prompt": "modified",
                                        "value": "None"
                                    },
                                    {
                                        "display": "True",
                                        "name": "name",
                                        "prompt": "name",
                                        "value": "master"
                                    },
                                    {
                                        "display": "True",
                                        "name": "owner",
                                        "prompt": "owner",
                                        "value": "system|aws"
                                    },
                                    {
                                        "display": "True",
                                        "name": "phone_number",
                                        "prompt": "phone_number",
                                        "value": "None"
                                    },
                                    {
                                        "display": "True",
                                        "name": "resource_type_and_id",
                                        "prompt": "resource_type_and_id",
                                        "value": "",
                                    },
                                    {
                                        "display": "True",
                                        "name": "source",
                                        "prompt": "source",
                                        "value": "Amazon Web Services"
                                    },
                                    {
                                        "display": "True",
                                        "name": "source_detail",
                                        "prompt": "source_detail",
                                        "value": "Amazon Web Services"
                                    },
                                    {
                                        "display": "True",
                                        "name": "super_admin_default_permissions",
                                        "prompt": "super_admin_default_permissions",
                                        "value": []
                                    },
                                    {
                                        "display": "True",
                                        "name": "type",
                                        "prompt": "type",
                                        "value": "heaobject.account.AWSAccount"
                                    },
                                    {
                                        "display": "True",
                                        "name": "type_display_name",
                                        "prompt": "type_display_name",
                                        "value": "AWS Account"
                                    },
                                ],
                                "links": [
                                    {
                                        "href": "http://localhost:8080/awsaccounts/123456789012",
                                        "prompt": "View account",
                                        "rel": "hea-account hea-self-container self"
                                    },
                                    {
                                        "href": "http://localhost:8080/awsaccounts/123456789012/creator",
                                        "prompt": "New",
                                        "rel": "hea-context-menu hea-creator-choices",
                                    },
                                    {
                                        "href": "http://localhost:8080/awsaccounts/123456789012/opener",
                                        "prompt": "Open",
                                        "rel": "hea-context-menu hea-opener-choices",
                                    },
                                    {
                                        "href": "http://localhost:8080/awsaccounts/123456789012/search",
                                        "prompt": "View searchitem",
                                        "rel": "hea-search"
                                    },
                                    {
                                        "href": "http://localhost:8080/volumes/666f6f2d6261722d71757578",
                                        "prompt": "View volume",
                                        "rel": "hea-volume"
                                    },
                                    {
                                        "href": "http://localhost:8080/volumes/666f6f2d6261722d71757578/awss3trash",
                                        "prompt": "Trash",
                                        "rel": "hea-context-menu hea-trash"
                                    },
                                ]
                            },
                        ],
                    "permissions": [["VIEWER"]],
                    "template": {
                                "data": [{"cardinality": "multiple",
                                          "index": "-1",
                                         "name": "collaborator_ids",
                                         "options": {
                                            "href": "http://localhost:8080/people/?excludesystem=yes",
                                            "text": "display_name",
                                            "value": "id",
                                         },
                                        "pattern": "None",
                                        "prompt": "Collaborators",
                                        "readOnly": "True",
                                        "required": "True",
                                        "section": "collaborators",
                                        "type": "select",
                                        "value": "None",
                                    },
                                    {"display": "False",
                                        "name": "id",
                                        "pattern": "None",
                                        "prompt": "Id",
                                        "readOnly": "True",
                                        "required": "False",
                                        "value": "123456789012"
                                    },
                                   {"display": "False",
                                        "name": "instance_id",
                                        "pattern": "None",
                                        "prompt": "Instance id",
                                        "readOnly": "True",
                                        "required": "False",
                                        "value": "heaobject.account.AWSAccount^123456789012"
                                    },
                                    {"display": "False",
                                        "name": "type",
                                        "pattern": "None",
                                        "prompt": "type",
                                        "readOnly": "True",
                                        "required": "True",
                                        "value": "heaobject.account.AWSAccount"
                                    },
                                    {"index": "-1",
                                        "name": "bucket_id",
                                        "options": {
                                            "href": "http://localhost:8080/volumes/666f6f2d6261722d71757578/bucketitems/",
                                            "text": "display_name",
                                            "value": "id"
                                        },
                                        "pattern": "None",
                                        "prompt": "Bucket",
                                        "readOnly": "True",
                                        "required": "True",
                                        "section": "collaborators",
                                        "sectionPrompt": "Collaborators",
                                        "type": "select",
                                        "value": "None"
                                    },
                                    {
                                        "display": "False",
                                        "index": "-1",
                                        "name": "type",
                                        "pattern": "None",
                                        "prompt": "type",
                                        "readOnly": "True",
                                        "required": "True",
                                        "section": "collaborators",
                                        "value": "heaobject.account.AWSAccountCollaborators"
                                    },
                                    {
                                        "display": "False",
                                        "index": "-1",
                                        "name": "type_display_name",
                                        "pattern": "None",
                                        "prompt": "type_display_name",
                                        "readOnly": "True",
                                        "required": "True",
                                        "section": "collaborators",
                                        "value": "None"
                                    },
                                    {"name": "alternate_contact_name",
                                        "pattern": "None",
                                        "prompt": "Alternate Contact Name",
                                        "readOnly": "True",
                                        "required": "False",
                                        "value": "None"
                                    },
                                    {"name": "alternate_email_address",
                                        "pattern": "None",
                                        "prompt": "Alternate Email Address",
                                        "readOnly": "True",
                                        "required": "False",
                                        "type": "email",
                                        "value": "None"
                                    },
                                    {"name": "alternate_phone_number",
                                        "pattern": "None",
                                        "prompt": "Alternate Phone Number",
                                        "readOnly": "True",
                                        "required": "False",
                                        "type": "tel",
                                        "value": "None"
                                    },
                                    {"name": "created",
                                        "pattern": "None",
                                        "prompt": "Created",
                                        "readOnly": "True",
                                        "required": "False",
                                        "type": "datetime",
                                        "value": "None"
                                    },
                                    {"name": "display_name",
                                        "pattern": "None",
                                        "prompt": "Name",
                                        "readOnly": "True",
                                        "required": "True",
                                        "value": "123456789012"
                                    },
                                    {"name": "email_address",
                                        "pattern": "None",
                                        "prompt": "Email Address",
                                        "readOnly": "True",
                                        "required": "False",
                                        "type": "email",
                                        "value": "master@example.com"
                                    },
                                    {"name": "full_name",
                                        "pattern": "None",
                                        "prompt": "Full Name",
                                        "readOnly": "True",
                                        "required": "False",
                                        "value": "None"
                                    },
                                    {"name": "modified",
                                        "pattern": "None",
                                        "prompt": "Modified",
                                        "readOnly": "True",
                                        "required": "False",
                                        "type": "datetime",
                                        "value": "None",
                                    },
                                    {"name": "owner",
                                        "options": {
                                            "href": "http://localhost:8080/people/",
                                            "text": "display_name",
                                            "value": "id"
                                        },
                                        "pattern": "None",
                                        "prompt": "Owner",
                                        "readOnly": "True",
                                        "required": "True",
                                        "type": "select",
                                        "value": "system|aws"
                                    },
                                    {"name": "phone_number",
                                        "pattern": "None",
                                        "prompt": "Phone Number",
                                        "readOnly": "True",
                                        "required": "False",
                                        "type": "tel",
                                        "value": "None"
                                    },
                                    {"name": "source",
                                        "pattern": "None",
                                        "prompt": "Source",
                                        "readOnly": "True",
                                        "required": "False",
                                        "value": "Amazon Web Services"
                                    },
                                    {"name": "type_display_name",
                                        "pattern": "None",
                                        "prompt": "Type",
                                        "readOnly": "True",
                                        "required": "True",
                                        "value": "AWS Account"
                                    }
                                ],
                                "prompt": "Properties",
                                "rel": "hea-context-menu hea-properties"
                            },
                            "version": "1.0"
                    }
            }
        ]

    def setUp(self):
        account_id = '123456789012'
        self.account: AWSAccount = AWSAccount()
        self.account.id = account_id
        self.account.name = 'master'
        self.account.display_name = account_id
        self.account.email_address = 'master@example.com'
        self.account.owner = AWS_USER
        self.account.source = AWS
        self.account.source_detail = AWS
        share: Share = ShareImpl()
        share.permissions = [Permission.VIEWER]
        share.user = NONE_USER
        self.account.add_user_share(share)

    async def test_get_account_me_status(self):
        async with self.client.request('GET', '/volumes/666f6f2d6261722d71757578/awsaccounts/me') as resp:
            self.assertEqual(200, resp.status)

    async def test_get_account_me(self):
        url = '/volumes/666f6f2d6261722d71757578/awsaccounts/me'
        async with self.client.request('GET', url, headers={hdrs.ACCEPT: nvpjson.MIME_TYPE}) as resp:
            self.assertEqual([self.account.to_dict()], await resp.json())

    # async def test_get_new_bucket_form(self):
    #     url = '/volumes/666f6f2d6261722d71757578/awsaccounts/me/newbucket/'
    #     expected = [{'collection': {'version': '1.0',
    #                                 'permissions': [['VIEWER']],
    #                                 'items': [{'data': [{'name': 'alternate_contact_name', 'value': None, 'prompt': 'alternate_contact_name', 'display': True},
    #                                                     {'name': 'alternate_email_address', 'value': None, 'prompt': 'alternate_email_address', 'display': True},
    #                                                     {'name': 'alternate_phone_number', 'value': None, 'prompt': 'alternate_phone_number', 'display': True},
    #                                                     {'name': 'created', 'value': None, 'prompt': 'created', 'display': True},
    #                                                     {'name': 'derived_by', 'value': None, 'prompt': 'derived_by', 'display': True},
    #                                                     {'name': 'derived_from', 'value': [], 'prompt': 'derived_from', 'display': True},
    #                                                     {'name': 'description', 'value': None, 'prompt': 'description', 'display': True},
    #                                                     {'name': 'display_name', 'value': '123456789012', 'prompt': 'display_name', 'display': True},
    #                                                     {'name': 'email_address', 'value': 'master@example.com', 'prompt': 'email_address', 'display': True},
    #                                                     {'name': 'full_name', 'value': None, 'prompt': 'full_name', 'display': True},
    #                                                     {'name': 'id', 'value': '123456789012', 'prompt': 'id', 'display': False},
    #                                                     {'name': 'instance_id', 'value': 'heaobject.account.AWSAccount^123456789012', 'prompt': 'instance_id', 'display': True},
    #                                                     {'name': 'invites', 'value': [], 'prompt': 'invites', 'display': True},
    #                                                     {'name': 'mime_type', 'value': 'application/x.awsaccount', 'prompt': 'mime_type', 'display': True},
    #                                                     {'name': 'modified', 'value': None, 'prompt': 'modified', 'display': True},
    #                                                     {'name': 'name', 'value': 'master', 'prompt': 'name', 'display': True},
    #                                                     {'name': 'owner', 'value': 'system|aws', 'prompt': 'owner', 'display': True},
    #                                                     {'name': 'phone_number', 'value': None, 'prompt': 'phone_number', 'display': True},
    #                                                     {'name': 'shares', 'value': [], 'prompt': 'shares', 'display': True},
    #                                                     {'name': 'user_shares', 'value': [], 'prompt': 'user_shares', 'display': True},
    #                                                     {'name': 'group_shares', 'value': [], 'prompt': 'group_shares', 'display': True},
    #                                                     {'name': 'source', 'value': 'Amazon Web Services', 'prompt': 'source', 'display': True},
    #                                                     {'name': 'source_detail', 'value': 'Amazon Web Services', 'prompt': 'source_detail', 'display': True},
    #                                                     {'name': 'resource_type_and_id', 'value': '', 'prompt': 'resource_type_and_id', 'display': True},
    #                                                     {'name': 'type', 'value': 'heaobject.account.AWSAccount', 'prompt': 'type', 'display': True},
    #                                                     {'name': 'type_display_name', 'value': 'AWS Account', 'prompt': 'type_display_name', 'display': True},
    #                                                     {'name': 'file_system_type', 'value': 'heaobject.volume.AWSFileSystem', 'prompt': 'file_system_type', 'display': True},
    #                                                     {'name': 'file_system_name', 'value': 'DEFAULT_FILE_SYSTEM', 'prompt': 'file_system_name', 'display': True},
    #                                                     {'name': 'credential_type_name', 'value': 'heaobject.keychain.AWSCredentials', 'prompt': 'credential_type_name', 'display': True},
    #                                                     {'name': 'super_admin_default_permissions', 'value': [], 'prompt': 'super_admin_default_permissions', 'display': True},
    #                                                     {'name': 'dynamic_permission_supported', 'value': False, 'prompt': 'dynamic_permission_supported', 'display': True}
    #                                                     ],
    #                                            'links': []}],
    #                                 'template': {'prompt': 'New Folder', 'rel': '',
    #                                              'data': [{'name': 'display_name', 'value': None, 'prompt': 'Name', 'required': True, 'readOnly': True, 'pattern': '^(cb-[a-z][a-z0-9\\.\\-]{0,})$'},
    #                                                       {'name': 'type', 'value': 'heaobject.bucket.AWSBucket', 'prompt': 'Type', 'required': True, 'readOnly': True, 'pattern': None, 'display': False},
    #                                                       {'name': 'region', 'value': None, 'prompt': 'Region', 'required': True, 'readOnly': False, 'pattern': None, 'type': 'select',
    #                                                        'options': [{'value': 'us-east-2', 'text': 'US East (Ohio)'}, {'value': 'us-east-1', 'text': 'US East (N. Virginia)'}, {'value': 'us-west-1', 'text': 'US West (N. California)'}, {'value': 'us-west-2', 'text': 'US West (Oregon)'}, {'value': 'af-south-1', 'text': 'Africa (Cape Town)'}, {'value': 'ap-east-1', 'text': 'Asia Pacific (Hong Kong)'}, {'value': 'ap-southeast-3', 'text': 'Asia Pacific (Jakarta)'}, {'value': 'ap-south-1', 'text': 'Asia Pacific (Mumbai)'}, {'value': 'ap-northeast-3', 'text': 'Asia Pacific (Osaka)'}, {'value': 'ap-northeast-2', 'text': 'Asia Pacific (Seoul)'}, {'value': 'ap-southeast-1', 'text': 'Asia Pacific (Singapore)'}, {'value': 'ap-southeast-2', 'text': 'Asia Pacific (Sydney)'}, {'value': 'ap-northeast-1', 'text': 'Asia Pacific (Tokyo)'}, {'value': 'ca-central-1', 'text': 'Canada (Central)'}, {'value': 'eu-central-1', 'text': 'Europe (Frankfurt)'}, {'value': 'eu-west-1', 'text': 'Europe (Ireland)'}, {'value': 'eu-west-2', 'text': 'Europe (London)'}, {'value': 'eu-south-1', 'text': 'Europe (Milan)'}, {'value': 'eu-west-3', 'text': 'Europe (Paris)'}, {'value': 'eu-north-1', 'text': 'Europe (Stockholm)'}, {'value': 'me-south-1', 'text': 'Middle East (Bahrain)'}, {'value': 'sa-east-1', 'text': 'South America (São Paulo)'}],
    #                                                        "value": "us-east-1"},
    #                                                       {'name': 'versioned', 'options': [{'text': 'True', 'value': 'true'}, {'text': 'False', 'value': 'false'}], 'pattern': None, 'prompt': 'Versioned', 'readOnly': False, 'required': True, 'type': 'select', 'value': 'true'},
    #                                                       {'name': 'instructions1', 'pattern': None, 'prompt': 'instructions1', 'readOnly': False, 'required': False, 'type': 'text-display', 'value': 'All bucket names must begin with "cb" followed by the first initial and beginning four characters of the owner\'s last name.'},
    #                                                       {'name': 'instructions2', 'pattern': None, 'prompt': 'instructions2', 'readOnly': False, 'required': False, 'type': 'text-display', 'value': 'For more information, see <a href="https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html" target="_blank">Bucket Naming Rules</a>.'}
    #                                                       ]}}}]

    #     async with self.client.request('GET', url) as resp:
    #         actual = await resp.json()
    #         del actual[0]['collection']['href']  # The href's port will change every time.
    #         self._assert_equal_ordered(expected, actual)

#
#
# class TestPutAccount(AWSAccountTestCase, PutMixin):
#     pass
#
#
# class TestPostAccount(AWSAccountTestCase, PostMixin):
#     pass
