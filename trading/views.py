from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import (
    Trade,
    TradingAccount,
    Transaction,
    MarketControl,
    PlatformControl,
)


# ==========================================
# SETTINGS
# ==========================================

ASSETS = {
    "BTC/PKR": Decimal("14500000"),
    "ETH/PKR": Decimal("500000"),
    "USDT/PKR": Decimal("280"),
    "BNB/PKR": Decimal("260000"),
    "SOL/PKR": Decimal("65000"),
    "XRP/PKR": Decimal("750"),
    "ADA/PKR": Decimal("220"),
    "DOGE/PKR": Decimal("65"),
    "TRX/PKR": Decimal("100"),
    "LTC/PKR": Decimal("30000"),
    "DOT/PKR": Decimal("1100"),
    "AVAX/PKR": Decimal("7500"),
    "BTS/PKR": Decimal("1600"),
}


# ==========================================
# BINARY DURATION / PAYOUT
# ==========================================

PAYOUT_RATES = {
    60: Decimal("30.00"),
    120: Decimal("30.00"),
    180: Decimal("60.00"),
    240: Decimal("60.00"),
}


# ==========================================
# CURRENCY HELPERS
# ==========================================

def get_selected_currency(request):
    currency = request.POST.get(
        "currency",
        "USD"
    ).upper()

    if currency not in ["USD", "PKR"]:
        currency = "USD"

    return currency


def get_balance(account, currency):
    if currency == "PKR":
        return account.balance_pkr

    return account.balance_usd


def set_balance(account, currency, amount):
    if currency == "PKR":
        account.balance_pkr = amount
    else:
        account.balance_usd = amount


def get_currency_symbol(currency):
    if currency == "PKR":
        return "₨"

    return "$"


# ==========================================
# PAYOUT
# ==========================================

def get_payout_rate(duration_seconds):
    return PAYOUT_RATES.get(
        duration_seconds,
        Decimal("30.00")
    )


# ==========================================
# GET DEMO PRICE
# ==========================================

def get_demo_price(request, asset=None):

    if asset is None:
        asset = request.POST.get(
            "asset",
            "BTC/PKR"
        )

    default_price = ASSETS.get(
        asset,
        Decimal("14500000")
    )

    try:

        price = Decimal(
            request.POST.get(
                "current_price",
                str(default_price)
            )
        )

    except (InvalidOperation, TypeError):

        price = default_price

    if price <= 0:
        price = default_price

    return price.quantize(
        Decimal("0.0001")
    )


# ==========================================
# CREATE BINARY TRADE
# ==========================================

@login_required
def create_binary_trade(request, side):

    if request.method != "POST":
        return redirect("dashboard")

    account, created = TradingAccount.objects.get_or_create(
        user=request.user,
        defaults={
            "balance": Decimal("0.00"),
            "balance_pkr": Decimal("0.00"),
            "balance_usd": Decimal("0.00"),
        }
    )

    # ==========================================
    # CURRENCY
    # ==========================================

    currency = get_selected_currency(request)
    currency_symbol = get_currency_symbol(currency)

    # ==========================================
    # GLOBAL TRADING CONTROL
    # ==========================================

    platform_control, _ = PlatformControl.objects.get_or_create(
        id=1,
        defaults={
            "trading_enabled": True,
            "withdrawals_enabled": True,
        }
    )

    if not platform_control.trading_enabled:

        messages.error(
            request,
            "Trading is currently disabled by admin."
        )

        return redirect("dashboard")

    # ==========================================
    # TRADING BAN CHECK
    # ==========================================

    if account.trading_banned:

        reason = (
            account.trading_ban_reason or ""
        ).strip()

        if reason:

            messages.error(
                request,
                f"Trading is currently banned. Reason: {reason}"
            )

        else:

            messages.error(
                request,
                "Trading is currently banned for your account."
            )

        return redirect("dashboard")

    # ==========================================
    # ASSET
    # ==========================================

    asset = request.POST.get(
        "asset",
        "BTC/PKR"
    )

    if asset not in ASSETS:

        messages.error(
            request,
            "Invalid asset."
        )

        return redirect("dashboard")

    # ==========================================
    # AMOUNT
    # ==========================================

    try:

        amount = Decimal(
            request.POST.get(
                "amount",
                "0"
            )
        )

    except (InvalidOperation, TypeError):

        amount = Decimal("0")

    if amount <= 0:

        messages.error(
            request,
            "Enter a valid trade amount."
        )

        return redirect("dashboard")

    current_balance = get_balance(
        account,
        currency
    )

    if amount > current_balance:

        messages.error(
            request,
            f"Insufficient {currency} balance."
        )

        return redirect("dashboard")

    # ==========================================
    # DURATION
    # ==========================================

    try:

        duration_seconds = int(
            request.POST.get(
                "duration_seconds",
                "60"
            )
        )

    except (ValueError, TypeError):

        duration_seconds = 60

    if duration_seconds not in PAYOUT_RATES:

        messages.error(
            request,
            "Invalid trade duration."
        )

        return redirect("dashboard")

    # ==========================================
    # PAYOUT
    # ==========================================

    payout_percent = get_payout_rate(
        duration_seconds
    )

    # ==========================================
    # ENTRY PRICE
    # ==========================================

    entry_price = get_demo_price(request)

    # ==========================================
    # CREATE TRADE
    # ==========================================

    Trade.objects.create(
        user=request.user,
        asset=asset,
        side=side,
        currency=currency,
        amount=amount,
        price=entry_price,
        duration_seconds=duration_seconds,
        payout_percent=payout_percent,
        status="OPEN",
        profit_loss=Decimal("0.00")
    )

    # ==========================================
    # DEDUCT STAKE
    # ==========================================

    set_balance(
        account,
        currency,
        current_balance - amount
    )

    account.save()

    # ==========================================
    # POTENTIAL PROFIT
    # ==========================================

    potential_profit = (
        amount
        * payout_percent
        / Decimal("100")
    ).quantize(
        Decimal("0.01")
    )

    potential_return = (
        amount
        + potential_profit
    ).quantize(
        Decimal("0.01")
    )

    if side == "BUY":
        direction = "BUY / UP"
    else:
        direction = "SELL / DOWN"

    messages.success(
        request,
        f"{asset} | {direction} | "
        f"{currency} | "
        f"{duration_seconds}s | "
        f"{payout_percent}% payout | "
        f"Potential Profit: {currency_symbol}{potential_profit} | "
        f"Potential Return: {currency_symbol}{potential_return}"
    )

    return redirect("dashboard")


