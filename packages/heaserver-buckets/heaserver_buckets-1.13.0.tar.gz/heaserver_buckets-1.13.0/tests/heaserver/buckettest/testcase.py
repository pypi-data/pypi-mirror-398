"""
Creates a test case class for use with the unittest library that is built into Python.
"""
from heaserver.service.testcase import expectedvalues
from heaserver.service.testcase.microservicetestcase import get_test_case_cls_default
from heaserver.bucket import service
from heaserver.service.testcase.mockaws import MockS3WithMockMongoManager
from heaobject.user import NONE_USER, AWS_USER
from heaserver.service.testcase.expectedvalues import Action

db_store = {
    service.MONGODB_BUCKET_COLLECTION: [{
        'id': 'hci-foundation-1',
        'instance_id': 'heaobject.bucket.AWSBucket^hci-foundation-1',
        'created': '2022-05-17T00:00:00+00:00',
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'object_count': None,
        'size': None,
        'display_name': 'hci-foundation-1',
        'invites': [],
        'modified': None,
        'name': 'hci-foundation-1',
        'owner': AWS_USER,
        'shares': [{
            'invite': None,
            'permissions': ['COOWNER'],
            'type': 'heaobject.root.ShareImpl',
            'user': 'system|none',
            'type_display_name': 'Share',
            'basis': 'USER',
            'group': 'system|none'
        }],
        'user_shares': [{
            'invite': None,
            'permissions': ['COOWNER'],
            'type': 'heaobject.root.ShareImpl',
            'user': 'system|none',
            'type_display_name': 'Share',
            'basis': 'USER',
            'group': 'system|none'
        }],
        'group_shares': [],
        'source': 'AWS S3',
        'source_detail': 'AWS S3',
        'type': 'heaobject.bucket.AWSBucket',
        'arn': 'arn:aws:s3::hci-foundation-1',
        'versioned': True,
        'encrypted': False,
        'region': 'us-west-1',
        'tags': [],
        's3_uri': 's3://hci-foundation-1/',
        'locked': False,
        'mime_type': 'application/x.awsbucket',
        'bucket_id': 'hci-foundation-1',
        'type_display_name': 'AWS S3 Bucket',
        'collaborator_ids': [],
        'resource_type_and_id': 'hci-foundation-1',
        'dynamic_permission_supported': False,
        'super_admin_default_permissions': []
    },
        {
            'id': 'hci-foundation-2',
            'instance_id': 'heaobject.bucket.AWSBucket^hci-foundation-2',
            'created': '2022-05-17T00:00:00+00:00',
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'object_count': None,
            'size': None,
            'display_name': 'hci-foundation-2',
            'invites': [],
            'modified': None,
            'name': 'hci-foundation-2',
            'owner': AWS_USER,
            'shares': [{
                'invite': None,
                'permissions': ['COOWNER'],
                'type': 'heaobject.root.ShareImpl',
                'user': 'system|none',
                'type_display_name': 'Share',
                'basis': 'USER',
                'group': 'system|none'
            }],
            'user_shares': [{
                'invite': None,
                'permissions': ['COOWNER'],
                'type': 'heaobject.root.ShareImpl',
                'user': 'system|none',
                'type_display_name': 'Share',
                'basis': 'USER',
                'group': 'system|none'
            }],
            'group_shares': [],
            'source': 'AWS S3',
            'source_detail': 'AWS S3',
            'type': 'heaobject.bucket.AWSBucket',
            'arn': 'arn:aws:s3::hci-foundation-2',
            'versioned': True,
            'encrypted': False,
            'region': 'us-west-1',
            'tags': [],
            's3_uri': 's3://hci-foundation-2/',
            'locked': False,
            'mime_type': 'application/x.awsbucket',
            'bucket_id': 'hci-foundation-2',
            'type_display_name': 'AWS S3 Bucket',
            'collaborator_ids': [],
            'resource_type_and_id': 'hci-foundation-2',
            'dynamic_permission_supported': False,
            'super_admin_default_permissions': []
        }

    ],
    'filesystems': [{
        'id': '666f6f2d6261722d71757578',
        'created': None,
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'Amazon Web Services',
        'invited': [],
        'modified': None,
        'name': 'amazon_web_services',
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
        'file_system_name': 'amazon_web_services',
        'credential_id': None  # Let boto3 try to find the user's credentials.
    }]}


