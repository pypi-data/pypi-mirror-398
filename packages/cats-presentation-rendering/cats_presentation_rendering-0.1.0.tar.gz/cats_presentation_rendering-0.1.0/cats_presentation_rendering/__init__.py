"""
cats_presentation-rendering - Display an embedded cat presentation in Jupyter.
"""

try:
    from IPython.display import HTML, display
    _in_jupyter = True
except ImportError:
    _in_jupyter = False

def show_presentation():
    """
    Display the cat presentation.
    Works in Jupyter notebooks (renders HTML) or prints HTML otherwise.
    """
    html_code = '''
    <div style="position: relative; width: 100%; height: 0; padding-top: 56.25%; padding-bottom: 0; box-shadow: 0 2px 8px 0 rgba(63,69,81,0.16); margin-top: 1.6em; margin-bottom: 0.9em; overflow: hidden; border-radius: 8px; will-change: transform;">
      <iframe loading="lazy" style="position:absolute; width: 100%; height: 100%; top: 0; left: 0; border: none; padding: 0; margin: 0;" 
              src="https://app.dochipo.com/pub/69415f46338332b6560ce085/documents/b42e7e2c-6284-464f-8596-942cb5fea9fd?embed=true" 
              frameborder="0">
      </iframe>
    </div>
    '''

    if _in_jupyter:
        display(HTML(html_code))
    else:
        print(":: cats_presentation-rendering ::\n")
        print("To view the presentation, run this in a Jupyter notebook.")
        print("Fallback HTML code:\n")
        print(html_code)