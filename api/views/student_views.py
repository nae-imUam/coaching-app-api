from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Sum, Count, F

from ..models import Student, Batch, Attendance, AttendanceRecord, FeePayment, Test, TestMark
from ..serializers import StudentSerializer, FeePaymentSerializer, TestMarkSerializer


# ─────────────────────────────────────────────────────────────────────────────
# List / Create
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def student_list_create_view(request):
    """
    GET  /api/students/        — list students (filters: batch_id, search)
    POST /api/students/        — create student (multipart/form-data or JSON)
    """
    if request.method == 'GET':
        students = Student.objects.filter(user=request.user).select_related('batch')

        batch_id = request.query_params.get('batch_id')
        if batch_id:
            students = students.filter(batch_id=batch_id)

        search = request.query_params.get('search', '').strip()
        if search:
            students = students.filter(name__icontains=search) | students.filter(phone__icontains=search)

        serializer = StudentSerializer(students, many=True, context={'request': request})
        return Response({
            'success':  True,
            'count':    students.count(),
            'students': serializer.data,
        })

    # POST — create
    data = request.data.copy()
    if 'profile_pic' in request.FILES:
        data['profile_pic'] = request.FILES['profile_pic']
    elif data.get('profile_pic') == '':
        data.pop('profile_pic', None)

    serializer = StudentSerializer(data=data, context={'request': request})
    if serializer.is_valid():
        batch_obj = serializer.validated_data.get('batch')
        if batch_obj and not Batch.objects.filter(id=batch_obj.id, user=request.user).exists():
            return Response({'success': False, 'message': 'Invalid batch selected'}, status=400)
        serializer.save(user=request.user)
        return Response({
            'success': True,
            'message': 'Student created successfully',
            'student': serializer.data,
        }, status=status.HTTP_201_CREATED)

    return Response({
        'success': False,
        'message': 'Student creation failed',
        'errors':  serializer.errors,
    }, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# Retrieve / Update / Delete
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def student_detail_view(request, student_id):
    """
    GET    /api/students/<id>/   — retrieve
    PATCH  /api/students/<id>/   — partial update (also handles profile_pic via FormData)
    PUT    /api/students/<id>/   — full update
    DELETE /api/students/<id>/   — delete
    """
    student = get_object_or_404(Student, id=student_id, user=request.user)

    if request.method == 'GET':
        return Response({
            'success': True,
            'student': StudentSerializer(student, context={'request': request}).data,
        })

    if request.method in ('PUT', 'PATCH'):
        data = request.data.copy()
        if 'profile_pic' in request.FILES:
            data['profile_pic'] = request.FILES['profile_pic']
        elif data.get('profile_pic') == '':
            data.pop('profile_pic', None)

        serializer = StudentSerializer(
            student, data=data,
            partial=(request.method == 'PATCH'),
            context={'request': request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Student updated successfully',
                'student': serializer.data,
            })
        return Response({
            'success': False,
            'message': 'Update failed',
            'errors':  serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        student.delete()
        return Response({'success': True, 'message': 'Student deleted'})


# ─────────────────────────────────────────────────────────────────────────────
# Profile pic upload
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def student_upload_profile_pic_view(request, student_id):
    """
    POST /api/students/<id>/upload-profile-pic/
    Body: multipart/form-data  key = "profile_pic"
    """
    student = get_object_or_404(Student, id=student_id, user=request.user)

    if 'profile_pic' not in request.FILES:
        return Response({'success': False, 'message': 'No file provided'}, status=400)

    student.profile_pic = request.FILES['profile_pic']
    student.save(update_fields=['profile_pic'])

    return Response({
        'success': True,
        'message': 'Profile picture updated',
        'student': StudentSerializer(student, context={'request': request}).data,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Full student profile  ← NEW
# Single endpoint that returns EVERYTHING needed by StudentProfile.tsx
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_full_profile_view(request, student_id):
    """
    GET /api/students/<id>/profile/

    Returns a complete student profile in ONE request:
      - student          basic info
      - batch            batch details
      - attendance       date → status map + monthly stats + totals
      - fees             payment history + summary
      - tests            all test results with percentage
      - summary          key KPIs for the overview tab
    """
    student = get_object_or_404(Student, id=student_id, user=request.user)
    batch   = student.batch

    # ── Attendance ────────────────────────────────────────────────────────────
    att_records = AttendanceRecord.objects.filter(
        student=student,
        attendance__user=request.user,
    ).select_related('attendance').order_by('attendance__date')

    date_map: dict[str, str] = {}
    monthly:  dict[str, dict] = {}

    for rec in att_records:
        date_str  = str(rec.attendance.date)
        month_key = date_str[:7]
        date_map[date_str] = rec.status

        if month_key not in monthly:
            monthly[month_key] = {'present': 0, 'absent': 0, 'leave': 0, 'total': 0, 'pct': 0}
        monthly[month_key][rec.status] += 1
        monthly[month_key]['total']    += 1

    for m in monthly.values():
        m['pct'] = round(m['present'] / m['total'] * 100) if m['total'] else 0

    att_total   = att_records.count()
    att_present = att_records.filter(status='present').count()
    att_absent  = att_records.filter(status='absent').count()
    att_leave   = att_records.filter(status='leave').count()
    att_pct     = round(att_present / att_total * 100) if att_total else 0

    # ── Fees ──────────────────────────────────────────────────────────────────
    fee_payments = FeePayment.objects.filter(
        student=student, user=request.user
    ).order_by('-payment_date')

    fee_serializer = FeePaymentSerializer(fee_payments, many=True)

    total_fee   = float(student.total_fees)
    fees_paid   = float(student.fees_paid)
    fees_due    = total_fee - fees_paid
    fee_pct     = round(fees_paid / total_fee * 100) if total_fee > 0 else 0

    # ── Tests ─────────────────────────────────────────────────────────────────
    test_marks = TestMark.objects.filter(
        student=student,
        test__user=request.user,
    ).select_related('test', 'test__batch').order_by('-test__date')

    tests_data = []
    for tm in test_marks:
        t   = tm.test
        pct = round(float(tm.marks_obtained) / t.total_marks * 100) if t.total_marks > 0 else 0
        tests_data.append({
            'test_id':      str(t.id),
            'test_name':    t.name,
            'date':         str(t.date),
            'board':        t.board,
            'batch_name':   t.batch.name if t.batch else '',
            'total_marks':  t.total_marks,
            'marks_obtained': float(tm.marks_obtained),
            'pct':          pct,
            'grade':        _grade(pct),
        })

    avg_test_pct = (
        round(sum(t['pct'] for t in tests_data) / len(tests_data))
        if tests_data else None
    )

    # ── Summary KPIs ──────────────────────────────────────────────────────────
    summary = {
        'attendance_pct':  att_pct,
        'attendance_total': att_total,
        'attendance_present': att_present,
        'fees_paid':       fees_paid,
        'fees_due':        fees_due,
        'fee_pct':         fee_pct,
        'tests_count':     len(tests_data),
        'avg_test_pct':    avg_test_pct,
        'overall_status':  (
            'excellent' if att_pct >= 75 and fee_pct >= 80 and (avg_test_pct or 0) >= 70
            else 'good' if att_pct >= 75 and fee_pct >= 50
            else 'needs_attention'
        ),
    }

    # ── Response ──────────────────────────────────────────────────────────────
    return Response({
        'success': True,
        'student': StudentSerializer(student, context={'request': request}).data,
        'batch': {
            'id':     str(batch.id) if batch else None,
            'name':   batch.name   if batch else None,
            'timing': batch.timing if batch else None,
        },
        'attendance': {
            'date_map': date_map,
            'monthly':  monthly,
            'totals': {
                'total':   att_total,
                'present': att_present,
                'absent':  att_absent,
                'leave':   att_leave,
                'pct':     att_pct,
            },
        },
        'fees': {
            'summary': {
                'total_fee':  total_fee,
                'fees_paid':  fees_paid,
                'fees_due':   fees_due,
                'fee_pct':    fee_pct,
            },
            'payments': fee_serializer.data,
        },
        'tests': tests_data,
        'summary': summary,
    }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def _grade(pct: int) -> str:
    if pct >= 90: return 'A+'
    if pct >= 80: return 'A'
    if pct >= 70: return 'B'
    if pct >= 60: return 'C'
    if pct >= 50: return 'D'
    if pct >= 33: return 'E'
    return 'F'