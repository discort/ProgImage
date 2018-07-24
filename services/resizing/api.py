import base64
from io import BytesIO

from aiohttp import web, ClientSession
from PIL import Image
from image_processing.handlers import ImageResizingHandler


routers = web.RouteTableDef()


STORAGE_API_URL = 'http://storage_api:8080'
import logging
LOG_FILENAME = 'resizing.log'
logging.basicConfig(
    filename=LOG_FILENAME,
    level=logging.DEBUG,
)


def base64_encode(data):
    return base64.b64encode(data).decode('utf-8')


def base64_decode(data):
    return base64.b64decode(data)


def check_for_madatories(req_data, params):
    message = None
    for param in params:
        if param not in req_data:
            message = "Param '{}' is mandatory".format(param)
    return message


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


@routers.post('/resize')
async def resize_image(request):
    """
    Resize an image

    Parameters
    ----------
    width: int - Image new width
    height: int – Image new height

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
                'image': resized image in base64-encoded representation
            }
    """
    data = await request.json()
    error = check_for_madatories(data, ('height', 'width'))
    if error:
        return standard_response(success=False, message=error)

    images_url = '{url}/images/{image_id}'.format(url=STORAGE_API_URL, image_id=data['image_id'])
    async with ClientSession() as session:
        async with session.get(images_url) as resp:
            resp_data = await resp.json()

    if not resp_data['success']:
        return standard_response(success=False, message=resp_data['message'])

    image_data = resp_data['data']['data']
    rotator = ImageResizingHandler(data=base64_decode(image_data),
                                   format=resp_data['data']['format'])
    image = rotator.resize(width=data['width'], height=data['height'])
    if not image:
        return standard_response(success=False, message='Resizing error occurred')

    return standard_response(data={'image': base64_encode(image)})


if __name__ == '__main__':
    app = web.Application()
    app.add_routes(routers)
    web.run_app(app, port=8082)
