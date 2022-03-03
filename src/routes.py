

from bottle import route, static_file, request
from furl import furl

from client import client
from components.actions import button
from components.gpt_conversation import gpt_conversation
from components.utils import lazy_block
from components.transcript_tabs import transcript_tabs
from errors import ValidationError


HEAD = '''
<head>
    <script src="https://unpkg.com/htmx.org@1.6.1"></script>

    <link rel="stylesheet" href="static/style.css"/>
</head>
'''


# ------- UTILITY ROUTES -------


@route('/static/<path:path>')
def static(path):
    return static_file(path, root='static')


@route('/audio/status')
def audio_status():
    message = "✔ Audio exists" if client.audio_exists() else "✘ Audio not found"
    return f'<div>{message}</div>'


@route('/text')
def text():

    # TRANSCRIPT FOUND
    if client.text_exists():
        return f'''
            <br>
            <div> ✔ Transcript exists </div>
            <br>
            <br>
            {transcript_tabs()}
            {get_questions()}
            <br>
        '''

    # TRANSCRIPT NOT FOUND, run?
    else:
        return f'''
            <br>
            <div> ✘ Transcript not found </div>
            <br>
            {button(
                identifier="transcribe-button",
                hx_get=f'/lazy/transcript/run',
                hx_target="#transcribe-button",
                load_label='AWS transcribing...',
                label='Run transcript')}
        '''


@route('/lazy/<path:path>')
def lazy_route(path):
    extra_values = dict(furl(f"/mock_url?{request.query_string}").args)
    load_label = extra_values.pop('load_label', '')
    return lazy_block(path, load_label, extra_values)


# ------- UI ROUTES -------


@route('/transcript/run')
def run_transcription():
    _ = client.transcribe()
    return text()


@route('/answers')
def answers():
    _ = client.narrate()
    answers = '<br>'.join(client.narrator.result.answers.split('\n'))
    return f'''
        <h3> Answers </h3>
        <p class="answers"> {answers} </p>
    '''

@route('/questions', method='GET')
def get_questions():
    return gpt_conversation()

@route('/questions', method='POST')
def post_questions():

    question = request.params.get('question')

    if question:
        client.questions.append(question)

    return gpt_conversation()


@route('/results', method='POST')
def results():

    feedback_id = request.params.get('search')

    if not feedback_id:
        return ''

    try:
        client.set_feedback_id(feedback_id)
    except ValidationError:
        return f"<p>Expected format: <b>1ab8eeec-7f60-4af0-ba16-06ad6f55a8a9</b></p>\
                 <p>Got instead: <b>{feedback_id}</b></p>"

    return f"""
            <br>
            {lazy_block(f"/audio/status", "Looking for Audio...")}
            <br>
            {lazy_block(f"/text", "Looking for Transcript...")}
        """


@route('/feedback')
def feedback():

    body = '''
            <div class="default">

                 <h1>
                   Transcription
                 </h1>

                <input class="text-input" type="search" id="input-box"
                       name="search" placeholder="Paste feedback id..."
                       hx-post="/results"
                       hx-trigger="keyup changed delay:500ms, search"
                       hx-target="#results">

                <div class="results" id="results"/>
            </div>
            '''

    return f"{HEAD}\n\n{body}"
