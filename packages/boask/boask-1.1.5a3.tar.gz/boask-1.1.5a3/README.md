# Boask

Pure Python website engine.  
Zero external dependencies.  
Real JSX-style templates without React.

```bash
pip install boask
```

## Quick Start

```python
from boask import route, use, run_server, html_templates

@route("/")
def home(handler):
    return html_templates.render("home.html", title="Boask")

if __name__ == "__main__":
    run_server()
```

### Comparison to Flask

1. Lightweight.
2. No external dependecies.
3. Unlike flask, it uses built in python libaries only! It uses built-in libs, and some python file libs that are using only built in functions!
4. No "{{ url_for('static', filename='css/main.css') }}" (example), we use /static/css/main.css for example!

#### Info

1. Do not install a earlier version than 1.0.4, you can 1.0.0 but that one is not supported! You can't import them! Also, do not install 1.1.4! It had a bug in strict slashes and it did 500 always! I don't know how the 1.1.4 issue happened! Do not install 1.1.5a2 also! It has import error instead of import .error
