========
Tutorial
========

This tutorial walks you through building progressively more complex applications with gntplib.

Tutorial 1: Simple Task Manager
================================

Let's build a task manager that sends notifications when tasks are completed.

Basic Version
-------------

.. code-block:: python

   from gntplib import Publisher, Event
   
   class TaskManager:
       def __init__(self):
           events = [Event('task_complete', 'Task Completed')]
           self.publisher = Publisher('TaskManager', events)
           self.publisher.register()
       
       def complete_task(self, task_name):
           """Mark a task as complete and notify."""
           print(f"Completing task: {task_name}")
           self.publisher.publish(
               'task_complete',
               'Task Done',
               f'"{task_name}" has been completed!'
           )
   
   # Usage
   manager = TaskManager()
   manager.complete_task('Write documentation')
   manager.complete_task('Fix bug #123')

Adding Priority
---------------

Let's add priority levels for tasks:

.. code-block:: python

   from gntplib import Publisher, Event
   
   class TaskManager:
       def __init__(self):
           events = [
               Event('low_priority', 'Low Priority Task'),
               Event('normal_priority', 'Normal Priority Task'),
               Event('high_priority', 'High Priority Task'),
           ]
           self.publisher = Publisher('TaskManager', events)
           self.publisher.register()
       
       def complete_task(self, task_name, priority='normal'):
           """Complete task with priority level."""
           priority_map = {
               'low': ('low_priority', -1),
               'normal': ('normal_priority', 0),
               'high': ('high_priority', 1),
           }
           
           event_name, notification_priority = priority_map[priority]
           
           self.publisher.publish(
               event_name,
               f'{priority.title()} Priority Task Done',
               f'"{task_name}" has been completed!',
               priority=notification_priority
           )
   
   # Usage
   manager = TaskManager()
   manager.complete_task('Update README', priority='low')
   manager.complete_task('Review code', priority='normal')
   manager.complete_task('Fix production bug', priority='high')

Adding Icons
------------

Make it visual with icons:

.. code-block:: python

   from gntplib import Publisher, Event, Resource
   
   class TaskManager:
       def __init__(self):
           # Define events with icons
           events = [
               Event('low_priority', 'Low Priority', 
                     icon=Resource.from_file('icons/low.png')),
               Event('normal_priority', 'Normal Priority',
                     icon=Resource.from_file('icons/normal.png')),
               Event('high_priority', 'High Priority',
                     icon=Resource.from_file('icons/high.png')),
           ]
           
           # App icon
           app_icon = Resource.from_file('icons/app.png')
           
           self.publisher = Publisher('TaskManager', events, icon=app_icon)
           self.publisher.register()
       
       def complete_task(self, task_name, priority='normal'):
           priority_map = {
               'low': ('low_priority', -1),
               'normal': ('normal_priority', 0),
               'high': ('high_priority', 1),
           }
           
           event_name, notification_priority = priority_map[priority]
           
           self.publisher.publish(
               event_name,
               f'{priority.title()} Priority Task',
               f'✓ "{task_name}" completed!',
               priority=notification_priority
           )

Tutorial 2: Build Monitor
=========================

A CI/CD build monitoring system with notifications.

Basic Build Monitor
-------------------

.. code-block:: python

   from gntplib import Publisher, Event, Resource
   from datetime import datetime
   
   class BuildMonitor:
       def __init__(self, project_name):
           self.project_name = project_name
           
           # Define build events
           events = [
               Event('build_started', 'Build Started'),
               Event('build_success', 'Build Succeeded'),
               Event('build_failed', 'Build Failed'),
           ]
           
           self.publisher = Publisher(f'BuildMonitor-{project_name}', events)
           self.publisher.register()
       
       def build_started(self, build_number):
           """Notify that build has started."""
           self.publisher.publish(
               'build_started',
               f'Build #{build_number} Started',
               f'Building {self.project_name}...',
               priority=0
           )
       
       def build_completed(self, build_number, success, duration):
           """Notify build completion."""
           if success:
               event = 'build_success'
               title = f'Build #{build_number} Succeeded ✓'
               priority = 0
           else:
               event = 'build_failed'
               title = f'Build #{build_number} Failed ✗'
               priority = 2  # Emergency
           
           message = f'{self.project_name} - Duration: {duration}s'
           
           self.publisher.publish(
               event,
               title,
               message,
               priority=priority,
               sticky=not success  # Keep failures visible
           )
   
   # Usage
   monitor = BuildMonitor('MyProject')
   
   import time
   monitor.build_started(42)
   time.sleep(2)  # Simulate build
   monitor.build_completed(42, success=True, duration=120)