# ==========================================
# BUY / UP
# ==========================================

@login_required
def buy_trade(request):

    return create_binary_trade(
        request,
        "BUY"
    )


# ==========================================
# SELL / DOWN
# ==========================================

@login_required
def sell_trade(request):

    return create_binary_trade(
        request,
        "SELL"
    )


# ==========================================
# SETTLE BINARY TRADE
# ==========================================

@login_required
def settle_trade(request, trade_id):

    if request.method != "POST":

        return redirect("dashboard")

    try:

        with db_transaction.atomic():

            trade = Trade.objects.select_for_update().get(
                id=trade_id,
                user=request.user,
                status="OPEN"
            )

            # ==========================================
            # CHECK EXPIRY
            # ==========================================

            expiry_time = (
                trade.created_at
                + timedelta(
                    seconds=trade.duration_seconds
                )
            )

            current_time = timezone.now()

            if current_time < expiry_time:

                remaining = int(
                    (
                        expiry_time
                        - current_time
                    ).total_seconds()
                )

                if remaining < 1:
                    remaining = 1

                messages.error(
                    request,
                    f"Trade has not expired yet. "
                    f"Wait {remaining} seconds."
                )

                return redirect("dashboard")

            # ==========================================
            # EXPIRY PRICE
            # ==========================================

            expiry_price = get_demo_price(
                request,
                trade.asset
            )

            # ==========================================
            # ADMIN MARKET CONTROL
            # ==========================================

            market_control = MarketControl.objects.filter(
                asset=trade.asset
            ).first()

            if market_control:

                market_direction = (
                    market_control.direction
                )

            else:

                market_direction = "AUTO"

            # ==========================================
            # BINARY RESULT
            # ==========================================

            if market_direction == "UP":

                if trade.side == "BUY":

                    result = "WIN"

                else:

                    result = "LOSS"

            elif market_direction == "DOWN":

                if trade.side == "SELL":

                    result = "WIN"

                else:

                    result = "LOSS"

            else:

                # ==========================================
                # AUTO MODE
                # ==========================================

                if trade.side == "BUY":

                    if expiry_price > trade.price:

                        result = "WIN"

                    else:

                        result = "LOSS"

                else:

                    if expiry_price < trade.price:

                        result = "WIN"

                    else:

                        result = "LOSS"

            # ==========================================
            # ACCOUNT
            # ==========================================

            account, created = TradingAccount.objects.get_or_create(
                user=request.user,
                defaults={
                    "balance": Decimal("0.00"),
                    "balance_pkr": Decimal("0.00"),
                    "balance_usd": Decimal("0.00"),
                }
            )

            currency = trade.currency or "USD"

            currency_symbol = get_currency_symbol(
                currency
            )

            # ==========================================
            # WIN
            # ==========================================

            if result == "WIN":

                profit = (
                    trade.amount
                    * trade.payout_percent
                    / Decimal("100")
                ).quantize(
                    Decimal("0.01")
                )

                trade.profit_loss = profit

                current_balance = get_balance(
                    account,
                    currency
                )

                set_balance(
                    account,
                    currency,
                    current_balance
                    + trade.amount
                    + profit
                )

                messages.success(
                    request,
                    f"{trade.asset} | "
                    f"{trade.side} | "
                    f"{currency} | WIN | "
                    f"+{currency_symbol}{profit} profit | "
                    f"Market: {market_direction} | "
                    f"Entry: {trade.price} | "
                    f"Expiry: {expiry_price}"
                )

            # ==========================================
            # LOSS
            # ==========================================

            else:

                trade.profit_loss = -trade.amount

                messages.error(
                    request,
                    f"{trade.asset} | "
                    f"{trade.side} | "
                    f"{currency} | LOSS | "
                    f"-{currency_symbol}{trade.amount} | "
                    f"Market: {market_direction} | "
                    f"Entry: {trade.price} | "
                    f"Expiry: {expiry_price}"
                )

            # ==========================================
            # SAVE RESULT
            # ==========================================

            trade.status = result

            trade.closing_price = expiry_price

            trade.closed_at = timezone.now()

            trade.save()

            account.save()

            return result

    except Trade.DoesNotExist:

        messages.error(
            request,
            "Open trade not found or already settled."
        )

        return redirect("dashboard")


