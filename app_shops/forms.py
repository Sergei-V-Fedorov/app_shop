from django import forms
from django.core.exceptions import ValidationError

from app_shops.models import Item
from django.utils.translation import gettext_lazy as _


class ItemForm(forms.ModelForm):
    file = forms.ImageField(widget=forms.ClearableFileInput(attrs={'multiple': True}),
                            label=_('файлы').capitalize(), required=False)

    class Meta:
        model = Item
        fields = ['code', 'name', 'description', 'price', 'amount',
                  'file', 'is_promotion', 'is_offer']


class UploadFile(forms.Form):
    file = forms.FileField(label=_('выбрать файл').capitalize())


class TimeInterval(forms.Form):
    """Define time interval for sale statistics."""
    date_from = forms.DateField(input_formats=['%Y-%m-%d'], help_text=_('ГГГГ-ММ-ДД'))
    date_to = forms.DateField(input_formats=['%Y-%m-%d'], help_text=_('ГГГГ-ММ-ДД'))

    def clean_date_to(self):
        """Check if date_to equal or greater than date_from."""
        if 'date_from' in self.cleaned_data and 'date_to' in self.cleaned_data:
            first_date = self.cleaned_data.get('date_from')
            second_date = self.cleaned_data.get('date_to')
            if second_date < first_date:
                raise ValidationError(_('последняя дата не должна быть меньше первой'))
            return second_date
