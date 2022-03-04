

from bottle import route
from client import Client

from .utils import lazy_block


def transcript_tabs(feedback_id):

    return f'''
      <div
        id="text-tabs"
        hx-get="components/text/tab1/{feedback_id}"
        hx-trigger="load after:100ms"
        hx-target="#text-tabs"
        hx-swap="innerHTML"></div>
    '''

@route('/components/text/tab1/<feedback_id>')
def text_tab1(feedback_id):
    return f'''
        <div class="tab-list">
        	<a hx-get="components/text/tab1/{feedback_id}" class="selected"> Original </a>
        	<a hx-get="components/text/tab2/{feedback_id}"> Translation </a>
        </div>
        <div class="tab-content">
            {lazy_block(f'/components/text/transcript/{feedback_id}')}
        </div>
    '''


@route('/components/text/transcript/<feedback_id>')
def _text_tab1(feedback_id):

    client = Client(feedback_id)
    return f'''
        <div class="tab-list">
        	<a hx-get="components/text/tab1/{feedback_id}" class="selected"> Original </a>
        	<a hx-get="components/text/tab2/{feedback_id}"> Translation </a>
        </div>
        <div class="tab-content">
            <p class="tab-content"> {client.get_transcript() if client.text_exists() else ""} </p>
        </div>
    '''

@route('/components/text/tab2/<feedback_id>')
def text_tab2(feedback_id):
    return f'''
        <div class="tab-list">
        	<a hx-get="components/text/tab1/{feedback_id}"> Original </a>
        	<a hx-get="components/text/tab2/{feedback_id}" class="selected"> Translation </a>
        </div>
        <div class="tab-content">
            {lazy_block(f'/components/text/translation/{feedback_id}')}
        </div>
    '''


@route('/components/text/translation/<feedback_id>')
def _text_tab2(feedback_id):

    client = Client(feedback_id)
    return f'''
        <div class="tab-list">
        	<a hx-get="components/text/tab1/{feedback_id}"> Original </a>
        	<a hx-get="components/text/tab2/{feedback_id}" class="selected"> Translation </a>
        </div>
        <div class="tab-content">
            <p class="tab-content"> {client.translate() if client.text_exists() else ""} </p>
        </div>
    '''
