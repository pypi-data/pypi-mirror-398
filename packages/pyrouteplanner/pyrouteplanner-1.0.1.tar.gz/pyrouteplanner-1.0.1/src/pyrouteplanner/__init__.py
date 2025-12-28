import importlib.resources
import pathlib
from flask import Flask, render_template

package = 'pyrouteplanner'
templates_path = pathlib.Path(importlib.resources.files(package).joinpath("templates"))
static_path = pathlib.Path(importlib.resources.files(package).joinpath("static"))

app = Flask(__name__,
            template_folder=str(templates_path),
            static_folder=str(static_path))


@app.route('/')
def root():
    return render_template('index.html')


def main():
    app.run(host="0.0.0.0", port=9000, debug=True)


if __name__ == '__main__':
    main()
