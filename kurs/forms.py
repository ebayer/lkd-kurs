# coding=utf-8

from django import forms
from kurs.models import ApplicationPermit, UserProfile, User
from registration.forms import RegistrationFormUniqueEmail
from django.contrib.localflavor.tr.forms import TRPhoneNumberField
from django.utils.translation import ugettext_lazy as _

# We would like to set the initial options to users previous application choices
# while editing application choices
class ApplicationChoiceForm(forms.Form):
    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices')
        super(ApplicationChoiceForm, self).__init__(*args, **kwargs)
        self.fields["choice"] = forms.ChoiceField(choices = choices)

# We want to only display a file field for applicationpermit upload form
class ApplicationPermitForm(forms.ModelForm):
    class Meta:
        model = ApplicationPermit
        fields = ["file"]

# Custom edit profile form
# We want to edit e-mail, first_name and last_name attributes from User object
# along with the profile information, we also want to use local flavor for
# phone fields
class ProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Load initial data from existing User object
        super(ProfileForm, self).__init__(*args, **kwargs)
        try:
            self.fields['mobile'].initial = self.instance.mobile
            self.fields['phone'].initial = self.instance.phone
            self.fields['email'].initial = self.instance.user.email
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
        except User.DoesNotExist:
            pass

    # Use local flavor for phone fields
    mobile = TRPhoneNumberField()
    phone = TRPhoneNumberField()
    email = forms.EmailField(label=_("E-mail"))
    first_name = forms.CharField(label=_("First name"))
    last_name = forms.CharField(label=_("Last name"))

    class Meta:
        model = UserProfile
        # We do not want users to edit their username
        # We will also use local flavor for phone fields
        # so we should exclude those in here and re-generate them at __init__
        exclude = ('user','mobile','phone',)

    # Custom method to save user profile information along with
    # base user information
    def save(self, *args, **kwargs):
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

# We want to gather all profile information for the user at the
# time of registration. We also want the registration form to
# enforce using a unique e-mail address
class RegistrationFormUniqueEmailwithProfile(RegistrationFormUniqueEmail):
    first_name = forms.CharField(label=_("First name"))
    last_name = forms.CharField(label=_("Last name"))
    company = forms.CharField(label=_('Company'))
    contact_address = forms.CharField(label=_("Contact address"), widget=forms.Textarea)
    mobile = TRPhoneNumberField(label=_("Mobile"))
    phone = TRPhoneNumberField(label=_("Phone"))