def get_test_case_cls(*args, **kwargs):
    """Get a test case class specifically for this microservice."""

    class MyTestCase(get_test_case_cls_default(*args, **kwargs)):
        def __init__(self, *args_, **kwargs_):
            super().__init__(*args_, **kwargs_)
            if self._body_post:
                modified_data = {**db_store[self._coll][0], 'name': 'tritimus', 'display_name': 'tritimus',
                                 's3_uri': 's3://tritimus/', 'bucket_id': 'tritimus', 'versioned': False,
                                 'arn': 'arn:aws:s3::tritimus', 'instance_id': 'heaobject.bucket.AWSBucket^tritimus',
                                 'resource_type_and_id': 'tritimus'}
                if 'id' in modified_data:
                    del modified_data['id']
                self._body_post = expectedvalues._create_template(modified_data)

    return MyTestCase


TestCase = \
    get_test_case_cls(coll=service.MONGODB_BUCKET_COLLECTION,
                      wstl_package=service.__package__,
                      href='http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/',
                      fixtures=db_store,
                      db_manager_cls=MockS3WithMockMongoManager,
                      get_actions=[Action(name='heaserver-buckets-bucket-get-properties',
                                          rel=['hea-properties', 'hea-context-menu']),
                                   Action(name='heaserver-buckets-bucket-get-open-choices',
                                          url='http://localhost:8080/volumes/{volume_id}/buckets/{id}/opener',
                                          rel=['hea-opener-choices', 'hea-context-menu', 'hea-downloader']),
                                   Action(name='heaserver-buckets-bucket-get-self',
                                          url='http://localhost:8080/volumes/{volume_id}/buckets/{id}',
                                          rel=['self', 'hea-self-container']),
                                   Action(name='heaserver-buckets-bucket-get-volume',
                                          url='http://localhost:8080/volumes/{volume_id}',
                                          rel=['hea-volume']),
                                   Action(name='heaserver-buckets-bucket-get-awsaccount',
                                          url='http://localhost:8080/volumes/{volume_id}/awsaccounts/me',
                                          rel=['hea-account']),
                                   Action(name='heaserver-buckets-bucket-get-create-choices',
                                          url='http://localhost:8080/volumes/{volume_id}/buckets/{id}/creator',
                                          rel=['hea-creator-choices', 'hea-context-menu']),
                                   Action(name='heaserver-buckets-bucket-get-uploader',
                                       url='http://localhost:8080/volumes/{volume_id}/buckets/{id}/awss3folders/root/uploader',
                                       rel=['hea-uploader']),
                                   Action(name='heaserver-buckets-bucket-get-trash',
                                          url='http://localhost:8080/volumes/{volume_id}/awss3trash',
                                          rel=['hea-trash', 'hea-context-menu']),
                                   Action(
                                            name='heaserver-buckets-bucket-get-delete-preflight-url',
                                            rel=['hea-delete-preflight'],
                                            url='http://localhost:8080/preflights/buckets/delete')
                                   ],
                      get_all_actions=[Action(name='heaserver-buckets-bucket-get-properties',
                                              rel=['hea-properties', 'hea-context-menu']),
                                       Action(name='heaserver-buckets-bucket-get-open-choices',
                                              url='http://localhost:8080/volumes/{volume_id}/buckets/{id}/opener',
                                              rel=['hea-opener-choices', 'hea-context-menu', 'hea-downloader']),
                                       Action(name='heaserver-buckets-bucket-get-self',
                                              url='http://localhost:8080/volumes/{volume_id}/buckets/{id}',
                                              rel=['self', 'hea-self-container']),
                                       Action(name='heaserver-buckets-bucket-get-create-choices',
                                              url='http://localhost:8080/volumes/{volume_id}/buckets/{id}/creator',
                                              rel=['hea-creator-choices', 'hea-context-menu']),
                                       Action(
                                           name='heaserver-buckets-bucket-get-uploader',
                                           url='http://localhost:8080/volumes/{volume_id}/buckets/{id}/awss3folders/root/uploader',
                                           rel=['hea-uploader']
                                       ),
                                       Action(name='heaserver-buckets-bucket-get-trash',
                                              url='http://localhost:8080/volumes/666f6f2d6261722d71757578/awss3trash',
                                              wstl_url='http://localhost:8080/volumes/{volume_id}/awss3trash',
                                              rel=['hea-trash', 'hea-context-menu']),
                                       Action(
                                            name='heaserver-buckets-bucket-get-delete-preflight-url',
                                            rel=['hea-delete-preflight'],
                                            url='http://localhost:8080/preflights/buckets/delete')
                                       ],
                      duplicate_action_name=None,
                      exclude=['body_put'])
