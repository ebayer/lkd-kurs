# coding=utf-8

from django import forms
from django.db import models
from kurs.models import *
from registration.forms import RegistrationFormUniqueEmail
from django.contrib.localflavor.tr.forms import TRPhoneNumberField

class ApplicationChoiceForm(forms.Form):
    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices')
        super(ApplicationChoiceForm, self).__init__(*args, **kwargs)
        self.fields["choice"] = forms.ChoiceField(choices = choices)

class ApplicationPermitForm(forms.Form):
    file = forms.FileField()

class ProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        try:
            self.fields['mobile'].initial = self.instance.mobile
            self.fields['phone'].initial = self.instance.phone
            self.fields['email'].initial = self.instance.user.email
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
        except User.DoesNotExist:
            pass

    mobile = TRPhoneNumberField()
    phone = TRPhoneNumberField()
    email = forms.EmailField(label="Primary email", help_text='')
    first_name = forms.CharField(label="First Name", help_text='')
    last_name = forms.CharField(label="Last Name", help_text='')

    class Meta:
        model = UserProfile
        exclude = ('user','mobile','phone',)

    def save(self, *args, **kwargs):
        """
        Update the primary email address on the related User object as well.
        """
        u = self.instance.user
        u.email = self.cleaned_data['email']
        u.first_name = self.cleaned_data['first_name']
        u.last_name = self.cleaned_data['last_name']
        u.save()
        profile = super(ProfileForm, self).save(*args,**kwargs)
        profile.mobile = self.cleaned_data['mobile']
        profile.phone = self.cleaned_data['phone']
        profile.save()
        return profile

class RegistrationFormUniqueEmailwithProfile(RegistrationFormUniqueEmail):
    first_name = forms.CharField(label="First Name", help_text='')
    last_name = forms.CharField(label="Last Name", help_text='')
    company = forms.CharField(label='Çalıştığı Kurum', max_length=30)
    contact_address = forms.CharField(label="İletişim Adresi", widget=forms.Textarea)
    mobile = TRPhoneNumberField()
    phone = TRPhoneNumberField()
