from django.urls import path
from .views import *
from . import views

urlpatterns = [
    path('gerar_relatorio_od/', RelatorioView.as_view(), name='gerar_relatorio_od'), # devolutiva pdf observação direta 
    path('gerar_relatorio_od_dois/', RelatorioViewDois.as_view(), name='gerar_relatorio_od_dois'), # devolutiva pdf observação direta 2
    path('gerar_relatorio_ed/', RelatorioViewEd.as_view(), name='gerar_relatorio_ed'), # devolutiva pdf entrevista do diretor    
    path('gerar_relatorio_ep/', RelatorioViewEp.as_view(), name='gerar_relatorio_ep'), # devolutiva pdf entrevista do professor    
    ]