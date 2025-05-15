from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
import datetime

class CustomUserCreationForm(UserCreationForm):
    full_name = forms.CharField(required=True, label="ФИО")
    date_of_birth = forms.DateField(
        required=True,
        label="Дата рождения",
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'full_name', 'date_of_birth')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует")
        return email

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = datetime.date.today()
            # Вычисляем возраст
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                raise forms.ValidationError("Регистрация доступна только пользователям старше 18 лет.")
        return dob
