from raystack.core.management.templates import TemplateCommand
import os
import raystack


class Command(TemplateCommand):
    help = (
        "Creates a Raystack app directory structure for the given app name in "
        "the current directory or optionally in the given directory."
    )
    missing_args_message = "You must provide an application name."

    def add_arguments(self, parser):
        super().add_arguments(parser)

    def handle(self, **options):
        app_name = options.pop("name")
        target = options.pop("directory")

        template_name = "app_template"
        options["template"] = os.path.join(raystack.__path__[0], "conf", template_name)
        super().handle("app", app_name, target, **options)
