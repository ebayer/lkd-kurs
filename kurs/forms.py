# coding=utf-8

from django import forms

class ApplicationChoiceForm(forms.Form):
    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices')
        super(ApplicationChoiceForm, self).__init__(*args, **kwargs)
        self.fields["choice"] = forms.ChoiceField(choices = choices)

class ApplicationPermitForm(forms.Form):
    file = forms.FileField()
