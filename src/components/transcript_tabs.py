

from bottle import route
from client import client

from components.utils import lazy_block


def transcript_tabs():
    return f'''
      <div
        id="text-tabs"
        hx-get="/text/tab1"
        hx-trigger="load after:100ms"
        hx-target="#text-tabs"
        hx-swap="innerHTML"></div>
    '''

@route('/text/tab1')
def text_tab1():
    return f'''
        <div class="tab-list">
        	<a hx-get="text/tab1" class="selected"> Original </a>
        	<a hx-get="text/tab2"> Translation </a>
        </div>
        <div class="tab-content">
            {lazy_block(f'/text/transcript')}
        </div>
    '''


@route('/text/transcript')
def _text_tab1():

    return f'''
        <div class="tab-list">
        	<a hx-get="text/tab1" class="selected"> Original </a>
        	<a hx-get="text/tab2"> Translation </a>
        </div>
        <div class="tab-content">
            <p class="tab-content"> {client.fetch_transcript() if client.text_exists() else ""} </p>
        </div>
    '''

@route('/text/tab2')
def text_tab2():
    return f'''
        <div class="tab-list">
        	<a hx-get="text/tab1"> Original </a>
        	<a hx-get="text/tab2" class="selected"> Translation </a>
        </div>
        <div class="tab-content">
            {lazy_block(f'/text/translation')}
        </div>
    '''


@route('/text/translation')
def _text_tab2():

    return f'''
        <div class="tab-list">
        	<a hx-get="text/tab1"> Original </a>
        	<a hx-get="text/tab2" class="selected"> Translation </a>
        </div>
        <div class="tab-content">
            <p class="tab-content"> {client.translate() if client.text_exists() else ""} </p>
        </div>
    '''
