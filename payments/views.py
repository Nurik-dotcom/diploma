from decimal import Decimal, InvalidOperation
import io
from .ml_utils import predict_fraud
import numpy as np
from .utils import calculate_user_features
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User, Transaction
from .utils import calculate_user_features
from .ml_utils import predict_fraud
import qrcode
from django.http import HttpResponse, Http404
from .models import PaymentQRCode
from django.urls import reverse
from django.shortcuts import render
from django.db import models
from .utils import calculate_user_features
from .ml_utils import predict_fraud
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from .models import User, Transaction, SuspiciousLog, PaymentQRCode
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages

from django.contrib.auth.decorators import login_required

from .utils import calculate_user_features


@login_required
def sent_transactions(request):
    # Показываем только транзакции, инициированные текущим пользователем
    transactions = Transaction.objects.filter(sender=request.user).order_by('-date')
    return render(request, 'payments/sent_transactions.html', {'transactions': transactions})

@login_required
def received_transactions(request):
    # Показываем транзакции, где пользователь является получателем и статус "APPROVED"
    transactions = Transaction.objects.filter(receiver=request.user, status='APPROVED').order_by('-date')
    return render(request, 'payments/received_transactions.html', {'transactions': transactions})



from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User, Transaction
from .utils import calculate_user_features
from .ml_utils import predict_fraud

@login_required
def create_transaction(request):
    if request.method == 'POST':
        sender = request.user
        receiver_account = request.POST.get('receiver_account')

        try:
            amount = float(request.POST.get('amount'))
        except (TypeError, ValueError):
            messages.error(request, "Некорректная сумма.")
            return redirect('home')

        # Проверяем, существует ли получатель
        try:
            receiver = User.objects.get(account_number=receiver_account)
        except User.DoesNotExist:
            messages.error(request, "Получатель не найден.")
            return redirect('home')

        # ❌ Блокируем замороженные и заблокированные аккаунты
        if sender.account_status in ['frozen', 'blocked']:
            messages.error(request, "Ваш аккаунт заморожен или заблокирован. Транзакции невозможны.")
            return redirect('home')

        if receiver.account_status in ['frozen', 'blocked']:
            messages.error(request, "Аккаунт получателя заморожен или заблокирован. Транзакция отклонена.")
            return redirect('home')

        # Проверка: нельзя переводить самому себе
        if sender.pk == receiver.pk:
            messages.error(request, "Нельзя отправлять деньги самому себе.")
            return redirect('home')

        # Проверка баланса отправителя
        if sender.balance < amount:
            messages.error(request, "Недостаточно средств.")
            return redirect('home')

        # Машинное обучение (определение риска)
        features = calculate_user_features(sender, amount)
        risk_score = predict_fraud(features)

        if risk_score >= 50.0:
            status = 'SUSPICIOUS'
            messages.warning(request, "Транзакция требует дополнительной проверки.")
        else:
            status = 'APPROVED'
            sender.balance -= amount
            receiver.balance += amount
            sender.save()
            receiver.save()
            messages.success(request, "Транзакция успешно выполнена.")

        # Создание транзакции
        Transaction.objects.create(
            sender=sender,
            receiver=receiver,
            amount=amount,
            risk_score=risk_score,
            status=status
        )

        return redirect('sent_transactions')

    return render(request, 'payments/new_transaction.html')


@login_required
def scan_qr_code(request):
    return render(request, 'payments/scan_qr.html')


@login_required
def process_qr_code(request, code):
    try:
        qr = PaymentQRCode.objects.get(code=code, is_active=True)
    except PaymentQRCode.DoesNotExist:
        messages.error(request, "Неверный или неактивный QR-код.")
        return redirect('home')

    # Если код фиксированный – сумма берётся из QR-кода, иначе оставляем возможность ввода
    amount = qr.fixed_amount if qr.qr_type == 'fixed' else None

    context = {
        'qr': qr,
        'amount': amount,
    }
    return render(request, 'payments/process_qr.html', context)


@login_required
def view_qr_page(request, code):
    try:
        qr = PaymentQRCode.objects.get(code=code, is_active=True)
    except PaymentQRCode.DoesNotExist:
        messages.error(request, "QR-код не найден или неактивен.")
        return redirect('qr_history')

    context = {
        'qr': qr,
    }
    return render(request, 'payments/view_qr.html', context)


