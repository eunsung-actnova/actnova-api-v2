from datetime import timedelta

beat_schedule = {
    'monitor-labeling-status-every-5-minutes': {
        'task': 'app.celery.monitor.monitor_labeling_status',
        'schedule': timedelta(minutes=5),
    },
}

broker_url = 'amqp://guest:guest@rabbitmq:5672//'
result_backend = 'rpc://'
