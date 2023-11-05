from flask import Flask
from jinja2 import Environment, PackageLoader, select_autoescape

app = Flask(__name__)

jinja_env = Environment(
        loader=PackageLoader("responder"),
        autoescape=select_autoescape()
        )


@app.route("/")
def hello_world():
    template = jinja_env.get_template("index.html")
    return template.render(the="variables", go="here")
