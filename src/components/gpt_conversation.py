
from .actions import button
from client import Client


def gpt_conversation(feedback_id):
    return f'''
        <div id="questions">
            <h3> Questions </h3>
            {Client(feedback_id).question_html()}
            <br><br>
            <form hx-post="/questions/{feedback_id}" hx-target="#questions">
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
                hx_get=f"/lazy/answers/{feedback_id}",
                hx_target="#q-button",
                label='Load answers',
                load_label="Asking GPT...")}
        </div>
    '''
