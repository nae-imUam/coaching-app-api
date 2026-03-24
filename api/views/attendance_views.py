from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from ..models import Attendance, AttendanceRecord, Batch, Student
from ..serializers import AttendanceSerializer


# ─────────────────────────────────────────────────────────────────────────────
# List / Create / Upsert
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def attendance_list_create_view(request):
    """
    GET  /api/attendance/          — list all attendance sessions
    POST /api/attendance/          — create OR fully replace an attendance session

    GET query params:
      batch_id  — filter by batch UUID
      date      — filter by exact date (YYYY-MM-DD)
      month     — filter by month (YYYY-MM)

    POST body:
    {
        "batch":   "<batch_uuid>",
        "date":    "YYYY-MM-DD",
        "records": [
            {"student": "<uuid>", "status": "present"},
            {"student": "<uuid>", "status": "absent"},
            {"student": "<uuid>", "status": "leave"}
        ]
    }
    """
    if request.method == 'GET':
        qs = Attendance.objects.filter(user=request.user).prefetch_related('records')

        batch_id = request.query_params.get('batch_id')
        if batch_id:
            qs = qs.filter(batch_id=batch_id)

        date = request.query_params.get('date')
        if date:
            qs = qs.filter(date=date)

        month = request.query_params.get('month')
        if month:
            try:
                year, month_num = month.split('-')
                qs = qs.filter(date__year=year, date__month=month_num)
            except ValueError:
                pass

        serializer = AttendanceSerializer(qs, many=True)
        return Response({
            'success':     True,
            'count':       qs.count(),
            'attendances': serializer.data,
        }, status=status.HTTP_200_OK)

    # ── POST: upsert ──────────────────────────────────────────────────────────
    batch_id = request.data.get('batch')
    date     = request.data.get('date')

    if not batch_id or not date:
        return Response({
            'success': False,
            'message': '"batch" and "date" are required.',
        }, status=status.HTTP_400_BAD_REQUEST)

    # Verify the batch belongs to this user
    batch = get_object_or_404(Batch, id=batch_id, user=request.user)

    try:
        attendance = Attendance.objects.get(user=request.user, batch=batch, date=date)
        serializer = AttendanceSerializer(attendance, data=request.data)
    except Attendance.DoesNotExist:
        serializer = AttendanceSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response({
            'success':    True,
            'message':    'Attendance saved successfully',
            'attendance': serializer.data,
        }, status=status.HTTP_201_CREATED)

    return Response({
        'success': False,
        'message': 'Attendance save failed',
        'errors':  serializer.errors,
    }, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# Retrieve / Update / Delete single session
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def attendance_detail_view(request, attendance_id):
    """
    GET    /api/attendance/<id>/  — retrieve
    PUT    /api/attendance/<id>/  — full replace
    PATCH  /api/attendance/<id>/  — partial update
    DELETE /api/attendance/<id>/  — delete
    """
    attendance = get_object_or_404(Attendance, id=attendance_id, user=request.user)

    if request.method == 'GET':
        return Response({
            'success':    True,
            'attendance': AttendanceSerializer(attendance).data,
        })

    if request.method in ('PUT', 'PATCH'):
        serializer = AttendanceSerializer(
            attendance, data=request.data, partial=(request.method == 'PATCH')
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success':    True,
                'message':    'Attendance updated successfully',
                'attendance': serializer.data,
            })
        return Response({
            'success': False,
            'message': 'Update failed',
            'errors':  serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        attendance.delete()
        return Response({'success': True, 'message': 'Attendance deleted'})


# ─────────────────────────────────────────────────────────────────────────────
# Student attendance report (date-map + monthly breakdown + totals)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_attendance_report_view(request, student_id):
    """
    GET /api/attendance/student/<student_id>/report/

    Returns:
      date_map  — { "YYYY-MM-DD": "present"|"absent"|"leave" }
      monthly   — { "YYYY-MM": { present, absent, leave, total, pct } }
      totals    — { present, absent, leave, total, pct }

    Query params:
      month — restrict to a single month (YYYY-MM)
    """
    student = get_object_or_404(Student, id=student_id, user=request.user)

    records = AttendanceRecord.objects.filter(
        student=student,
        attendance__user=request.user,
    ).select_related('attendance').order_by('attendance__date')

    # Optional month filter
    month = request.query_params.get('month')
    if month:
        try:
            year, month_num = month.split('-')
            records = records.filter(
                attendance__date__year=year,
                attendance__date__month=month_num,
            )
        except ValueError:
            pass

    date_map: dict[str, str] = {}
    monthly:  dict[str, dict] = {}

    for rec in records:
        date_str  = str(rec.attendance.date)
        month_key = date_str[:7]                    # YYYY-MM

        date_map[date_str] = rec.status

        if month_key not in monthly:
            monthly[month_key] = {
                'present': 0, 'absent': 0, 'leave': 0, 'total': 0, 'pct': 0,
            }
        monthly[month_key][rec.status] += 1
        monthly[month_key]['total']    += 1

    for m in monthly.values():
        m['pct'] = round(m['present'] / m['total'] * 100) if m['total'] else 0

    total   = records.count()
    present = records.filter(status='present').count()
    absent  = records.filter(status='absent').count()
    leave   = records.filter(status='leave').count()
    pct     = round(present / total * 100) if total else 0

    return Response({
        'success': True,
        'student': {
            'id':   str(student.id),
            'name': student.name,
            'roll': student.roll,
        },
        'date_map': date_map,
        'monthly':  monthly,
        'totals': {
            'present': present,
            'absent':  absent,
            'leave':   leave,
            'total':   total,
            'pct':     pct,
        },
        # Legacy fields kept for backward compatibility
        'report': {
            'total_days':            total,
            'present_days':          present,
            'absent_days':           absent,
            'leave_days':            leave,
            'attendance_percentage': pct,
        },
    }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# Class-wide report (per-student totals, with optional date range)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def class_attendance_report_view(request):
    """
    GET /api/attendance/class-report/

    Query params (all optional):
      batch_id    — required; batch UUID
      start_date  — YYYY-MM-DD
      end_date    — YYYY-MM-DD

    Returns per-student totals + overall class average.
    """
    batch_id   = request.query_params.get('batch_id')
    start_date = request.query_params.get('start_date')
    end_date   = request.query_params.get('end_date')

    if not batch_id:
        return Response(
            {'success': False, 'message': 'batch_id query param is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    batch = get_object_or_404(Batch, id=batch_id, user=request.user)

    sessions = Attendance.objects.filter(user=request.user, batch=batch)
    if start_date:
        sessions = sessions.filter(date__gte=start_date)
    if end_date:
        sessions = sessions.filter(date__lte=end_date)

    total_classes = sessions.count()
    if total_classes == 0:
        return Response({
            'success':       True,
            'total_classes': 0,
            'students':      [],
            'avg_pct':       0,
        })

    batch_students = Student.objects.filter(batch=batch, user=request.user)

    student_stats = []
    for student in batch_students:
        records = AttendanceRecord.objects.filter(
            attendance__in=sessions, student=student
        )
        present = records.filter(status='present').count()
        absent  = records.filter(status='absent').count()
        leave   = records.filter(status='leave').count()
        pct     = round(present / total_classes * 100) if total_classes else 0

        student_stats.append({
            'student_id': str(student.id),
            'name':       student.name,
            'roll':       student.roll,
            'present':    present,
            'absent':     absent,
            'leave':      leave,
            'total':      total_classes,
            'pct':        pct,
        })

    student_stats.sort(key=lambda x: x['pct'], reverse=True)
    avg_pct = (
        round(sum(s['pct'] for s in student_stats) / len(student_stats))
        if student_stats else 0
    )

    return Response({
        'success':       True,
        'batch':         {'id': str(batch.id), 'name': batch.name},
        'total_classes': total_classes,
        'avg_pct':       avg_pct,
        'students':      student_stats,
    }, status=status.HTTP_200_OK)