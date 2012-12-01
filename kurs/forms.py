# coding=utf-8

from django import forms

class ApplicationAgreement(forms.Form):
    approve = forms.BooleanField()

class ApplicationChoiceForm(forms.Form):
    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices')
        super(ApplicationChoiceForm, self).__init__(*args, **kwargs)
        self.fields["choice"] = forms.ChoiceField(choices = choices)
