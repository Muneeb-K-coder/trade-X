from django.contrib import admin

from .models import (
    TradingPair,
    TradingAccount,
    Trade,
    Transaction,
    MarketControl,
)


# ==========================================
# TRADING PAIR ADMIN
# ==========================================

@admin.register(TradingPair)
class TradingPairAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "symbol",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
        "symbol",
    )


# ==========================================
# TRADING ACCOUNT ADMIN
# ==========================================

@admin.register(TradingAccount)
class TradingAccountAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "balance",
        "credit_score",
        "trading_banned",
        "withdrawal_banned",
        "created_at",
    )

    list_filter = (
        "trading_banned",
        "withdrawal_banned",
    )

    search_fields = (
        "user__username",
        "user__email",
    )


# ==========================================
# TRADE ADMIN
# ==========================================
# ==========================================
# TRADE ADMIN
# ==========================================

@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "asset",
        "side",
        "amount",
        "duration_seconds",
        "price",
        "closing_price",
        "status",
        "profit_loss",
        "created_at",
        "closed_at",
    )

    list_filter = (
        "side",
        "status",
        "asset",
        "duration_seconds",
    )

    search_fields = (
        "user__username",
        "user__email",
        "asset",
    )

    readonly_fields = (
        "user",
        "asset",
        "side",
        "amount",
        "duration_seconds",
        "price",
        "closing_price",
        "status",
        "profit_loss",
        "created_at",
        "closed_at",
    )

    ordering = (
        "-created_at",
    )

    list_per_page = 50
    class Media:
        js = ("admin/js/trade_auto_refresh.js",)
# ==========================================
# TRANSACTION ADMIN
# ==========================================

# ==========================================
# TRANSACTION ADMIN
# ==========================================

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "transaction_type",
        "amount",
        "account_title",
        "account_holder_name",
        "account_number",
        "status",
        "created_at",
    )

    list_filter = (
        "transaction_type",
        "status",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "account_title",
        "account_holder_name",
        "account_number",
    )

    readonly_fields = (
        "user",
        "transaction_type",
        "amount",
        "account_title",
        "account_holder_name",
        "account_number",
        "created_at",
    )

    ordering = (
        "-created_at",
    )
# ==========================================
# MARKET CONTROL ADMIN
# ==========================================

@admin.register(MarketControl)
class MarketControlAdmin(admin.ModelAdmin):

    list_display = (
        "pair",
        "direction",
        "updated_at",
    )

    list_filter = (
        "direction",
    )

    search_fields = (
        "pair__name",
        "pair__symbol",
    )