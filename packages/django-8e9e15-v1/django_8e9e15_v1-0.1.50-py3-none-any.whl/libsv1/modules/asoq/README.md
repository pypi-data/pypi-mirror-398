# ASOQ - Asynchronous Simple In-Memory Queue

ASOQ is a minimalist, zero-dependency background task processor for Python, designed for simple, in-memory asynchronous execution. It's perfect for Django applications that need to offload long-running, non-critical tasks from the request-response cycle without the overhead of setting up external brokers like Redis or RabbitMQ.

## Key Features

* **Zero External Dependencies:** Works out-of-the-box with any standard Python installation.
* **Pure Python:** Built entirely on the standard `multiprocessing` library.
* **Extremely Simple API:** Just use the `@task()` decorator on your functions.
* **Non-Blocking Execution:** Your API views return immediately while tasks run in the background.
* **Seamless Django Integration:** Designed to work flawlessly with the Django development server's process model.
* **Configurable Logging:** Integrates with Python's standard `logging` module.

> ### Important Note: In-Memory Operation
> ASOQ is **in-memory**. This means any tasks in the queue that have not been processed will be **lost** if the server restarts or crashes. It is not suitable for critical or persistent tasks. For production-grade, persistent task queuing, consider robust solutions like **Celery** with **Redis** or **RabbitMQ**.

---

## Installation

Currently, ASOQ is distributed as a single file.

1.  Create a `libs` or `utils` directory in your Django project's root.
2.  Place the `asoq.py` file inside it.

---

## Quick Start with Django

Here’s how to get ASOQ running in your Django project in 4 simple steps.

### Step 1: Define Your Tasks

Create a `tasks.py` file inside one of your Django apps (e.g., `yourapp/tasks.py`) and define your background tasks using the `@task` decorator.

**`yourapp/tasks.py`**
```python
import time
import logging
from libsv1.modules.asoq import task

logger = logging.getLogger(__name__)

@task()
def send_welcome_email(user_id: int):
    """
    A simulated task to send a welcome email.
    """
    logger.info(f"WORKER: Starting to send welcome email to user {user_id}...")
    time.sleep(10)  # Simulate a long network operation
    logger.info(f"WORKER: Welcome email sent to user {user_id}.")

@task()
def generate_report(report_id: str):
    logger.info(f"WORKER: Generating report {report_id}...")
    time.sleep(15)
    logger.info(f"WORKER: Report {report_id} is complete.")
```

### Step 2: Start the Worker with Django

The best place to start the ASOQ worker is in the `ready()` method of an `AppConfig`. This ensures it starts once Django is initialized.

**`yourapp/apps.py`**
```python
from django.apps import AppConfig
import sys
import os

class YourAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'yourapp'

    def ready(self):
        # Import the worker starter from your asoq library
        from libsv1.modules.asoq import start_worker

        # The 'RUN_MAIN' env var is set by Django's reloader to ensure
        # this code runs only once in the main process.
        if 'runserver' in sys.argv and os.environ.get('RUN_MAIN'):
            print("MAIN PROCESS: Starting ASOQ worker...")
            start_worker()
```

Don't forget to register this AppConfig in your `yourapp/__init__.py`:
`default_app_config = 'yourapp.apps.YourAppConfig'`

### Step 3: Use Your Task in a View

Now you can call your tasks from anywhere in your Django project, like a view. The `.delay()` method is non-blocking and will return immediately.


**`yourapp/views.py`**
```python
from rest_framework.views import APIView
from rest_framework.response import Response
from .tasks import send_welcome_email  # Import your task

class UserRegistrationView(APIView):
    def post(self, request, *args, **kwargs):
        # ... your user creation logic here ...
        user_id = 123 # Assume user is created and has an ID

        print("API VIEW: User created. Enqueuing welcome email.")
        
        # This call is non-blocking. The API will return instantly.
        send_welcome_email.delay(user_id=user_id)
        
        print("API VIEW: Task enqueued. Returning HTTP response.")
        
        return Response({"status": "success", "message": "User registered."}, status=201)
```

## Configuration

### Logging

ASOQ uses Python's standard `logging` module with the logger name `asoq`. You can easily configure it in your Django `settings.py` to control its output and verbosity.

This allows you to see detailed debug messages from the ASOQ worker, format them consistently with your project's logs, or send them to a file or external service.

**`yourproject/settings.py`**
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {process:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        # Configuration for the ASOQ package
        'asoq': {
            'handlers': ['console'],
            'level': 'DEBUG',  # Use DEBUG to see all messages, or INFO for less verbosity
            'propagate': False,
        },
    },
}
```

---

## How It Works

ASOQ leverages Django's `runserver` process model.

1.  **Main Process:** When Django starts, the `ready()` method is called in the main process. This process starts the single, long-lived **ASOQ Worker Process**.
2.  **API Processes:** Django also spawns one or more child processes to handle API requests. These processes are short-lived.
3.  **Communication:** When a task's `.delay()` method is called in an API process, the task details are put onto a `multiprocessing.Queue`. This queue is a process-safe communication channel.
4.  **Execution:** The ASOQ Worker Process continuously listens to this queue. As soon as a task appears, it pulls it from the queue and executes it.

This architecture ensures that the execution of the task is decoupled from the API request-response cycle.

---

## License

This project is licensed under the MIT License.