# -*- coding: utf-8 -*-
import logging

from celery import Celery, Task
from flask import Flask


def create_app():
    app = Flask(__name__)

    app.config["CELERY"] = {
        "broker_url": "redis://redis:6379/0",
        "result_backend": "redis://redis:6379/0",
        "task_ignore_result": False
    }

    celery_init_app(app)

    app.logger.setLevel(logging.ERROR)
    logging.basicConfig(filename="app/logs/main.log",
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")  # noqa: E501

    from . import routes
    app.register_blueprint(routes.bp, url_prefix="/")

    return app


def celery_init_app(app: Flask):
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app