# ==========================================
# AUTO SETTLE EXPIRED TRADES
# ==========================================

@login_required
def settle_expired_trades(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "message": "POST request required."
            },
            status=405
        )

    now = timezone.now()

    open_trades = Trade.objects.filter(
        user=request.user,
        status="OPEN"
    )

    settled = 0

    for trade in open_trades:

        expiry_time = (
            trade.created_at
            + timedelta(
                seconds=trade.duration_seconds
            )
        )

        if now >= expiry_time:

            try:

                result = settle_trade(
                    request,
                    trade.id
                )

                if result in ["WIN", "LOSS"]:

                    settled += 1

            except Exception:

                continue

    return JsonResponse(
        {
            "success": True,
            "settled": settled
        }
    )


# ==========================================
# OLD CLOSE URL
# ==========================================

@login_required
def close_trade(request, trade_id):

    if request.method != "POST":

        return redirect("dashboard")

    try:

        trade = Trade.objects.get(
            id=trade_id,
            user=request.user,
            status="OPEN"
        )

    except Trade.DoesNotExist:

        messages.error(
            request,
            "Open trade not found."
        )

        return redirect("dashboard")

    expiry_time = (
        trade.created_at
        + timedelta(
            seconds=trade.duration_seconds
        )
    )

    if timezone.now() < expiry_time:

        remaining = int(
            (
                expiry_time
                - timezone.now()
            ).total_seconds()
        )

        if remaining < 1:
            remaining = 1

        messages.error(
            request,
            f"Trade is still running. "
            f"Wait {remaining} seconds."
        )

        return redirect("dashboard")

    return settle_trade(
        request,
        trade.id
    )


# ==========================================
# DEPOSIT
# ==========================================

@login_required
def deposit(request):

    if request.method == "POST":

        currency = get_selected_currency(request)
        currency_symbol = get_currency_symbol(
            currency
        )

        try:

            amount = Decimal(
                request.POST.get(
                    "amount",
                    "0"
                )
            )

        except (InvalidOperation, TypeError):

            amount = Decimal("0")

        if amount <= 0:

            messages.error(
                request,
                "Enter a valid deposit amount."
            )

            return redirect("deposit")

        Transaction.objects.create(
            user=request.user,
            transaction_type="DEPOSIT",
            amount=amount,
            currency=currency,
            status="PENDING"
        )

        messages.success(
            request,
            f"Deposit request of "
            f"{currency_symbol}{amount} "
            f"{currency} submitted for admin approval."
        )

        return redirect("dashboard")

    return render(
        request,
        "trading/deposit.html"
    )


# ==========================================
# WITHDRAW
# ==========================================