@login_required
def transfer_via_qr(request, code):
    try:
        qr = PaymentQRCode.objects.get(code=code, is_active=True)
    except PaymentQRCode.DoesNotExist:
        messages.error(request, "Неверный или неактивный QR-код.")
        return redirect('home')

    sender = request.user

    # ❌ Блокируем замороженные и заблокированные аккаунты
    if sender.account_status in ['frozen', 'blocked']:
        messages.error(request, "Ваш аккаунт заморожен или заблокирован. Транзакции невозможны.")
        return redirect('home')

    if qr.owner.account_status in ['frozen', 'blocked']:
        messages.error(request, "Аккаунт получателя заморожен или заблокирован. Транзакция отклонена.")
        return redirect('home')

    # Запрещаем перевод самому себе
    if sender.pk == qr.owner.pk:
        messages.error(request, "Нельзя переводить самому себе.")
        return redirect('home')

    if request.method == 'POST':
        if qr.qr_type == 'fixed':
            amount = qr.fixed_amount
        else:
            amount_str = request.POST.get('amount')
            try:
                amount = float(amount_str)
            except (TypeError, ValueError):
                messages.error(request, "Некорректная сумма.")
                return redirect('process_qr', code=code)

        # Проверка баланса отправителя
        if sender.balance < amount:
            messages.error(request, "Недостаточно средств.")
            return redirect('process_qr', code=code)

        # Создание транзакции
        transaction = Transaction.objects.create(sender=sender, receiver=qr.owner, amount=amount, status='APPROVED')
        sender.balance -= amount
        qr.owner.balance += amount
        sender.save()
        qr.owner.save()

        # Обновляем статистику QR-кода
        qr.transferred_amount += amount
        qr.transfer_count += 1
        qr.save()

        messages.success(request, "Транзакция выполнена через QR-код.")
        return redirect('sent_transactions')
    else:
        return render(request, 'payments/process_qr.html', {'qr': qr})



@login_required
def create_open_qr(request):
    if request.method == 'POST':
        expires_at_str = request.POST.get('expires_at')  # ожидаем формат ISO или другой удобный для parse_datetime
        expires_at = None
        if expires_at_str:
            from django.utils.dateparse import parse_datetime
            expires_at = parse_datetime(expires_at_str)
        qr = PaymentQRCode.objects.create(owner=request.user, qr_type='open', expires_at=expires_at)
        messages.success(request, f"Открытый QR-код создан. Код: {qr.code}")
        return redirect('qr_history')
    return render(request, 'payments/create_open_qr.html')

@login_required
def create_fixed_qr(request):
    if request.method == 'POST':
        fixed_amount = request.POST.get('fixed_amount')
        try:
            fixed_amount = float(fixed_amount)
        except (TypeError, ValueError):
            messages.error(request, "Некорректная сумма.")
            return redirect('create_fixed_qr')
        expires_at_str = request.POST.get('expires_at')
        expires_at = None
        if expires_at_str:
            from django.utils.dateparse import parse_datetime
            expires_at = parse_datetime(expires_at_str)
        qr = PaymentQRCode.objects.create(owner=request.user, qr_type='fixed', fixed_amount=fixed_amount, expires_at=expires_at)
        messages.success(request, f"Фиксированный QR-код создан. Код: {qr.code}")
        return redirect('qr_history')
    return render(request, 'payments/create_fixed_qr.html')

@login_required
def qr_history(request):
    qr_codes = PaymentQRCode.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'payments/qr_history.html', {'qr_codes': qr_codes})


def is_admin(user):
    # Проверка, является ли пользователь администратором (роль admin или флаг is_staff)
    return user.is_authenticated and (user.is_staff or getattr(user, 'role', '') == 'admin')

@user_passes_test(is_admin)
def admin_dashboard(request):
    # Фильтрация по параметрам запроса (например, ?status=SUSPICIOUS или ?user=email)
    tx_queryset = Transaction.objects.select_related('sender', 'receiver').all().order_by('-date')
    status_filter = request.GET.get('status')
    user_filter = request.GET.get('user')
    if status_filter:
        tx_queryset = tx_queryset.filter(status=status_filter.upper())
    if user_filter:
        # фильтр по отправителю или получателю по email или части имени
        tx_queryset = tx_queryset.filter(models.Q(sender__email__icontains=user_filter) | 
                                         models.Q(receiver__email__icontains=user_filter))
    # Получаем логи подозрительных операций для отображения причин (словарь transaction_id -> reason)
    suspicious_logs = SuspiciousLog.objects.filter(resolved=False)
    log_dict = {log.transaction_id: log.reason for log in suspicious_logs}
    context = {
        'transactions': tx_queryset,
        'log_reasons': log_dict,
        'status_filter': status_filter or '',
        'user_filter': user_filter or '',
    }
    return render(request, 'payments/admin_dashboard.html', context)


@user_passes_test(lambda user: user.is_authenticated and (user.is_staff or getattr(user, 'role', '') == 'admin'))
def approve_transaction(request, tx_id):
    transaction = get_object_or_404(Transaction, id=tx_id)
    # Если транзакция ранее не была одобрена, обновляем балансы
    if transaction.status != 'APPROVED':
        sender = transaction.sender
        receiver = transaction.receiver
        # Дополнительная проверка: достаточно ли средств на балансе отправителя
        if sender.balance < transaction.amount:
            messages.error(request, "Недостаточно средств для одобрения транзакции.")
            return redirect('admin_dashboard')
        sender.balance -= float(transaction.amount)
        receiver.balance += transaction.amount
        sender.save()
        receiver.save()
    transaction.status = 'APPROVED'
    transaction.save()
    SuspiciousLog.objects.filter(transaction=transaction).update(resolved=True)
    messages.success(request, f"Транзакция #{tx_id} одобрена.")
    return redirect('admin_dashboard')

