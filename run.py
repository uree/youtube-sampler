from app import create_app

app = create_app()
celery_app = app.extensions["celery"]
app.app_context().push()
