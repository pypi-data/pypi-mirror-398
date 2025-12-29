import os


def needs_sentry_init():
    return os.getenv('SENTRY_DSN') is not None


def init_sentry():
    import sentry_sdk
    from sentry_sdk.integrations.ray import RayIntegration

    dsn = os.getenv('SENTRY_DSN')
    if dsn is None:
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv('DEPLOYMENT_TARGET', 'development'),
        integrations=[RayIntegration()],
        send_default_pii=True,
    )


def worker_process_setup_hook(*_, **__):
    init_sentry()
