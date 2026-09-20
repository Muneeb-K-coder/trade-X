from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db.models import Sum
from django.contrib import messages
from django.db import transaction as db_transaction

from .models import TradingAccount, Trade, Transaction, MarketControl


# ==========================================
# ADMIN DASHBOARD
# ==========================================

@staff_member_required
def admin_dashboard(request):

    if request.method == "POST":

        transaction_id = request.POST.get("transaction_id")
        action = request.POST.get("action")
        admin_comment = request.POST.get("comment", "").strip()

        try:
            txn = Transaction.objects.get(
                id=transaction_id
            )
        except Transaction.DoesNotExist:

            messages.error(
                request,
                "Transaction not found."
            )

            return redirect("admin_dashboard")

        if txn.status != "PENDING":

            messages.warning(
                request,
                "This transaction has already been processed."
            )

            return redirect("admin_dashboard")

        # ==========================================
        # APPROVE
        # ==========================================

        if action == "approve":

            with db_transaction.atomic():

                account, created = TradingAccount.objects.get_or_create(
                    user=txn.user,
                    defaults={
                        "balance": 0,
                        "balance_pkr": 0,
                        "balance_usd": 0,
                        "credit_score": 100
                    }
                )

                # ------------------------------
                # DEPOSIT
                # ------------------------------

                if txn.transaction_type == "DEPOSIT":

                    if txn.currency == "PKR":
                        account.balance_pkr += txn.amount
                    else:
                        account.balance_usd += txn.amount

                    account.save()

                    txn.status = "APPROVED"
                    txn.comment = admin_comment
                    txn.save()

                    messages.success(
                        request,
                        f"Deposit of {txn.amount} {txn.currency} approved for {txn.user.username}."
                    )

                # ------------------------------
                # WITHDRAW
                # ------------------------------

                elif txn.transaction_type == "WITHDRAW":

                    if txn.currency == "PKR":
                        current_balance = account.balance_pkr
                    else:
                        current_balance = account.balance_usd

                    if txn.amount > current_balance:

                        messages.error(
                            request,
                            f"Insufficient {txn.currency} balance for {txn.user.username}."
                        )

                    else:

                        if txn.currency == "PKR":
                            account.balance_pkr -= txn.amount
                        else:
                            account.balance_usd -= txn.amount

                        account.save()

                        txn.status = "APPROVED"
                        txn.comment = admin_comment
                        txn.save()

                        messages.success(
                            request,
                            f"Withdrawal of {txn.amount} {txn.currency} approved for {txn.user.username}."
                        )

        # ==========================================
        # REJECT
        # ==========================================

        elif action == "reject":

            txn.status = "REJECTED"
            txn.comment = admin_comment
            txn.save()

            messages.success(
                request,
                f"Transaction rejected for {txn.user.username}."
            )

        return redirect("admin_dashboard")

    # ==========================================
    # ADMIN STATISTICS
    # ==========================================

    total_users = User.objects.count()

    total_balance = (
        TradingAccount.objects.aggregate(
            total=Sum("balance")
        )["total"] or 0
    )

    total_trades = Trade.objects.count()

    open_trades = Trade.objects.filter(
        status="OPEN"
    ).count()

    finished_trades = Trade.objects.filter(
        status__in=["WIN", "LOSS"]
    ).count()

    pending_transactions = Transaction.objects.filter(
        status="PENDING"
    ).count()

    approved_transactions = Transaction.objects.filter(
        status="APPROVED"
    ).count()

    rejected_transactions = Transaction.objects.filter(
        status="REJECTED"
    ).count()

    # ==========================================
    # RECENT DATA
    # ==========================================

    recent_users = User.objects.order_by(
        "-date_joined"
    )[:8]

    pending_list = Transaction.objects.select_related(
        "user"
    ).filter(
        status="PENDING"
    ).order_by(
        "-created_at"
    )[:10]

    recent_transactions = Transaction.objects.select_related(
        "user"
    ).order_by(
        "-created_at"
    )[:8]

    recent_trades = Trade.objects.select_related(
        "user"
    ).order_by(
        "-created_at"
    )[:8]

    context = {
        "total_users": total_users,
        "total_balance": total_balance,
        "total_trades": total_trades,
        "open_trades": open_trades,
        "closed_trades": finished_trades,
        "finished_trades": finished_trades,
        "pending_transactions": pending_transactions,
        "approved_transactions": approved_transactions,
        "rejected_transactions": rejected_transactions,
        "recent_users": recent_users,
        "pending_list": pending_list,
        "recent_transactions": recent_transactions,
        "recent_trades": recent_trades,
    }

    return render(
        request,
        "trading/admin_dashboard.html",
        context
    )


# ==========================================
# ADMIN USERS
# ==========================================

