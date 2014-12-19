# coding=utf-8

from django import forms
from kurs.models import ApplicationPermit, UserProfile, User
from userena.forms import SignupForm
from localflavor.tr.forms import TRPhoneNumberField
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
# time of registration.
class SignupFormwithProfile(SignupForm):
    first_name = forms.CharField(label=_("First name"))
    last_name = forms.CharField(label=_("Last name"))
    company = forms.CharField(label=_('Company'))
    contact_address = forms.CharField(label=_("Contact address"), widget=forms.Textarea)
    mobile = TRPhoneNumberField(label=_("Mobile"))
    phone = TRPhoneNumberField(label=_("Phone"))

    def __init__(self, *args, **kw):
        """
        A bit of hackery to get the first name and last name at the top of the
        form instead at the end.
        """
        super(SignupFormwithProfile, self).__init__(*args, **kw)

    def save(self):
        """
        Override the save method to save the first and last name to the user
        field.
        """
        # First save the parent form and get the user.
        new_user = super(SignupFormwithProfile, self).save()

        # Get the profile, the `save` method above creates a profile for each
        # user because it calls the manager method `create_user`.
        # See: https://github.com/bread-and-pepper/django-userena/blob/master/userena/managers.py#L65
        user_profile = new_user.my_profile

        new_user.first_name = self.cleaned_data['first_name']
        new_user.last_name = self.cleaned_data['last_name']
        new_user.save()
        user_profile.company = self.cleaned_data['company']
        user_profile.contact_address = self.cleaned_data['contact_address']
        user_profile.mobile = self.cleaned_data['mobile']
        user_profile.phone = self.cleaned_data['phone']
        user_profile.save()

        # Userena expects to get the new user from this form, so return the new
        # user.
        return new_user
