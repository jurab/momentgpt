

from bottle import route, static_file, request
from client import Client, QUESTIONS
from furl import furl

from components.actions import button
from components.utils import lazy_block
from errors import ValidationError
from validators import validate_feedback_id


HEAD = '''
<head>
    <script src="https://unpkg.com/htmx.org@1.6.1"></script>

    <link rel="stylesheet" href="static/style.css"/>
</head>
'''

QUESTIONS = '<br>'.join(QUESTIONS.split('\n'))

# ------- UTILITY ROUTES -------


@route('/static/<path:path>')
def static(path):
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
                hx_get=f'/lazy/transcript/{feedback_id}/run',
                hx_target="#transcribe-button",
                load_label='AWS transcribing...',
                label='Run transcript')}
        '''


@route('/text/<feedback_id>/tab1')
def tab1(feedback_id):
    return f'''
        <div class="tab-list">
        	<a hx-get="text/{feedback_id}/tab1" class="selected">Tab 1</a>
        	<a hx-get="text/{feedback_id}/tab2">Tab 2</a>
        </div>

        <div class="tab-content">
        	Commodo normcore truffaut VHS duis gluten-free keffiyeh iPhone taxidermy godard ramps anim pour-over.
        	Pitchfork vegan mollit umami quinoa aute aliquip kinfolk eiusmod live-edge cardigan ipsum locavore.
        	Polaroid duis occaecat narwhal small batch food truck.
        	PBR&B venmo shaman small batch you probably haven't heard of them hot chicken readymade.
        	Enim tousled cliche woke, typewriter single-origin coffee hella culpa.
        	Art party readymade 90's, asymmetrical hell of fingerstache ipsum.
        </div>
        '''


@route('/text/<feedback_id>/tab2')
def tab2(feedback_id):
    return f'''
        <div class="tab-list">
        	<a hx-get="/text/{feedback_id}/tab1">Tab 1</a>
        	<a hx-get="/text/{feedback_id}/tab2" class="selected">Tab 2</a>
        </div>

        <div class="tab-content">
        	 cooking your scrambled eggs for less time on the heat. Yeah. Okay. By doing this, you're gonna affect
             the change of texture. Therefore, giving you a looser product, a slightly lighter and giving us that
             desire. Glossy, glossy look, outcome. Um, So to give you a bit of information and egg starts to cook
             at around 60 degrees. So white and jokes are slightly different, but with scrambled eggs, you've got
              the mixed together, so we'll go for around 60 degrees, and that's not really that hot. That's about
              the same. Temperatures are really hot cup of teeth. So be be mindful of how long you're hitting the
              pan for. Um, how do we know for ages over cooking?
        </div>
        '''


# @route('/text/<feedback_id>/translation_tabs')
# def translation_tabs(feedback_id):
#     return f'''
#         <div id="tabs" hx-target="#tab-contents" _="on htmx:afterOnLoad take .selected for event.target">
#         	<a hx-get="/text/{feedback_id}/tab1" class="selected"> Original </a>
#         	<a hx-get="/text/{feedback_id}/tab2"> Translation </a>
#         </div>
#
#         <div id="tab-contents" hx-get="/text/{feedback_id}/tab1" hx-trigger="load"></div>
#         '''


@route('/text/<feedback_id>/translation_tabs')
def translation_tabs(feedback_id):
    return '''
        <div id="tabs" hx-get="/tab1" hx-trigger="load after:100ms" hx-target="#tabs" hx-swap="innerHTML"></div>
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


@route('/transcript/<feedback_id>')
def transcript(feedback_id):
    client = Client(feedback_id)

    if not client.text_exists():
        return ''

    return f'''
        <p class="default">{client.fetch_transcript()}</p>
        <div id="tabs" hx-get="text/{feedback_id}/tab1" hx-trigger="load after:100ms" hx-target="#tabs" hx-swap="innerHTML"></div>
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
            <br>
            {lazy_block(f"/text/{feedback_id}/translation_tabs", "Translating...")}
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