@staff_member_required
def admin_users(request):

    users = User.objects.all().order_by(
        "-date_joined"
    )

    search = request.GET.get(
        "search",
        ""
    ).strip()

    if search:

        users = users.filter(
            username__icontains=search
        ) | users.filter(
            email__icontains=search
        )

    user_data = []

    for user in users:

        account = TradingAccount.objects.filter(
            user=user
        ).first()

        trade_count = Trade.objects.filter(
            user=user
        ).count()

        open_trade_count = Trade.objects.filter(
            user=user,
            status="OPEN"
        ).count()

        finished_trade_count = Trade.objects.filter(
            user=user,
            status__in=["WIN", "LOSS"]
        ).count()

        user_data.append({
            "user": user,
            "account": account,
            "trade_count": trade_count,
            "open_trade_count": open_trade_count,
            "finished_trade_count": finished_trade_count,
        })

    return render(
        request,
        "trading/admin_users.html",
        {
            "user_data": user_data,
            "search": search,
        }
    )


# ==========================================
# ADMIN USER DETAIL
# ==========================================

@staff_member_required
def admin_user_detail(request, user_id):

    user = get_object_or_404(
        User,
        id=user_id
    )

    account, created = TradingAccount.objects.get_or_create(
        user=user,
        defaults={
            "balance": 0.00,
            "balance_pkr": 0.00,
            "balance_usd": 0.00,
            "credit_score": 100
        }
    )

    # ==========================================
    # UPDATE CREDIT SCORE
    # ==========================================

    if request.method == "POST":

        credit_score = request.POST.get(
            "credit_score"
        )

        try:

            credit_score = int(credit_score)

            credit_score = max(
                0,
                min(100, credit_score)
            )

            account.credit_score = credit_score
            account.save()

            messages.success(
                request,
                f"Credit Score updated to {credit_score}/100 for {user.username}."
            )

        except (TypeError, ValueError):

            messages.error(
                request,
                "Please enter a valid Credit Score."
            )

        return redirect(
            "admin_user_detail",
            user_id=user.id
        )

    # ==========================================
    # USER TRADES
    # ==========================================

    trades = Trade.objects.filter(
        user=user
    ).order_by(
        "-created_at"
    )

    # ==========================================
    # USER TRANSACTIONS
    # ==========================================

    transactions = Transaction.objects.filter(
        user=user
    ).order_by(
        "-created_at"
    )

    # ==========================================
    # STATISTICS
    # ==========================================

    total_trades = trades.count()

    open_trades = trades.filter(
        status="OPEN"
    ).count()

    finished_trades = trades.filter(
        status__in=["WIN", "LOSS"]
    ).count()

    total_profit_loss = trades.filter(
        status__in=["WIN", "LOSS"]
    ).aggregate(
        total=Sum("profit_loss")
    )["total"] or 0

    # ==========================================
    # RENDER
    # ==========================================

    return render(
        request,
        "trading/admin_user_detail.html",
        {
            "user_obj": user,
            "account": account,
            "trades": trades[:20],
            "transactions": transactions[:20],
            "total_trades": total_trades,
            "open_trades": open_trades,
            "closed_trades": finished_trades,
            "finished_trades": finished_trades,
            "total_profit_loss": total_profit_loss,
        }
    )


# ==========================================
# FREEZE USER
# ==========================================

@staff_member_required
def freeze_user(request, user_id):

    if request.method != "POST":
        return redirect("admin_users")

    user = get_object_or_404(
        User,
        id=user_id
    )

    if user.id == request.user.id:

        messages.error(
            request,
            "You cannot freeze your own admin account."
        )

        return redirect("admin_users")

    user.is_active = False
    user.save()

    messages.success(
        request,
        f"User {user.username} has been frozen."
    )

    return redirect("admin_users")


# ==========================================
# UNFREEZE USER
# ==========================================

@staff_member_required
def unfreeze_user(request, user_id):

    if request.method != "POST":
        return redirect("admin_users")

    user = get_object_or_404(
        User,
        id=user_id
    )

    user.is_active = True
    user.save()

    messages.success(
        request,
        f"User {user.username} has been unfrozen."
    )

    return redirect("admin_users")


# ==========================================
# BAN TRADING
# ==========================================

@staff_member_required
def ban_trading(request, user_id):

    if request.method != "POST":
        return redirect("admin_users")

    user = get_object_or_404(
        User,
        id=user_id
    )

    # Admin cannot ban himself
    if user.id == request.user.id:

        messages.error(
            request,
            "You cannot ban trading on your own admin account."
        )

        return redirect("admin_users")

    account, created = TradingAccount.objects.get_or_create(
        user=user,
        defaults={
            "balance": 0.00,
            "balance_pkr": 0.00,
            "balance_usd": 0.00,
            "credit_score": 100,
            "trading_banned": False,
            "withdrawal_banned": False
        }
    )

    reason = request.POST.get(
        "reason",
        ""
    ).strip()

    # ==========================================
    # SAVE TRADING BAN DIRECTLY
    # ==========================================

    TradingAccount.objects.filter(
        id=account.id
    ).update(
        trading_banned=True,
        trading_ban_reason=reason
    )

    messages.success(
        request,
        f"Trading banned for {user.username}."
    )

    return redirect("admin_users")


# ==========================================
# UNBAN TRADING
# ==========================================

