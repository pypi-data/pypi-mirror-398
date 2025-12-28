from thestage import __app_name__

from thestage.controllers import base_controller, container_controller, instance_controller, \
    config_controller, project_controller

base_controller.app.add_typer(container_controller.app, name="container")
base_controller.app.add_typer(instance_controller.app, name="instance")
base_controller.app.add_typer(config_controller.app, name="config")
base_controller.app.add_typer(project_controller.app, name="project")


def main():
    # example of a command to debug
    project_controller.app([
        "run",
        "-wd",
        "/Users/alexey/Documents/clonetest",
        "-dcuid",
        '62-1',
        '-t',
        'task',
        '-com',
        "'echo 123'"
    ], prog_name=__app_name__)


if __name__ == "__main__":
    main()
