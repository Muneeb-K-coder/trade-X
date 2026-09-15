from django.urls import path
from . import views
from .admin_views import (
    admin_users,
    admin_user_detail,
    freeze_user,
    unfreeze_user,
    ban_trading,
    unban_trading,
    ban_withdrawal,
    unban_withdrawal,
    market_control,
)


urlpatterns = [

    # ==========================================
    # TRADING
    # ==========================================

    path(
        "buy/",
        views.buy_trade,
        name="buy_trade"
    ),

    path(
        "sell/",
        views.sell_trade,
        name="sell_trade"
    ),

    path(
        "close/<int:trade_id>/",
        views.close_trade,
        name="close_trade"
    ),

    path(
        "settle/<int:trade_id>/",
        views.settle_trade,
        name="settle_trade"
    ),

    path(
        "settle-expired/",
        views.settle_expired_trades,
        name="settle_expired_trades"
    ),


    # ==========================================
    # DEPOSIT / WITHDRAW
    # ==========================================

    path(
        "deposit/",
        views.deposit,
        name="deposit"
    ),

    path(
        "withdraw/",
        views.withdraw,
        name="withdraw"
    ),


    # ==========================================
    # HISTORY
    # ==========================================

    path(
        "history/",
        views.trade_history,
        name="trade_history"
    ),

    path(
        "transactions/",
        views.transaction_history,
        name="transaction_history"
    ),


    # ==========================================
    # MY ACCOUNT
    # ==========================================

    path(
        "account/",
        views.my_account,
        name="my_account"
    ),


    # ==========================================
    # CUSTOM ADMIN USERS
    # ==========================================

    path(
        "admin-users/",
        admin_users,
        name="admin_users"
    ),

    path(
        "admin-users/<int:user_id>/",
        admin_user_detail,
        name="admin_user_detail"
    ),


    # ==========================================
    # FREEZE / UNFREEZE USER
    # ==========================================

    path(
        "admin-users/<int:user_id>/freeze/",
        freeze_user,
        name="freeze_user"
    ),

    path(
        "admin-users/<int:user_id>/unfreeze/",
        unfreeze_user,
        name="unfreeze_user"
    ),


    # ==========================================
    # TRADING BAN / UNBAN
    # ==========================================

    path(
        "admin-users/<int:user_id>/ban-trading/",
        ban_trading,
        name="ban_trading"
    ),

    path(
        "admin-users/<int:user_id>/unban-trading/",
        unban_trading,
        name="unban_trading"
    ),


    # ==========================================
    # WITHDRAWAL BAN / UNBAN
    # ==========================================

    path(
        "admin-users/<int:user_id>/ban-withdrawal/",
        ban_withdrawal,
        name="ban_withdrawal"
    ),

    path(
        "admin-users/<int:user_id>/unban-withdrawal/",
        unban_withdrawal,
        name="unban_withdrawal"
    ),


    # ==========================================
    # MARKET CONTROL
    # ==========================================

    path(
        "market-control/",
        market_control,
        name="market_control"
    ),


    # ==========================================
    # MARKET DIRECTION API
    # ==========================================

    path(
        "market-direction/",
        views.market_direction,
        name="market_direction"
    ),
]