

from .utils import hx_vals


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
            {hx_vals(extra_values)}
        >
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{label} <img class="htmx-indicator" src="/static/bars.svg" width="20">
        </button>
    '''
