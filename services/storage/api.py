import base64
from datetime import datetime
from io import BytesIO
import os
import uuid

from aiohttp import web
import motor.motor_asyncio
from PIL import Image

from image_processing.handlers import ImageFormatConverter

DB_NAME = os.environ.get('DB_NAME')

routers = web.RouteTableDef()

import logging
LOG_FILENAME = 'storage.log'
logging.basicConfig(
    filename=LOG_FILENAME,
    level=logging.DEBUG,
)


def base64_encode(data):
    return base64.b64encode(data).decode('utf-8')


def base64_decode(data):
    return base64.b64decode(data)


def standard_response(success=None, message=None, data=None):
    """Creates a standard response dict from keyword arguments."""
    if success is None:
        success = True
    if message is None:
        message = ''
    if data is None:
        data = []
    _response = {'success': success, 'message': message, 'data': data}
    return web.json_response(_response)


def get_image_format(content_type, default='JPEG'):
    if not content_type:
        return default

    format_ = content_type.split('/')[1]
    return format_.upper()


@routers.post('/images')
async def upload_image(request):
    """
    Uploads an image

    Returns
    -------
    success : bool
        True if successful, false if not
    message : str
        A human-readable error message
    data : dict
        The data response having the form
        ::
            {
                'id': UUID of uploaded image,
            }
    """
    db = request.app['db']
    host, _ = request.transport.get_extra_info('peername')

    content_type = request.headers.get('Content-Type')
    if 'image' not in content_type:
        return standard_response(success=False, message='Content type must contain an image format')

    data = await request.read()
    if not data:
        return standard_response(success=False, message='Image not found')

    image = {
        'id': str(uuid.uuid4()),
        'content_type': content_type,
        'format': get_image_format(content_type),
        'size': len(data),
        'data': base64_encode(data),
        'host': host,
        'upload_time': datetime.utcnow().isoformat()
    }
    await db.images.insert_one(image)

    return standard_response(data={'id': image['id']})


@routers.get('/images/{uuid}')
async def get_image(request):
    """
    Downloads an image. You can specify the needed image type in URL
    Example: '/images/<some_UUID>?type=png'

    Parameters
    ----------
    uuid: str
        Image ID (UUID)

    Returns
    -------
    success : bool
        True if successful, false if not
    message : str
        A human-readable error message
    data : dict
        The data response having the form
        ::
            {
                'id': 'UUID of uploaded image',
                'data': 'base64-encoded image',
                'content_type': 'A content type of an image',
                'size': 'Size of image in bytes',
                'upload_time': '2018-07-20T08:54:28.660792' # In UTC
            }
    """
    db = request.app['db']
    data = await db.images.find_one({'id': request.match_info['uuid']},
                                    projection={'_id': False, 'host': False})
    if not data:
        return standard_response(success=False, message='Image not found')

    image_type = request.query.get('type')
    if image_type:
        format_converter = ImageFormatConverter(data=base64_decode(data['data']),
                                                format=data['format'])

        if not format_converter.validate_format(image_type):
            message = ('Invalid image type: {0}. Available types are:'
                       '{1}'.format(image_type, format_converter.available_types))
            return standard_response(success=False, message=message)

        image_data = format_converter.convert_to(image_type)
        if not image_data:
            return standard_response(success=False, message="Conversion error occurred")

        data['data'] = base64_encode(image_data)
        data['content_type'] = 'image/{}'.format(image_type)

    return standard_response(data=data)


async def setup(app):
    # Setup MongoDB async connection
    client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://mongodb:27017', io_loop=app.loop)
    app['db'] = client[DB_NAME]


if __name__ == '__main__':
    app = web.Application()
    app.add_routes(routers)
    app.on_startup.append(setup)
    web.run_app(app)
