from django.urls import path
from . import views

app_name = "reviews"

urlpatterns = [
    path("product/<uuid:product_id>/add/", views.AddReviewView.as_view(), name="add"),
    path("product/<uuid:product_id>/ask/", views.AskQuestionView.as_view(), name="ask"),
]
