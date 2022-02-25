

import json
import re

from bottle import route, static_file, request, default_app
from client import Client, QUESTIONS
from furl import furl


HEAD = '''
<head>
    <script src="https://unpkg.com/htmx.org@1.6.1"></script>

    <link rel="stylesheet" href="static/page/style.css"/>
</head>
'''

QUESTIONS = '<br>'.join(QUESTIONS.split('\n'))


class ValidationError(Exception):
    pass


def _hx_vals(dictionary=None):
    if not dictionary:
        return ''
    return f"hx-vals='{json.dumps(dictionary)}'" if any(dictionary.values()) else ''


def lazy_block(hx_get, load_label, extra_values=None, indicator_size=20):
    return f"""
        <div hx-get="{hx_get}" hx-trigger="load" {_hx_vals(extra_values)}>
            <span class="htmx-indicator">
                <img src="/static/bars.svg" width="{indicator_size}"/>
                {load_label}
            </span>
        </div>
    """


def button(identifier, hx_get, hx_target, label, load_label=None):

    extra_values = {
        'load_label': load_label
    }

    return f'''
        <button class="button"
            hx-swap="outerHTML"
            id="{identifier}"
            hx-get="{hx_get}"
            hx-target="{hx_target}"
            {_hx_vals(extra_values)}
        >
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{label} <img class="htmx-indicator" src="/static/bars.svg" width="20">
        </button>
    '''


def validate_feedback_id(feedback_id):
    pattern = re.compile("[0-9a-z]{8}(-[0-9a-z]{4}){3}-[0-9a-z]{12}$")
    if not pattern.match(feedback_id):
        raise ValidationError("Unexpected feedback id format. Expecting i.e.: 1ab8eeec-7f60-4af0-ba16-06ad6f55a8a9")


# ------- UTILITY ROUTES -------


@route('/static/<path:path>')
def static(path):
    print('>>> STATIC', path)
    return static_file(path, root='static')


@route('/audio/<feedback_id>/status')
def audio_status(feedback_id):
    client = Client(feedback_id)
    message = "✔ Audio exists" if client.audio_exists() else "✘ Audio not found"
    return f'<div>{message}</div>'


@route('/text/<feedback_id>')
def text(feedback_id):
    client = Client(feedback_id)

    # TRANSCRIPT FOUND
    if client.text_exists():
        return f'''
          <br>
          <div> ✔ Transcript exists </div>
          <br>
          {lazy_block(f"/transcript/{feedback_id}", "Fetching...")}
        '''

    # TRANSCRIPT NOT FOUND, run?
    else:
        return f'''
            <br>
            <div> ✘ Transcript not found </div>
            <br>
            {button(
                identifier='transcribe_button',
                hx_get=f'/lazy/transcript/{feedback_id}/run',
                hx_target='#transcribe-button',
                load_label='AWS transcribing...',
                label='Run transcript')}
        '''


@route('/lazy/<path:path>')
def lazy_route(path):
    extra_values = dict(furl(f"/mock_url?{request.query_string}").args)
    load_label = extra_values.pop('load_label', None)
    return lazy_block(path, load_label, extra_values)


# ------- UI ROUTES -------


@route('/transcript/<feedback_id>/run')
def run_transcription(feedback_id):
    client = Client(feedback_id)
    _ = client.transcribe()
    return text(feedback_id)


@route('/transcript/<feedback_id>/run')
def run_transcript(feedback_id):
    client = Client(feedback_id)
    _ = client.narrate
    return transcript(feedback_id)


@route('/transcript/<feedback_id>')
def transcript(feedback_id):
    client = Client(feedback_id)

    if not client.text_exists():
        return ''

    return f'''
        <p class="default">{client.fetch_transcript()}</p>
        <h3> Questions </h3>
        <p class="questions"> {QUESTIONS} </p>

        {button(
            identifier='q-button',
            hx_get=f"/lazy/answers/{feedback_id}",
            hx_target="#q-button",
            label='Load answers',
            load_label="Asking GPT...")}
    '''


@route('/answers/<feedback_id>')
def answers(feedback_id):
    client = Client(feedback_id)
    _ = client.narrate()
    answers = '<br>'.join(client.narrator.result.answers.split('\n'))
    return f'''
        <h3> Answers </h3>
        <p class="answers"> {answers} </p>
    '''


@route('/results', method='POST')
def results():

    feedback_id = request.params.get('search')

    if not feedback_id:
        return ''

    try:
        validate_feedback_id(feedback_id)
    except ValidationError:
        return f"<p>Expected format: <b>1ab8eeec-7f60-4af0-ba16-06ad6f55a8a9</b></p>\
                 <p>Got instead: <b>{feedback_id}</b></p>"

    return f"""
            <br>
            {lazy_block(f"/audio/{feedback_id}/status", "Looking for Audio...")}
            <br>
            {lazy_block(f"/text/{feedback_id}", "Looking for Transcript...")}
        """


@route('/feedback')
def feedback():

    print(">>> FUCK THIS SHIT")

    body = '''
            <div class="default">

                 <h1>
                   Transcription
                 </h1>

                <input class="form-control" type="search" id="input-box"
                       name="search" placeholder="Paste feedback id..."
                       hx-post="/results"
                       hx-trigger="keyup changed delay:500ms, search"
                       hx-target="#results">

                <div class="results" id="results"/>
            </div>
            '''

    return f"{HEAD}\n\n{body}"
