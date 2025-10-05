from django.urls import path
from django.conf import settings
from .views import *
from . import views

urlpatterns = [
    path(
        "register",
        RegisterView.as_view(),
        name="sign_up"
    ),
    path(
        "login",
        LoginView.as_view(),
        name="sign_in"
    ),
    path(
        "otp",
        OTPView.as_view(),
        name="forgot_password_request",
    ),
    path(
        "reset-password",
        ForgotPasswordVerifyView.as_view(),
        name="forgot_password_verify",
    ),
    path(
        "user-profile",
        UserProfileView.as_view(),
        name="get_user_profile"
    ),
    path("session",SaveSessionView.as_view(),name="session"),
    path("user-data",UserDataView.as_view(),name="user_data"),
    path("user-session-data",GetUserBySessionId.as_view(),name="GetUserBySessionId"),
    path("web-appointment-form", WebAppointmentFormView.as_view(),name="web-appointment-form"),
    path("index",views.IndexView),
    path("google-redirext",views.GoogleApiView)
    # path("index",IndexView.as_view(),name = "index-page")
]
