
from client import client
from components.actions import button


def gpt_conversation():

    return f'''
        <div id="questions">
            <h3> Questions </h3>
            {client.question_html()}
            <br><br>
            <form hx-post="/questions" hx-target="#questions">
              <label>
                    <input  name="question"
                            type="question"
                            class="text-input"
                            id="new-question"
                            placeholder="Add new question">
              </label>
            </form>

            {button(
                identifier='q-button',
                hx_get=f"/lazy/answers",
                hx_target="#q-button",
                label='Load answers',
                load_label="Asking GPT...")}
        </div>
    '''
