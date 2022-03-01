
import json


def hx_vals(dictionary=None):
    if not dictionary:
        return ''
    return f"hx-vals='{json.dumps(dictionary)}'" if any(dictionary.values()) else ''


def lazy_block(hx_get, load_label="Loading...", extra_values=None, indicator_size=20):
    return f"""
        <div hx-get="{hx_get}" hx-trigger="load" {hx_vals(extra_values)}>
            <span class="htmx-indicator">
                <img src="/static/bars.svg" width="{indicator_size}"/>
                {load_label}
            </span>
        </div>
    """
