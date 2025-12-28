from django.dispatch import Signal

task_started = Signal()
task_finished = Signal()
task_failure = Signal()
