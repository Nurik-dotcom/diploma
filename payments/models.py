import uuid
import random
from datetime import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from datetime import timezone

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import AbstractUser
import random
from decimal import Decimal


def generate_account_number():
    # Генерирует случайное 16-ричное число (строка из 16 символов)
    return ''.join(random.choices('0123456789ABCDEF', k=16))


class User(AbstractUser):
    """Модель пользователя с балансом и ролью."""
    balance = models.FloatField(default=0.0)

    ROLE_CHOICES = (
        ('admin', 'Администратор'),
        ('user', 'Обычный пользователь'),
    )
    account_number = models.CharField(max_length=16, unique=True, null=False, default=generate_account_number)
    full_name = models.CharField(max_length=255, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    ACCOUNT_STATUS_CHOICES = (
        ('active', 'Активен'),
        ('blocked', 'Заблокирован'),
        ('frozen', 'Заморожен'),
    )
    account_status = models.CharField(max_length=10, choices=ACCOUNT_STATUS_CHOICES, default='active')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')

    def __str__(self):
        return self.email or self.username


class PaymentQRCode(models.Model):
    TYPE_CHOICES = (
        ('open', 'Открытая'),  # пользователь вводит сумму при сканировании
        ('fixed', 'Фиксированная'),  # сумма фиксирована
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='qr_codes')
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)  # уникальный идентификатор для QR-кода
    qr_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='open')
    fixed_amount = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # если не задан – код может не истекать
    is_active = models.BooleanField(default=True)
    transferred_amount = models.FloatField(default=0.0)
    transfer_count = models.PositiveIntegerField(default=0)

    def remaining_time(self):
        if self.expires_at:
            delta = self.expires_at - timezone.now()
            return delta.total_seconds() if delta.total_seconds() > 0 else 0
        return None

    def __str__(self):
        return f"QR Code {self.code} ({self.get_qr_type_display()}) для {self.owner.username}"


class Transaction(models.Model):
    """Модель финансовой транзакции."""
    sender = models.ForeignKey('User', related_name="sent_transactions", on_delete=models.CASCADE)
    receiver = models.ForeignKey('User', related_name="received_transactions", on_delete=models.CASCADE)
    amount = models.FloatField(validators=[MinValueValidator(0.01), MaxValueValidator(1000000000.0)])
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('SUSPICIOUS', 'Suspicious'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    date = models.DateTimeField(auto_now_add=True)
    risk_score = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(100.0)], default=0.0)

    def __str__(self):
        return f"Transaction #{self.id} from {self.sender} to {self.receiver}"


class SuspiciousLog(models.Model):
    """Лог подозрительной транзакции."""
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    reason = models.TextField()  # Причина пометки как подозрительной
    date = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)  # Обработана ли ситуация

    def __str__(self):
        return f"SuspiciousLog for Transaction #{self.transaction.id}"
