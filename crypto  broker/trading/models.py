from django.db import models
from django.contrib.auth.models import User


# ==========================================
# TRADING PAIRS
# ==========================================

class TradingPair(models.Model):

    name = models.CharField(
        max_length=30,
        unique=True
    )

    symbol = models.CharField(
        max_length=20,
        unique=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


# ==========================================
# TRADING ACCOUNT
# ==========================================

class TradingAccount(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default= 0.00
    )

    credit_score = models.PositiveIntegerField(
        default=100
    )

    trading_banned = models.BooleanField(
        default=False
    )

    trading_ban_reason = models.TextField(
        blank=True,
        default=""
    )

    withdrawal_banned = models.BooleanField(
        default=False
    )

    withdrawal_ban_reason = models.TextField(
        blank=True,
        default=""
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.user.username


# ==========================================
# TRADE
# ==========================================

class Trade(models.Model):

    SIDE_CHOICES = [
        ("BUY", "BUY"),
        ("SELL", "SELL"),
    ]

    STATUS_CHOICES = [
        ("OPEN", "OPEN"),
        ("WIN", "WIN"),
        ("LOSS", "LOSS"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    pair = models.ForeignKey(
        TradingPair,
        on_delete=models.PROTECT,
        related_name="trades",
        null=True,
        blank=True
    )

    asset = models.CharField(
        max_length=20,
        default="BTC/USD"
    )

    side = models.CharField(
        max_length=4,
        choices=SIDE_CHOICES
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    price = models.DecimalField(
        max_digits=20,
        decimal_places=8
    )

    closing_price = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True
    )

    duration_seconds = models.PositiveIntegerField(
        default=60
    )

    payout_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=30.00
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="OPEN"
    )

    profit_loss = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )

    closed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        pair_name = self.pair.symbol if self.pair else self.asset

        return (
            f"{self.user.username} - "
            f"{pair_name} - "
            f"{self.side} - "
            f"{self.status}"
        )


# ==========================================
# TRANSACTIONS
# ==========================================

class Transaction(models.Model):

    TYPE_CHOICES = [
        ("DEPOSIT", "DEPOSIT"),
        ("WITHDRAW", "WITHDRAW"),
    ]

    STATUS_CHOICES = [
        ("PENDING", "PENDING"),
        ("APPROVED", "APPROVED"),
        ("REJECTED", "REJECTED"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    transaction_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    comment = models.TextField(
        blank=True,
        default=""
    )

    # ==========================================
    # WITHDRAWAL ACCOUNT DETAILS
    # ==========================================

    account_title = models.CharField(
        max_length=150,
        blank=True,
        default=""
    )

    account_holder_name = models.CharField(
        max_length=150,
        blank=True,
        default=""
    )

    account_number = models.CharField(
        max_length=100,
        blank=True,
        default=""
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.transaction_type} - "
            f"${self.amount}"
        )


# ==========================================
# MARKET CONTROL
# ==========================================

class MarketControl(models.Model):

    DIRECTION_CHOICES = [
        ("AUTO", "AUTO"),
        ("UP", "UP"),
        ("DOWN", "DOWN"),
    ]

    pair = models.OneToOneField(
        TradingPair,
        on_delete=models.CASCADE,
        related_name="market_control",
        null=True,
        blank=True
    )

    asset = models.CharField(
        max_length=20,
        default="BTC/USD"
    )

    direction = models.CharField(
        max_length=10,
        choices=DIRECTION_CHOICES,
        default="AUTO"
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        pair_name = self.pair.symbol if self.pair else self.asset
        return f"{pair_name} - {self.direction}"

    # ==========================================
# PLATFORM CONTROL
# ==========================================

class PlatformControl(models.Model):

    trading_enabled = models.BooleanField(
        default=True
    )

    withdrawals_enabled = models.BooleanField(
        default=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return "Platform Control"