@login_required
def withdraw(request):

    account, created = TradingAccount.objects.get_or_create(
        user=request.user,
        defaults={
            "balance": Decimal("0.00"),
            "balance_pkr": Decimal("0.00"),
            "balance_usd": Decimal("0.00"),
        }
    )

    # ==========================================
    # POST REQUEST
    # ==========================================

    if request.method == "POST":

        account.refresh_from_db()

        currency = get_selected_currency(request)
        currency_symbol = get_currency_symbol(
            currency
        )

        current_balance = get_balance(
            account,
            currency
        )

        # ==========================================
        # GLOBAL WITHDRAWAL CONTROL
        # ==========================================

        platform_control, _ = PlatformControl.objects.get_or_create(
            id=1,
            defaults={
                "trading_enabled": True,
                "withdrawals_enabled": True,
            }
        )

        if not platform_control.withdrawals_enabled:

            messages.error(
                request,
                "Withdrawals are currently disabled by admin."
            )

            return redirect("withdraw")

        # ==========================================
        # WITHDRAWAL BAN CHECK
        # ==========================================

        if account.withdrawal_banned:

            reason = (
                account.withdrawal_ban_reason or ""
            ).strip()

            if reason:

                messages.error(
                    request,
                    f"Withdrawals are currently banned. Reason: {reason}"
                )

            else:

                messages.error(
                    request,
                    "Withdrawals are currently banned for your account."
                )

            return redirect("withdraw")

        # ==========================================
        # AMOUNT
        # ==========================================

        try:

            amount = Decimal(
                request.POST.get(
                    "amount",
                    "0"
                )
            )

        except (InvalidOperation, TypeError):

            amount = Decimal("0")

        if amount <= 0:

            messages.error(
                request,
                "Enter a valid withdrawal amount."
            )

            return redirect("withdraw")

        if amount > current_balance:

            messages.error(
                request,
                f"Insufficient {currency} balance."
            )

            return redirect("withdraw")

        # ==========================================
        # WITHDRAWAL ACCOUNT DETAILS
        # ==========================================

        account_title = request.POST.get(
            "account_title",
            ""
        ).strip()

        account_holder_name = request.POST.get(
            "account_holder_name",
            ""
        ).strip()

        account_number = request.POST.get(
            "account_number",
            ""
        ).strip()

        # ==========================================
        # REQUIRED ACCOUNT NAME
        # ==========================================

        if not account_title:

            messages.error(
                request,
                "Please enter account name."
            )

            return redirect("withdraw")

        # ==========================================
        # REQUIRED HOLDER NAME
        # ==========================================

        if not account_holder_name:

            messages.error(
                request,
                "Please enter account holder name."
            )

            return redirect("withdraw")

        # ==========================================
        # REQUIRED ACCOUNT NUMBER
        # ==========================================

        if not account_number:

            messages.error(
                request,
                "Please enter account number."
            )

            return redirect("withdraw")

        # ==========================================
        # CREATE WITHDRAWAL REQUEST
        # ==========================================

        Transaction.objects.create(
            user=request.user,
            transaction_type="WITHDRAW",
            amount=amount,
            currency=currency,
            status="PENDING",
            account_title=account_title,
            account_holder_name=account_holder_name,
            account_number=account_number
        )

        messages.success(
            request,
            f"Withdrawal request of "
            f"{currency_symbol}{amount} "
            f"{currency} submitted for admin approval."
        )

        return redirect("dashboard")

    # ==========================================
    # GET REQUEST
    # SHOW WITHDRAW PAGE
    # ==========================================

    return render(
        request,
        "trading/withdraw.html"
    )


# ==========================================
# TRADE HISTORY
# ==========================================

@login_required
def trade_history(request):

    trades = Trade.objects.filter(
        user=request.user
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "trading/trade_history.html",
        {
            "trades": trades
        }
    )


# ==========================================
# TRANSACTION HISTORY
# ==========================================

@login_required
def transaction_history(request):

    transactions = Transaction.objects.filter(
        user=request.user
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "trading/transaction_history.html",
        {
            "transactions": transactions
        }
    )


# ==========================================
# MARKET DIRECTION
# ==========================================

@login_required
def market_direction(request):

    directions = dict(
        MarketControl.objects.values_list(
            "asset",
            "direction"
        )
    )

    for asset in ASSETS:

        if asset not in directions:

            directions[asset] = "AUTO"

    return JsonResponse(
        directions
    )


# ==========================================
# MY ACCOUNT
# ==========================================

@login_required
def my_account(request):

    account, created = TradingAccount.objects.get_or_create(
        user=request.user,
        defaults={
            "balance": Decimal("0.00"),
            "balance_pkr": Decimal("0.00"),
            "balance_usd": Decimal("0.00"),
        }
    )

    trades = Trade.objects.filter(
        user=request.user
    )

    total_trades = trades.count()

    open_trades = trades.filter(
        status="OPEN"
    ).count()

    win_trades = trades.filter(
        status="WIN"
    ).count()

    loss_trades = trades.filter(
        status="LOSS"
    ).count()

    total_profit_loss = sum(
        (
            trade.profit_loss
            for trade in trades
        ),
        Decimal("0.00")
    )

    total_profit_loss = Decimal(
        total_profit_loss
    ).quantize(
        Decimal("0.01")
    )

    return render(
        request,
        "trading/my_account.html",
        {
            "account": account,
            "user_obj": request.user,
            "total_trades": total_trades,
            "open_trades": open_trades,
            "win_trades": win_trades,
            "loss_trades": loss_trades,
            "total_profit_loss": total_profit_loss,
        }
    )