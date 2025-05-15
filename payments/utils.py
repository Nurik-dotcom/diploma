from django.utils import timezone
from django.db.models import Avg, Max
from .models import Transaction, SuspiciousLog

def calculate_user_features(user, amount):
    now = timezone.now()

    features = {
        'amount': amount,
        'days_since_signup': (now - user.date_joined).days,
        'transactions_last_hour': Transaction.objects.filter(sender=user, date__gte=now - timezone.timedelta(hours=1)).count(),
        'transactions_last_day': Transaction.objects.filter(sender=user, date__gte=now - timezone.timedelta(days=1)).count(),
        'transactions_last_week': Transaction.objects.filter(sender=user, date__gte=now - timezone.timedelta(days=7)).count(),
        'avg_transaction_amount': Transaction.objects.filter(sender=user).aggregate(Avg('amount'))['amount__avg'] or 0.0,
        'suspicious_transactions_count': SuspiciousLog.objects.filter(transaction__sender=user).count(),
        'max_transaction_amount_day': Transaction.objects.filter(sender=user, date__gte=now - timezone.timedelta(days=1)).aggregate(Max('amount'))['amount__max'] or 0.0,
        'failed_transactions_today': Transaction.objects.filter(sender=user, status='REJECTED', date__gte=now - timezone.timedelta(days=1)).count(),
        'incoming_outgoing_ratio': (Transaction.objects.filter(receiver=user).count() / Transaction.objects.filter(sender=user).count()) if Transaction.objects.filter(sender=user).count() else 0
    }
    return features
