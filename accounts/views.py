from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

from trading.models import TradingAccount, Trade, TradingPair


def home(request):
    return render(request, "accounts/home.html")


def signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("signup")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        TradingAccount.objects.create(
            user=user,
            balance=0.00
        )

        messages.success(
            request,
            "Account created successfully!"
        )

        return redirect("login")

    return render(request, "accounts/signup.html")


def login_view(request):
    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect("dashboard")

        messages.error(
            request,
            "Invalid username or password."
        )

    return render(request, "accounts/login.html")


@login_required
def logout_view(request):

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect("login")


@login_required
def dashboard(request):

    # ==========================================
    # USER TRADING ACCOUNT
    # ==========================================

    account, created = TradingAccount.objects.get_or_create(
        user=request.user,
        defaults={
            "balance": 0.00
        }
    )

    # ==========================================
    # ACTIVE TRADING PAIRS
    # ==========================================

    pairs = TradingPair.objects.filter(
        is_active=True
    ).order_by("name")

    # ==========================================
    # ALL USER TRADES
    # ==========================================

    trades = Trade.objects.filter(
        user=request.user
    ).order_by("-created_at")

    # ==========================================
    # OPEN TRADES
    # ==========================================

    open_positions = trades.filter(
        status="OPEN"
    )

    # ==========================================
    # TOTAL TRADES
    # ==========================================

    total_trades = trades.count()

    # ==========================================
    # OPEN TRADES COUNT
    # ==========================================

    open_trades = trades.filter(
        status="OPEN"
    ).count()

    # ==========================================
    # WIN TRADES
    # ==========================================

    win_trades = trades.filter(
        status="WIN"
    ).count()

    # ==========================================
    # LOSS TRADES
    # ==========================================

    loss_trades = trades.filter(
        status="LOSS"
    ).count()

    # ==========================================
    # COMPLETED TRADES
    # ==========================================

    closed_trades = trades.filter(
        status__in=[
            "WIN",
            "LOSS"
        ]
    )

    # ==========================================
    # TOTAL PROFIT / LOSS
    # ==========================================

    total_profit_loss = trades.filter(
        status__in=[
            "WIN",
            "LOSS"
        ]
    ).aggregate(
        total=Sum("profit_loss")
    )["total"] or 0

    # ==========================================
    # DEMO ASSET PRICES
    # ==========================================

    assets = {
        "BTC/USD": "50000.00",
        "ETH/USD": "3000.00",
        "GOLD/USD": "2500.00",
        "EUR/USD": "1.0800",
    }

    # ==========================================
    # DASHBOARD
    # ==========================================

    return render(
        request,
        "accounts/dashboard.html",
        {
            "account": account,

            # TRADING PAIRS
            "pairs": pairs,

            # ALL TRADES
            "trades": trades,

            # OPEN TRADES
            "open_positions": open_positions,

            # STATS
            "total_trades": total_trades,
            "open_trades": open_trades,
            "win_trades": win_trades,
            "loss_trades": loss_trades,

            # COMPLETED TRADES
            "closed_trades": closed_trades,

            # TOTAL PROFIT / LOSS
            "total_profit_loss": total_profit_loss,

            # ASSET PRICES
            "assets": assets,
        }
    )