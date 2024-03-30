from django.urls import path
from . import views
from . import pivot_views

urlpatterns = [
    path('bookkeeping/', views.index, name='index'),
    path('get_data/', views.get_data, name='get_data'),
    path('bookkeeping/list_files_and_folders/', views.list_files_and_folders, name='list_files_and_folders'),
    path('pivot_table/', pivot_views.pivot_table, name='pivot_table'),
    path('bookkeeping/check_search_library/', views.check_search_library, name='check_search_library'),  
]
