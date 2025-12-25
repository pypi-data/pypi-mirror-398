from django.db.models.signals import ModelSignal

# this signal gathers all activity report needed to be inserted into the daily brief
add_employee_activity_to_daily_brief = ModelSignal(use_caching=True)
