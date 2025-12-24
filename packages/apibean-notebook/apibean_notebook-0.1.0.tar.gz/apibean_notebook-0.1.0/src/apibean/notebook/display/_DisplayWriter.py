from IPython.display import clear_output, display, update_display, HTML

class DisplayWriter:
    surround_top: str = "⬆️<br>"
    surround_bottom: str = "<br>⬇️"

    def __init__(self, title:str="stdout stream", use_display_id=True):
        if use_display_id:
            self._display_id = display(self._get_formatted_title(title), display_id=True)
        else:
            self._display_id = None

    def render(self, lines, stream_type:str|None=None):
        html_object = self._get_formatted_lines(lines, stream_type=stream_type)
        if self._display_id:
            update_display(html_object, display_id=self._display_id.display_id)
        else:
            clear_output(wait=True)
            display(html_object)

    def write(self, html:str):
        html_object = self._get_enclosed_html(html)
        if self._display_id:
            update_display(html_object, display_id=self._display_id.display_id)
        else:
            display(html_object)

    def clear(self):
        if self._display_id:
            blank = HTML("<pre style='margin:0'></pre>")
            update_display(blank, display_id=self._display_id.display_id, clear=True)
        else:
            clear_output(wait=True)

    def _get_formatted_title(self, title):
        return HTML(f"<pre style='margin:0;color:#555'>[{title}]</pre>")

    def _get_formatted_lines(self, lines, stream_type:str|None=None):
        if stream_type == 'stderr':
            html_lines = []
            for line in lines:
                html_lines.append(f"<span style='color:red'>{line}</span>")
            html = "<br>".join(html_lines)
        else:
            html = '<br>'.join(lines)
        return self._get_enclosed_html(html)

    def _get_enclosed_html(self, html):
        return HTML(f"<pre style='margin:0'>{self.surround_top}{html}{self.surround_bottom}</pre>")
