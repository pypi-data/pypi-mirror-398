"""
caerp related hacks used to ensure code compatibility from within celery tasks
"""
from pyramid.security import remember
from pyramid_layout.config import create_layout_manager
from caerp.views.render_api import Api


class DummyEvent:
    def __init__(self, request, context):
        self.request = request
        self.request.context = context
        self.context = context


def setup_rendering_hacks(pyramid_request, context):
    event = DummyEvent(pyramid_request, context)
    create_layout_manager(event)
    pyramid_request.api = Api(context, pyramid_request)