@staff_member_required
def unban_trading(request, user_id):

    if request.method != "POST":
        return redirect("admin_users")

    user = get_object_or_404(
        User,
        id=user_id
    )

    account = TradingAccount.objects.filter(
        user=user
    ).first()

    if account:

        TradingAccount.objects.filter(
            id=account.id
        ).update(
            trading_banned=False,
            trading_ban_reason=""
        )

    messages.success(
        request,
        f"Trading unbanned for {user.username}."
    )

    return redirect("admin_users")


# ==========================================
# BAN WITHDRAWAL
# ==========================================

@staff_member_required
def ban_withdrawal(request, user_id):

    if request.method != "POST":
        return redirect("admin_users")

    user = get_object_or_404(
        User,
        id=user_id
    )

    # Admin cannot ban himself
    if user.id == request.user.id:

        messages.error(
            request,
            "You cannot ban withdrawals on your own admin account."
        )

        return redirect("admin_users")

    account, created = TradingAccount.objects.get_or_create(
        user=user,
        defaults={
            "balance": 0.00,
            "balance_pkr": 0.00,
            "balance_usd": 0.00,
            "credit_score": 100,
            "trading_banned": False,
            "withdrawal_banned": False
        }
    )

    reason = request.POST.get(
        "reason",
        ""
    ).strip()

    TradingAccount.objects.filter(
        id=account.id
    ).update(
        withdrawal_banned=True,
        withdrawal_ban_reason=reason
    )

    messages.success(
        request,
        f"Withdrawals banned for {user.username}."
    )

    return redirect("admin_users")


# ==========================================
# UNBAN WITHDRAWAL
# ==========================================

@staff_member_required
def unban_withdrawal(request, user_id):

    if request.method != "POST":
        return redirect("admin_users")

    user = get_object_or_404(
        User,
        id=user_id
    )

    account = TradingAccount.objects.filter(
        user=user
    ).first()

    if account:

        TradingAccount.objects.filter(
            id=account.id
        ).update(
            withdrawal_banned=False,
            withdrawal_ban_reason=""
        )

    messages.success(
        request,
        f"Withdrawals unbanned for {user.username}."
    )

    return redirect("admin_users")


# ==========================================
# MARKET CONTROL
# ==========================================

@staff_member_required
def market_control(request):

    assets = [
        "BTC/PKR",
        "ETH/PKR",
        "USDT/PKR",
        "XRP/PKR",
        "BNB/PKR",
        "BTS/PKR",
        "BTC/USD",
        "ETH/USD",
        "USDT/USD",
        "BTC/INR",
        "ETH/INR",
    ]

    if request.method == "POST":

        for asset in assets:

            direction = request.POST.get(
                f"direction_{asset}"
            )

            if direction not in [
                "AUTO",
                "UP",
                "DOWN"
            ]:
                continue

            MarketControl.objects.update_or_create(
                asset=asset,
                defaults={
                    "direction": direction
                }
            )

        messages.success(
            request,
            "Demo market direction updated successfully."
        )

        return redirect("market_control")

    controls = []

    for asset in assets:

        control, created = MarketControl.objects.get_or_create(
            asset=asset,
            defaults={
                "direction": "AUTO"
            }
        )

        controls.append(control)

    return render(
        request,
        "trading/market_control.html",
        {
            "controls": controls
        }
    )


# ==========================================
# ADMIN MANUAL TRADE RESULT
# ==========================================

@staff_member_required
def admin_trade_result(request, trade_id, result):

    if request.method != "POST":
        return redirect("admin_dashboard")

    trade = get_object_or_404(
        Trade,
        id=trade_id
    )

    # Sirf OPEN trade ka result set hoga
    if trade.status != "OPEN":

        messages.warning(
            request,
            "This trade has already been processed."
        )

        return redirect("admin_dashboard")

    if result not in ["WIN", "LOSS"]:

        messages.error(
            request,
            "Invalid trade result."
        )

        return redirect("admin_dashboard")

    with db_transaction.atomic():

        account, created = TradingAccount.objects.get_or_create(
            user=trade.user,
            defaults={
                "balance": 0.00,
                "balance_pkr": 0.00,
                "balance_usd": 0.00,
                "credit_score": 100
            }
        )

        # ==========================================
        # WIN
        # ==========================================

        if result == "WIN":

            payout_rates = {
                60:  "0.30",
                120: "0.30",
                180: "0.60",
                240: "0.60"
            }

            payout_rate = Decimal(
                payout_rates.get(
                    trade.duration_seconds,
                    "0.30"
                )
            )

            profit = trade.amount * payout_rate

            trade.profit_loss = profit
            trade.status = "WIN"

            if trade.currency == "PKR":

                account.balance_pkr += (
                    trade.amount + profit
                )

            else:

                account.balance_usd += (
                    trade.amount + profit
                )

            account.save()

        # ==========================================
        # LOSS
        # ==========================================

        elif result == "LOSS":

            trade.profit_loss = -trade.amount
            trade.status = "LOSS"

            # Trade amount pehle hi balance se deduct ho chuka hai.
            # Isliye LOSS par balance mein kuch add nahi hoga.

        trade.save()

    messages.success(
        request,
        f"Trade for {trade.user.username} marked as {result}."
    )

    return redirect("admin_dashboard")