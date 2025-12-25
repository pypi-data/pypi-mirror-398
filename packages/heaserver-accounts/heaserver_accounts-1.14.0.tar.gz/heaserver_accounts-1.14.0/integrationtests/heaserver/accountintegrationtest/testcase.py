"""
Creates a test case class for use with the unittest library that is built into Python.
"""
from heaserver.service.testcase.collection import CollectionKey
from heaserver.service.testcase.dockermongo import MockDockerMongoManager
from heaserver.service.testcase.mockaws import MockS3Manager
from heaserver.service.sources import AWS
from heaobject.user import NONE_USER, AWS_USER


db_store = {
    CollectionKey(name='filesystems', db_manager_cls=MockDockerMongoManager): [{
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
        'source': None,
        'type': 'heaobject.volume.AWSFileSystem',
        'version': None
    }],
    CollectionKey(name='volumes', db_manager_cls=MockDockerMongoManager): [{
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
        'source': None,
        'type': 'heaobject.volume.Volume',
        'version': None,
        'file_system_name': 'DEFAULT_FILE_SYSTEM',
        'file_system_type': 'heaobject.volume.AWSFileSystem'  # Let boto3 try to find the user's credentials.
    }],
    CollectionKey(name='awsaccounts', db_manager_cls=MockS3Manager): [
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
            "owner": AWS_USER,
            "phone_number": None,
            "shares": [{
                "invite": None,
                "permissions": ["VIEWER"],
                "type": "heaobject.root.ShareImpl",
                "type_display_name": "Share",
                "user": "system|none"
            }],
            "source": AWS,
            "source_detail": AWS,
            "type": "heaobject.account.AWSAccount",
            "type_display_name": "AWS Account",
            "file_system_type": "heaobject.volume.AWSFileSystem",
            "file_system_name": "DEFAULT_FILE_SYSTEM",
            "credential_type_name": "heaobject.keychain.AWSCredentials"
        }
    ]
}
