

import time

from bottle import route
from client import Client

from components.utils import lazy_block


def transcript_tabs(feedback_id):
    return f'''
      <div
        id="text-tabs"
        hx-get="/text/{feedback_id}/tab1"
        hx-trigger="load after:100ms"
        hx-target="#text-tabs"
        hx-swap="innerHTML"></div>
    '''

@route('/text/<feedback_id>/tab1')
def text_tab1(feedback_id):
    return f'''
        <div class="tab-list">
        	<a hx-get="text/{feedback_id}/tab1" class="selected"> Original </a>
        	<a hx-get="text/{feedback_id}/tab2"> Translation </a>
        </div>
        <div class="tab-content">
            {lazy_block(f'/text/{feedback_id}/transcript')}
        </div>
    '''


@route('/text/<feedback_id>/transcript')
def _text_tab1(feedback_id):

    client = Client(feedback_id)
    return f'''
        <div class="tab-list">
        	<a hx-get="text/{feedback_id}/tab1" class="selected"> Original </a>
        	<a hx-get="text/{feedback_id}/tab2"> Translation </a>
        </div>
        <div class="tab-content">
            <p class="tab-content"> {client.fetch_transcript() if client.text_exists() else ""} </p>
        </div>
    '''

@route('/text/<feedback_id>/tab2')
def text_tab2(feedback_id):
    return f'''
        <div class="tab-list">
        	<a hx-get="text/{feedback_id}/tab1"> Original </a>
        	<a hx-get="text/{feedback_id}/tab2" class="selected"> Translation </a>
        </div>
        <div class="tab-content">
            {lazy_block(f'/text/{feedback_id}/translation')}
        </div>
    '''


@route('/text/<feedback_id>/translation')
def _text_tab2(feedback_id):

    client = Client(feedback_id)
    return f'''
        <div class="tab-list">
        	<a hx-get="text/{feedback_id}/tab1"> Original </a>
        	<a hx-get="text/{feedback_id}/tab2" class="selected"> Translation </a>
        </div>
        <div class="tab-content">
            <p class="tab-content"> {client.translate() if client.text_exists() else ""} </p>
        </div>
    '''
