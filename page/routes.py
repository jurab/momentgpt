

import re

from bottle import route, static_file, request
from client import Client, QUESTIONS


HEAD = '''
<head>
    <script src="https://unpkg.com/htmx.org@1.6.1"></script>

    <link rel="stylesheet" href="static/page/style.css"/>
</head>
'''

QUESTIONS = '<br>'.join(QUESTIONS.split('\n'))


class ValidationError(Exception):
    pass


def validate_feedback_id(feedback_id):
    pattern = re.compile("[0-9a-z]{8}(-[0-9a-z]{4}){3}-[0-9a-z]{12}$")
    if not pattern.match(feedback_id):
        raise ValidationError("Unexpected feedback id format. Expecting i.e.: 1ab8eeec-7f60-4af0-ba16-06ad6f55a8a9")


@route('/static/<path:path>')
def media(path):
    print('>>> MEDIA CALL', path)
    return static_file(path, root='.')


@route('/audio_status/<feedback_id>')
def audio_status(feedback_id):
    client = Client(feedback_id)
    message = "✔ Audio exists" if client.audio_exists() else "✘ Audio not found"
    return f'<div>{message}</div>'


@route('/text/<feedback_id>')
def text(feedback_id):
    client = Client(feedback_id)
    if client.text_exists():
        return f'''
          <br>
          <div> ✔ Transcript exists </div>
          <br>
          {_lazy_block(f"/transcript/{feedback_id}", "Fetching...")}
        '''

    else:
        return f'''
            <br>
            <div> ✘ Text not found </div>
            <br>
            <button class='button' id="transcribe-button" hx-get="/lazy_run_transcription/{feedback_id}" hx-target="#transcribe-button" hx-swap="outerHTML">
                Run transcription <img class="htmx-indicator" src="/media/bars.svg" width="20">
            </button>
        '''


@route('/run_transcription/<feedback_id>')
def run_transcription(feedback_id):
    client = Client(feedback_id)
    _ = client.transcribe()
    return text(feedback_id)



@route('/lazy_run_transcription/<feedback_id>')
def lazy_run_transcription(feedback_id):
    return _lazy_block(f'/run_transcription/{feedback_id}', "AWS transcribing...")


@route('/answers/<feedback_id>')
def answers(feedback_id):
    client = Client(feedback_id)
    _ = client.narrate()
    answers = '<br>'.join(client.narrator.result.answers.split('\n'))
    return f'<p class="answers"> {answers} </p>'


@route('/qa/<feedback_id>')
def qa(feedback_id):
    return _lazy_block(f"/answers/{feedback_id}", "Asking GPT...")


@route('/run_transcript/<feedback_id>')
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
        <button class='button' id="q-button" hx-get="/qa/{feedback_id}" hx-target="#q-button" hx-swap="outerHTML">
            Load answers <img class="htmx-indicator" src="/media/bars.svg" width="20">
        </button>
    '''


def _lazy_block(hx_get, placeholder, indicator_size=20):
    return f"""
        <div hx-get="{hx_get}" hx-trigger="load">
            <span class="htmx-indicator">
                <img src="/media/bars.svg" width="{indicator_size}"/>
                {placeholder}
            </span>
        </div>
    """


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
            {_lazy_block(f"/audio_status/{feedback_id}", "Looking for Audio...")}
            <br>
            {_lazy_block(f"/text/{feedback_id}", "Looking for Transcript...")}
        """


@route('/feedback')
def feedback():

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
