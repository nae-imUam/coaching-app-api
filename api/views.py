# api/views.py  — re-exports every view so urls.py can import from one place

from .views_sub.auth_views import (
    register_view, login_view, logout_view,
    get_profile_view, update_profile_view, change_password_view,
    password_reset_request_view, password_reset_confirm_view, verify_token_view,
)
from .views_sub.batch_views import (
    batch_list_create_view, batch_detail_view,
)
from .views_sub.student_views import (
    student_list_create_view, student_detail_view,
    student_upload_profile_pic_view,
    student_full_profile_view,
)
from .views_sub.attendance_views import (
    attendance_list_create_view, attendance_detail_view,
    student_attendance_report_view, class_attendance_report_view,
)
from .views_sub.fee_views import (
    fee_payment_list_create_view, fee_payment_detail_view,
    student_fee_status_view, batch_fee_overview_view, fee_analytics_view,
)
from .views_sub.test_views import (
    test_list_create_view, test_detail_view,
    test_marks_bulk_create_view, test_marks_list_view, student_test_report_view,
)
from .views_sub.dashboard_views import (
    dashboard_overview_view, dashboard_analytics_view,
)