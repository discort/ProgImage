import datetime
from io import BytesIO
import uuid

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import web
import motor.motor_asyncio
from PIL import Image

from api import routers, base64_encode


def create_test_image():
    file = BytesIO()
    image = Image.new('RGBA', size=(50, 50), color=(155, 0, 0))
    image.save(file, 'png')
    file.name = 'test.png'
    file.seek(0)
    return file


class BaseAPITestCase(AioHTTPTestCase):
    db_name = 'testdb'
    host = 'mongodb://mongodb:27017'

    async def get_application(self):
        async def cleanup(app):
            client = motor.motor_asyncio.AsyncIOMotorClient(host=self.host, io_loop=app.loop)
            client.drop_database(self.db_name)

        async def setup(app):
            client = motor.motor_asyncio.AsyncIOMotorClient(host=self.host, io_loop=app.loop)
            app['db'] = client[self.db_name]

        app = web.Application()
        app.add_routes(routers)
        app.on_cleanup.append(cleanup)
        app.on_startup.append(setup)
        return app


class TestImageUploading(BaseAPITestCase):
    @unittest_run_loop
    async def test_error_upload(self):
        headers = {'Content-Type': 'image/jpeg'}
        resp = await self.client.request('POST', '/images', headers=headers)
        assert resp.status == 200
        data = await resp.json()
        self.assertDictEqual(data, {'success': False, 'message': 'Image not found', 'data': []})

    @unittest_run_loop
    async def test_upload_image(self):
        headers = {'Content-Type': 'image/jpeg'}
        data = b'123'
        resp = await self.client.request('POST', '/images', headers=headers, data=data)
        assert resp.status == 200
        data = await resp.json()
        assert 'id' in data['data']


class TestImageDownloading(BaseAPITestCase):
    def setUp(self):
        super(TestImageDownloading, self).setUp()
        self.image_data = {
            'id': str(uuid.uuid4()),
            'data': base64_encode(b'test'),
            'format': 'JPEG',
            'host': '127.0.0.1',
            'size': 4,
            'content_type': 'image/jpeg',
            'upload_time': datetime.datetime.utcnow().isoformat()
        }

    async def _add_image(self, data=None, real_image=False):
        if not data:
            data = self.image_data

        if real_image:
            data['data'] = base64_encode(create_test_image().read())
            data['size'] = len(data['data'])

        client = motor.motor_asyncio.AsyncIOMotorClient(host=self.host)
        db = client[self.db_name]
        await db.images.insert_one(data)

    @unittest_run_loop
    async def test_get_image(self):
        await self._add_image()
        resp = await self.client.request('GET', '/images/{}'.format(self.image_data['id']))
        assert resp.status == 200
        data = await resp.json()
        assert self.image_data['id'] == data['data']['id']

    @unittest_run_loop
    async def test_image_not_found(self):
        resp = await self.client.request('GET', '/images/fake_uuid')
        assert resp.status == 200
        data = await resp.json()
        self.assertDictEqual(data, {'success': False, 'message': 'Image not found', 'data': []})

    @unittest_run_loop
    async def test_format_conversion(self):
        await self._add_image(real_image=True)
        resp = await self.client.request('GET', '/images/{}?type=gif'.format(self.image_data['id']))
        assert resp.status == 200
        data = await resp.json()
        assert 'gif' in data['data']['content_type']
