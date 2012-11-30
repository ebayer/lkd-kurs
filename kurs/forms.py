from django import forms

class ApplicationAgreement(forms.Form):
    approve = forms.BooleanField()

class ApplicationChoice(forms.Form):
    choice = forms.ChoiceField()