With Detailed Information
-------------------------

Add more details to notifications:

.. code-block:: python

   from gntplib import Publisher, Event
   from datetime import datetime
   
   class BuildMonitor:
       def __init__(self, project_name):
           self.project_name = project_name
           
           events = [
               Event('build_started', 'Build Started'),
               Event('build_success', 'Build Succeeded'),
               Event('build_failed', 'Build Failed'),
               Event('tests_failed', 'Tests Failed'),
           ]
           
           self.publisher = Publisher(f'BuildMonitor-{project_name}', events)
           self.publisher.register()
       
       def build_started(self, build_number, branch='main', commit=None):
           """Notify build start with details."""
           details = [
               f'Project: {self.project_name}',
               f'Branch: {branch}',
               f'Time: {datetime.now().strftime("%H:%M:%S")}'
           ]
           
           if commit:
               details.append(f'Commit: {commit[:8]}')
           
           self.publisher.publish(
               'build_started',
               f'Build #{build_number} Started',
               '\n'.join(details),
               priority=0,
               id_=f'build-{build_number}'
           )
       
       def build_completed(self, build_number, success, duration, 
                          tests_passed=None, tests_failed=None, errors=None):
           """Notify completion with test results."""
           
           if not success:
               # Build failed
               event = 'build_failed'
               title = f'Build #{build_number} Failed ✗'
               priority = 2
               
               details = [
                   f'Project: {self.project_name}',
                   f'Duration: {duration}s',
               ]
               
               if errors:
                   details.append(f'\nErrors:\n{errors}')
               
           elif tests_failed and tests_failed > 0:
               # Build succeeded but tests failed
               event = 'tests_failed'
               title = f'Build #{build_number} - Tests Failed'
               priority = 1
               
               details = [
                   f'Project: {self.project_name}',
                   f'Duration: {duration}s',
                   f'Tests Passed: {tests_passed}',
                   f'Tests Failed: {tests_failed}',
               ]
           else:
               # Everything succeeded
               event = 'build_success'
               title = f'Build #{build_number} Succeeded ✓'
               priority = 0
               
               details = [
                   f'Project: {self.project_name}',
                   f'Duration: {duration}s',
                   f'Tests Passed: {tests_passed}',
               ]
           
           self.publisher.publish(
               event,
               title,
               '\n'.join(details),
               priority=priority,
               sticky=(priority > 0),  # Keep if issues
               coalescing_id=f'build-{build_number}'
           )
   
   # Usage
   monitor = BuildMonitor('MyProject')
   
   monitor.build_started(42, branch='feature-x', commit='abc123def')
   # ... build happens ...
   monitor.build_completed(
       42,
       success=True,
       duration=145,
       tests_passed=150,
       tests_failed=0
   )

Tutorial 3: System Monitor
==========================

Monitor system resources and send alerts.

