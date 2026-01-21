from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg, F, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from ..models import Student, Batch, Attendance, AttendanceRecord, FeePayment, Test, TestMark


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_overview_view(request):
    """
    Get dashboard overview statistics
    GET /api/dashboard/overview/
    Headers: Authorization: Bearer <access_token>
    """
    user = request.user
    
    # Basic counts
    total_students = Student.objects.filter(user=user).count()
    total_batches = Batch.objects.filter(user=user).count()
    total_tests = Test.objects.filter(user=user).count()
    
    # Fee statistics
    students = Student.objects.filter(user=user)
    total_expected_fees = students.aggregate(total=Sum('total_fees'))['total'] or Decimal('0.00')
    total_collected_fees = students.aggregate(total=Sum('fees_paid'))['total'] or Decimal('0.00')
    pending_fees = total_expected_fees - total_collected_fees
    
    # Today's attendance
    today = timezone.now().date()
    today_attendance = Attendance.objects.filter(user=user, date=today)
    present_today = AttendanceRecord.objects.filter(
        attendance__in=today_attendance,
        status='present'
    ).count()
    
    # Fee defaulters
    defaulters = students.filter(total_fees__gt=F('fees_paid')).values(
        'id', 'name', 'roll', 'batch__name', 'total_fees', 'fees_paid'
    )[:10]  # Top 10 defaulters
    
    defaulters_list = []
    for student in defaulters:
        defaulters_list.append({
            'id': str(student['id']),
            'name': student['name'],
            'roll': student['roll'],
            'batch': student['batch__name'],
            'due_amount': float(student['total_fees']) - float(student['fees_paid'])
        })
    
    # Recent activities (last 10 fee payments)
    recent_payments = FeePayment.objects.filter(user=user).order_by('-created_at')[:10]
    recent_activities = []
    
    for payment in recent_payments:
        recent_activities.append({
            'type': 'fee_payment',
            'student_name': payment.student.name,
            'amount': float(payment.amount),
            'date': payment.payment_date
        })
    
    return Response({
        'success': True,
        'overview': {
            'total_students': total_students,
            'total_batches': total_batches,
            'total_tests': total_tests,
            'total_expected_fees': float(total_expected_fees),
            'total_collected_fees': float(total_collected_fees),
            'pending_fees': float(pending_fees),
            'present_today': present_today,
            'fee_collection_percentage': round(
                (float(total_collected_fees) / float(total_expected_fees) * 100), 2
            ) if total_expected_fees > 0 else 0
        },
        'defaulters': defaulters_list,
        'recent_activities': recent_activities
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_analytics_view(request):
    """
    Get detailed analytics for dashboard
    GET /api/dashboard/analytics/
    Headers: Authorization: Bearer <access_token>
    
    Query params:
    - period: 'week', 'month', 'year' (default: month)
    """
    user = request.user
    period = request.query_params.get('period', 'month')
    
    # Calculate date range
    today = timezone.now().date()
    if period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'year':
        start_date = today - timedelta(days=365)
    else:  # month
        start_date = today - timedelta(days=30)
    
    # Fee collection trend
    payments = FeePayment.objects.filter(
        user=user,
        payment_date__date__gte=start_date
    )
    
    total_collected_period = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Attendance trend
    attendance_records = AttendanceRecord.objects.filter(
        attendance__user=user,
        attendance__date__gte=start_date
    )
    
    total_present = attendance_records.filter(status='present').count()
    total_records = attendance_records.count()
    attendance_percentage = (total_present / total_records * 100) if total_records > 0 else 0
    
    # Test performance trend
    test_marks = TestMark.objects.filter(
        test__user=user,
        test__date__gte=start_date
    )
    
    avg_test_percentage = 0
    if test_marks.exists():
        total_percentage = sum([mark.percentage for mark in test_marks])
        avg_test_percentage = total_percentage / test_marks.count()
    
    # Batch-wise statistics
    batches = Batch.objects.filter(user=user)
    batch_stats = []
    
    for batch in batches:
        batch_students = Student.objects.filter(batch=batch)
        batch_total_fees = batch_students.aggregate(total=Sum('total_fees'))['total'] or Decimal('0.00')
        batch_collected_fees = batch_students.aggregate(total=Sum('fees_paid'))['total'] or Decimal('0.00')
        
        batch_stats.append({
            'batch_id': str(batch.id),
            'batch_name': batch.name,
            'student_count': batch_students.count(),
            'total_fees': float(batch_total_fees),
            'collected_fees': float(batch_collected_fees),
            'collection_percentage': round(
                (float(batch_collected_fees) / float(batch_total_fees) * 100), 2
            ) if batch_total_fees > 0 else 0
        })
    
    return Response({
        'success': True,
        'period': period,
        'analytics': {
            'fee_collection': {
                'total_collected': float(total_collected_period),
                'payment_count': payments.count()
            },
            'attendance': {
                'total_records': total_records,
                'total_present': total_present,
                'attendance_percentage': round(attendance_percentage, 2)
            },
            'test_performance': {
                'total_tests': test_marks.values('test').distinct().count(),
                'average_percentage': round(avg_test_percentage, 2)
            },
            'batch_statistics': batch_stats
        }
    }, status=status.HTTP_200_OK)