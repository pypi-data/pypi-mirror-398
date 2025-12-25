import os
from chameleon import PageTemplateLoader
from flask import current_app


class Chameleon(object):
    def __init__(self, app=None, root_dir=None, macro_templates=None):
        """
        Args:
            app: the Flask App
            root_dir: filesystem path that is root for the templates
            macro_templates: mapping with name -> template_file for macro templates
        """
        self.app = app
        if root_dir is None:
            root_dir = os.getcwd()
        self.loader = PageTemplateLoader(root_dir)
        self.macros = {}
        if macro_templates is not None:
            for name, template_file in macro_templates.items():
                self.macros[name] = self.loader[template_file]
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.extensions["chameleon"] = self
