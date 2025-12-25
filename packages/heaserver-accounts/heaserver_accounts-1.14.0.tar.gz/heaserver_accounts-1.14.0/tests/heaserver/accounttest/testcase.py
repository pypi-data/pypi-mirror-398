"""
Creates a test case class for use with the unittest library that is built into Python.
"""

from heaserver.account import service
from heaobject.user import NONE_USER
from heaobject.account import AWSAccount
from heaserver.service.testcase import microservicetestcase, expectedvalues
from heaserver.service.testcase.mockaws import MockS3WithMockMongoManager
from heaserver.service.sources import AWS

db_store = {
    'filesystems': [{
        'id': '666f6f2d6261722d71757578',
        'created': None,
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'Amazon Web Services',
        'invited': [],
        'modified': None,
        'name': 'DEFAULT_FILE_SYSTEM',
        'owner': NONE_USER,
        'shares': [],
        'user_shares': [],
        'group_shares': [],
        'source': None,
        'type': 'heaobject.volume.AWSFileSystem',
        'version': None
    }],
    'volumes': [{
        'id': '666f6f2d6261722d71757578',
        'created': None,
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'My Amazon Web Services',
        'invited': [],
        'modified': None,
        'name': 'amazon_web_services',
        'owner': NONE_USER,
        'shares': [],
        'user_shares': [],
        'group_shares': [],
        'source': None,
        'type': 'heaobject.volume.Volume',
        'version': None,
        'file_system_name': 'DEFAULT_FILE_SYSTEM',
        'file_system_type': 'heaobject.volume.AWSFileSystem',
        'credential_id': None,  # Let boto3 try to find the user's credentials.
        'account_id': f'{AWSAccount.get_type_name()}^123456789012'
    }],
    'awsaccounts': [
        {
            "alternate_contact_name": None,
            "alternate_email_address": None,
            "alternate_phone_number": None,
            "created": None,
            "derived_by": None,
            "derived_from": [],
            "description": None,
            "display_name": "123456789012",
            "email_address": 'master@example.com',
            "full_name": None,
            "id": "123456789012",
            "instance_id": "heaobject.account.AWSAccount^123456789012",
            "invites": [],
            "mime_type": "application/x.awsaccount",
            "modified": None,
            "name": "master",
            "owner": "system|aws",
            "phone_number": None,
            "shares": [{'invite': None,'permissions': ['VIEWER'],'type': 'heaobject.root.ShareImpl','type_display_name': 'Share','user': 'system|none', 'group': 'system|none', 'basis': 'USER'}],
            'user_shares': [{'invite': None,'permissions': ['VIEWER'],'type': 'heaobject.root.ShareImpl','type_display_name': 'Share','user': 'system|none', 'group': 'system|none', 'basis': 'USER'}],
            'group_shares': [],
            "source": AWS,
            "source_detail": AWS,
            "type": AWSAccount.get_type_name(),
            "type_display_name": "AWS Account",
            "file_system_type": "heaobject.volume.AWSFileSystem",
            "file_system_name": "DEFAULT_FILE_SYSTEM",
            "credential_type_name": "heaobject.keychain.AWSCredentials",
            "resource_type_and_id": "",
            'super_admin_default_permissions': [],
            'dynamic_permission_supported': False,
            'collaborators': []
        }
    ]}

AWSAccountTestCase = \
    microservicetestcase.get_test_case_cls_default(
        href='http://localhost:8080/awsaccounts/',
        wstl_package=service.__package__,
        coll='awsaccounts',
        fixtures=db_store,
        db_manager_cls=MockS3WithMockMongoManager,
        get_all_actions=[
            expectedvalues.Action(
                name='heaserver-accounts-awsaccount-get-open-choices',
                url='http://localhost:8080/awsaccounts/{id}/opener',
                rel=['hea-context-menu', 'hea-opener-choices']),
            expectedvalues.Action(name='heaserver-accounts-awsaccount-get-self',
                url='http://localhost:8080/awsaccounts/{id}',
                rel=['self', 'hea-account', 'hea-self-container']),
            expectedvalues.Action(name='heaserver-accounts-awsaccount-get-properties',
                   rel=['hea-properties', 'hea-context-menu']),
            expectedvalues.Action(
                name='heaserver-accounts-awsaccount-get-create-choices',
                url='http://localhost:8080/awsaccounts/{id}/creator',
                rel=['hea-creator-choices', 'hea-context-menu']),
            expectedvalues.Action(
                name='heaserver-accounts-awsaccount-get-searchitem',
                url='http://localhost:8080/awsaccounts/{id}/search',
                rel=['hea-search'])
        ],
        get_actions=[
            expectedvalues.Action(
                name='heaserver-accounts-awsaccount-get-open-choices',
                url='http://localhost:8080/awsaccounts/{id}/opener',
                rel=['hea-context-menu', 'hea-opener-choices']),
            expectedvalues.Action(
                name='heaserver-accounts-awsaccount-get-create-choices',
                url='http://localhost:8080/awsaccounts/{id}/creator',
                rel=['hea-creator-choices', 'hea-context-menu']),
            expectedvalues.Action(name='heaserver-accounts-awsaccount-get-self',
                url='http://localhost:8080/awsaccounts/{id}',
                rel=['hea-account', 'self', 'hea-self-container']),
            expectedvalues.Action(name='heaserver-accounts-awsaccount-get-properties',
                   rel=['hea-properties', 'hea-context-menu']),
            expectedvalues.Action(name='heaserver-accounts-awsaccount-get-trash',
                                  rel=['hea-trash', 'hea-context-menu'],
                                  url='http://localhost:8080/volumes/666f6f2d6261722d71757578/awss3trash',
                                  wstl_url='http://localhost:8080/volumes/{volume_id}/awss3trash'),
            expectedvalues.Action(
                name='heaserver-accounts-awsaccount-get-searchitem',
                url='http://localhost:8080/awsaccounts/{id}/search',
                rel=['hea-search']),
            expectedvalues.Action(
                name='heaserver-accounts-awsaccount-get-volume',
                url='http://localhost:8080/volumes/666f6f2d6261722d71757578',
                wstl_url='http://localhost:8080/volumes/{volume_id}',
                rel=['hea-volume'])],
        put_content_status=404,
        duplicate_action_name=None,
        exclude=['body_put', 'body_post']
    )