@login_required
def freeze_account(request):
    user = request.user
    # Если счет уже не активен, выводим сообщение
    if user.account_status != 'active':
        messages.error(request, "Ваш счет уже не активен, заморозить его нельзя.")
    else:
        user.account_status = 'frozen'
        user.save()
        messages.success(request, "Ваш счет успешно заморожен.")
    return redirect('profile')

@login_required
def unfreeze_account(request):
    user = request.user
    if user.account_status != 'frozen':
        messages.error(request, "Ваш счет не заморожен.")
    else:
        user.account_status = 'active'
        user.save()
        messages.success(request, "Ваш счет успешно разморожен.")
    return redirect('profile')

@user_passes_test(is_admin)
def reject_transaction(request, tx_id):
    transaction = get_object_or_404(Transaction, id=tx_id)
    # Если в URL передан параметр block=1, блокируем отправителя
    if request.GET.get('block') == '1':
        sender = transaction.sender
        sender.account_status = 'blocked'
        sender.save()
        messages.info(request, f"Пользователь {sender.username} заблокирован.")

    transaction.status = 'REJECTED'
    transaction.save()
    SuspiciousLog.objects.filter(transaction=transaction).update(resolved=True)
    messages.success(request, f"Транзакция #{tx_id} отклонена.")
    return redirect('admin_dashboard')

# payments/views.py (фрагмент)
@login_required
def transaction_history(request):
    # Выбираем транзакции, где текущий пользователь является отправителем или получателем
    transactions = Transaction.objects.filter(models.Q(sender=request.user) | models.Q(receiver=request.user))
    transactions = transactions.select_related('sender', 'receiver').order_by('-date')
    return render(request, 'payments/(old)cd.html', {'transactions': transactions})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Устанавливаем дополнительные поля из формы
            user.full_name = form.cleaned_data['full_name']
            user.date_of_birth = form.cleaned_data['date_of_birth']
            user.role = 'user'
            user.save()
            login(request, user)  # Автоматический вход после регистрации
            messages.success(request, "Регистрация прошла успешно!")
            return redirect('home')
        else:
            messages.error(request, "Ошибка регистрации. Проверьте введённые данные.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})




def custom_login(request):
    if request.method == 'POST':
        # Получаем данные из формы
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Проверяем учетные данные
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Вы успешно вошли в систему.")
            return redirect('home')
        else:
            messages.error(request, "Неверное имя пользователя или пароль.")
    # GET-запрос или ошибка – возвращаем форму входа
    return render(request, 'registration/login.html')


from django.contrib.auth import logout
from django.contrib import messages

def custom_logout(request):
    logout(request)
    messages.info(request, "Вы успешно вышли из системы.")
    return redirect('login')

from django.contrib.auth.decorators import login_required

@login_required
def profile(request):
    return render(request, 'payments/profile.html', {'user': request.user})



@login_required
def top_up_balance(request):
    if request.method == 'POST':
        try:
            amount = float(request.POST.get('amount'))
            if amount <= 0:
                messages.error(request, "Введите корректную сумму для пополнения.")
                return redirect('profile')
        except (TypeError, ValueError):
            messages.error(request, "Некорректное значение суммы.")
            return redirect('profile')

        request.user.balance += amount
        request.user.save()
        messages.success(request, f"Баланс успешно пополнен на {amount:.2f}.")
    return redirect('profile')



def qr_code_image(request, code):
    try:
        qr_obj = PaymentQRCode.objects.get(code=code)
    except PaymentQRCode.DoesNotExist:
        raise Http404("QR-код не найден")

    # Формируем абсолютный URL для обработки QR-кода
    qr_url = request.build_absolute_uri(reverse('process_qr', kwargs={'code': qr_obj.code}))

    # Генерируем QR-код с данными ссылки
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return HttpResponse(buf.getvalue(), content_type="image/png")


import joblib
import os


# Функция для извлечения признаков из новой транзакции (аналогична оффлайн-версии)
def extract_features_from_tx(sender, amount):
    days_since_signup = (timezone.now() - sender.date_joined).days
    one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
    recent_count = Transaction.objects.filter(sender=sender, date__gte=one_hour_ago).count()
    return [amount, days_since_signup, recent_count]


def predict_fraud_risk(sender, amount):
    # Загрузите модель (убедитесь, что путь корректный и модель обучена)
    model_path = os.path.join(os.path.dirname(__file__), 'fraud_model_balanced.pkl')
    try:
        model = joblib.load(model_path)
    except Exception as e:
        # Если модель не найдена, вернем нулевой риск
        return 0.0, []

    features = np.array([extract_features_from_tx(sender, amount)])
    risk_probability = model.predict_proba(features)[0][1]  # вероятность мошенничества
    # Можно добавить дополнительные причины на основе пороговых значений
    reasons = []
    if risk_probability >= 0.5:
        reasons.append("Высокая вероятность мошенничества по модели.")
    return risk_probability * 100.0, reasons  # переводим в проценты