.. code-block:: python

   from gntplib import Publisher, Event
   import psutil
   import time
   
   class SystemMonitor:
       def __init__(self, thresholds=None):
           # Default thresholds
           self.thresholds = thresholds or {
               'cpu': 80.0,
               'memory': 85.0,
               'disk': 90.0,
           }
           
           # Define events
           events = [
               Event('cpu_alert', 'CPU Alert'),
               Event('memory_alert', 'Memory Alert'),
               Event('disk_alert', 'Disk Alert'),
               Event('system_normal', 'System Normal'),
           ]
           
           self.publisher = Publisher('SystemMonitor', events)
           self.publisher.register()
           
           # Track alert state to avoid spam
           self.alert_active = {
               'cpu': False,
               'memory': False,
               'disk': False,
           }
       
       def check_cpu(self):
           """Check CPU usage."""
           usage = psutil.cpu_percent(interval=1)
           
           if usage > self.thresholds['cpu'] and not self.alert_active['cpu']:
               self.publisher.publish(
                   'cpu_alert',
                   'High CPU Usage',
                   f'CPU usage is at {usage:.1f}%',
                   priority=1,
                   sticky=True
               )
               self.alert_active['cpu'] = True
           
           elif usage <= self.thresholds['cpu'] and self.alert_active['cpu']:
               self.publisher.publish(
                   'system_normal',
                   'CPU Normal',
                   f'CPU usage back to {usage:.1f}%',
                   priority=0
               )
               self.alert_active['cpu'] = False
       
       def check_memory(self):
           """Check memory usage."""
           memory = psutil.virtual_memory()
           usage = memory.percent
           
           if usage > self.thresholds['memory'] and not self.alert_active['memory']:
               self.publisher.publish(
                   'memory_alert',
                   'High Memory Usage',
                   f'Memory usage is at {usage:.1f}%\n'
                   f'Available: {memory.available / (1024**3):.1f} GB',
                   priority=1,
                   sticky=True
               )
               self.alert_active['memory'] = True
           
           elif usage <= self.thresholds['memory'] and self.alert_active['memory']:
               self.publisher.publish(
                   'system_normal',
                   'Memory Normal',
                   f'Memory usage back to {usage:.1f}%',
                   priority=0
               )
               self.alert_active['memory'] = False
       
       def check_disk(self):
           """Check disk usage."""
           disk = psutil.disk_usage('/')
           usage = disk.percent
           
           if usage > self.thresholds['disk'] and not self.alert_active['disk']:
               self.publisher.publish(
                   'disk_alert',
                   'Low Disk Space',
                   f'Disk usage is at {usage:.1f}%\n'
                   f'Free space: {disk.free / (1024**3):.1f} GB',
                   priority=2,
                   sticky=True
               )
               self.alert_active['disk'] = True
           
           elif usage <= self.thresholds['disk'] and self.alert_active['disk']:
               self.publisher.publish(
                   'system_normal',
                   'Disk Space Normal',
                   f'Disk usage back to {usage:.1f}%',
                   priority=0
               )
               self.alert_active['disk'] = False
       
       def monitor_loop(self, interval=60):
           """Run monitoring loop."""
           print(f"Starting system monitor (interval: {interval}s)")
           print("Press Ctrl+C to stop")
           
           try:
               while True:
                   self.check_cpu()
                   self.check_memory()
                   self.check_disk()
                   time.sleep(interval)
           except KeyboardInterrupt:
               print("\nMonitoring stopped")
   
   # Usage
   if __name__ == '__main__':
       # Custom thresholds
       monitor = SystemMonitor(thresholds={
           'cpu': 75.0,
           'memory': 80.0,
           'disk': 85.0,
       })
       
       # Start monitoring
       monitor.monitor_loop(interval=30)

Tutorial 4: Application with Callbacks
=======================================

Handle user interactions with callbacks.

.. code-block:: python

   from gntplib import Publisher, Event, SocketCallback
   
   class InteractiveApp:
       def __init__(self):
           events = [Event('question', 'User Question')]
           self.publisher = Publisher('InteractiveApp', events)
           self.publisher.register()
           
           self.user_responses = []
       
       def on_clicked(self, response):
           """Handle click event."""
           print(f"User clicked the notification!")
           context = response.headers.get('Notification-Callback-Context')
           self.user_responses.append(('clicked', context))
           return f"Handled click: {context}"
       
       def on_closed(self, response):
           """Handle close event."""
           print(f"User closed the notification")
           context = response.headers.get('Notification-Callback-Context')
           self.user_responses.append(('closed', context))
           return f"Handled close: {context}"
       
       def ask_question(self, question, question_id):
           """Ask user a question via notification."""
           callback = SocketCallback(
               context=question_id,
               context_type='question',
               on_click=self.on_clicked,
               on_close=self.on_closed
           )
           
           self.publisher.publish(
               'question',
               'Question',
               question,
               priority=1,
               sticky=True,
               gntp_callback=callback
           )
   
   # Usage
   app = InteractiveApp()
   app.ask_question('Do you want to continue?', 'q1')
   app.ask_question('Save changes?', 'q2')

Next Steps
==========

Continue learning:

* :doc:`advanced` - Authentication, encryption, and more
* :doc:`async` - Async/await with Tornado
* :doc:`../api/core` - Complete API reference