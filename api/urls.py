from django.urls import path
from .views import (
    # Auth views
    register_view,
    login_view,
    logout_view,
    get_profile_view,
    update_profile_view,
    change_password_view,
    password_reset_request_view,
    password_reset_confirm_view,
    verify_token_view,
    
    # Batch views
    batch_list_create_view,
    batch_detail_view,
    
    # Student views
    student_list_create_view,
    student_detail_view,
    student_upload_profile_pic_view,
    
    # Attendance views
    attendance_list_create_view,
    attendance_detail_view,
    student_attendance_report_view,
    
    # Fee views
    fee_payment_list_create_view,
    fee_payment_detail_view,
    student_fee_status_view,
    batch_fee_overview_view,
    fee_analytics_view,
    
    # Test views
    test_list_create_view,
    test_detail_view,
    test_marks_bulk_create_view,
    test_marks_list_view,
    student_test_report_view,
    
    # Dashboard views
    dashboard_overview_view,
    dashboard_analytics_view,
)

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', register_view, name='register'),
    path('auth/login/', login_view, name='login'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/profile/', get_profile_view, name='get-profile'),
    path('auth/profile/update/', update_profile_view, name='update-profile'),
    path('auth/change-password/', change_password_view, name='change-password'),
    path('auth/password-reset/request/', password_reset_request_view, name='password-reset-request'),
    path('auth/password-reset/confirm/', password_reset_confirm_view, name='password-reset-confirm'),
    path('auth/verify-token/', verify_token_view, name='verify-token'),
    
    # Batch endpoints
    path('batches/', batch_list_create_view, name='batch-list-create'),
    path('batches/<uuid:batch_id>/', batch_detail_view, name='batch-detail'),
    
    # Student endpoints
    path('students/', student_list_create_view, name='student-list-create'),
    path('students/<uuid:student_id>/', student_detail_view, name='student-detail'),
    path('students/<uuid:student_id>/upload-profile-pic/', student_upload_profile_pic_view, name='student-upload-profile-pic'),
    
    # Attendance endpoints
    path('attendance/', attendance_list_create_view, name='attendance-list-create'),
    path('attendance/<uuid:attendance_id>/', attendance_detail_view, name='attendance-detail'),
    path('attendance/student/<uuid:student_id>/report/', student_attendance_report_view, name='student-attendance-report'),
    
    # Fee endpoints
    path('fees/', fee_payment_list_create_view, name='fee-payment-list-create'),
    path('fees/<uuid:payment_id>/', fee_payment_detail_view, name='fee-payment-detail'),
    path('fees/student/<uuid:student_id>/status/', student_fee_status_view, name='student-fee-status'),
    path('fees/batch/<uuid:batch_id>/overview/', batch_fee_overview_view, name='batch-fee-overview'),
    path('fees/analytics/', fee_analytics_view, name='fee-analytics'),
    
    # Test endpoints
    path('tests/', test_list_create_view, name='test-list-create'),
    path('tests/<uuid:test_id>/', test_detail_view, name='test-detail'),
    path('tests/<uuid:test_id>/marks/bulk/', test_marks_bulk_create_view, name='test-marks-bulk-create'),
    path('tests/<uuid:test_id>/marks/', test_marks_list_view, name='test-marks-list'),
    path('tests/student/<uuid:student_id>/report/', student_test_report_view, name='student-test-report'),
    
    # Dashboard endpoints
    path('dashboard/overview/', dashboard_overview_view, name='dashboard-overview'),
    path('dashboard/analytics/', dashboard_analytics_view, name='dashboard-analytics'),
]