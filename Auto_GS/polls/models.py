from django.db import models

# Create your models here.

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model

from django import forms



class tcForm(forms.Form):
    example_dataview_sequence_number = forms.IntegerField()
    dummy_telecommand__myinteger_payload = forms.IntegerField()
    dummy_telecommand__myinteger_timestamp = forms.IntegerField()
    dummy_telemetry__myinteger_payload = forms.IntegerField()
    dummy_telemetry__myinteger_timestamp = forms.IntegerField()


