from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from datetime import datetime

from ..models import Attendance, AttendanceRecord, Batch, Student
from ..serializers import AttendanceSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def attendance_list_create_view(request):
    """
    GET /api/attendance/ - List all attendance records
    POST /api/attendance/ - Create/Update attendance
    Headers: Authorization: Bearer <access_token>
    
    Query params for GET:
    - batch_id: filter by batch
    - date: filter by date (YYYY-MM-DD)
    - month: filter by month (YYYY-MM)
    
    POST Body: {
        "batch": "batch_uuid",
        "date": "2024-01-20",
        "records": [
            {"student": "student_uuid", "status": "present"},
            {"student": "student_uuid", "status": "absent"}
        ]
    }
    """
    if request.method == 'GET':
        attendances = Attendance.objects.filter(user=request.user)
        
        # Filter by batch
        batch_id = request.query_params.get('batch_id')
        if batch_id:
            attendances = attendances.filter(batch_id=batch_id)
        
        # Filter by date
        date = request.query_params.get('date')
        if date:
            attendances = attendances.filter(date=date)
        
        # Filter by month
        month = request.query_params.get('month')
        if month:
            try:
                year, month_num = month.split('-')
                attendances = attendances.filter(date__year=year, date__month=month_num)
            except:
                pass
        
        serializer = AttendanceSerializer(attendances, many=True)
        return Response({
            'success': True,
            'count': attendances.count(),
            'attendances': serializer.data
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        # Check if attendance already exists for this batch and date
        batch_id = request.data.get('batch')
        date = request.data.get('date')
        
        try:
            attendance = Attendance.objects.get(
                user=request.user,
                batch_id=batch_id,
                date=date
            )
            # Update existing attendance
            serializer = AttendanceSerializer(attendance, data=request.data)
        except Attendance.DoesNotExist:
            # Create new attendance
            serializer = AttendanceSerializer(data=request.data)
        
        if serializer.is_valid():
            # Verify batch belongs to user
            batch = get_object_or_404(Batch, id=batch_id, user=request.user)
            
            serializer.save(user=request.user)
            return Response({
                'success': True,
                'message': 'Attendance saved successfully',
                'attendance': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Attendance save failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def attendance_detail_view(request, attendance_id):
    """
    GET /api/attendance/<id>/ - Get attendance details
    PUT/PATCH /api/attendance/<id>/ - Update attendance
    DELETE /api/attendance/<id>/ - Delete attendance
    Headers: Authorization: Bearer <access_token>
    """
    attendance = get_object_or_404(Attendance, id=attendance_id, user=request.user)
    
    if request.method == 'GET':
        serializer = AttendanceSerializer(attendance)
        return Response({
            'success': True,
            'attendance': serializer.data
        }, status=status.HTTP_200_OK)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = AttendanceSerializer(attendance, data=request.data, partial=request.method == 'PATCH')
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Attendance updated successfully',
                'attendance': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Attendance update failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        attendance.delete()
        return Response({
            'success': True,
            'message': 'Attendance deleted successfully'
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_attendance_report_view(request, student_id):
    """
    Get attendance report for a specific student
    GET /api/attendance/student/<student_id>/report/
    Headers: Authorization: Bearer <access_token>
    
    Query params:
    - month: filter by month (YYYY-MM)
    """
    student = get_object_or_404(Student, id=student_id, user=request.user)
    
    # Get all attendance records for this student
    records = AttendanceRecord.objects.filter(
        student=student,
        attendance__user=request.user
    )
    
    # Filter by month if provided
    month = request.query_params.get('month')
    if month:
        try:
            year, month_num = month.split('-')
            records = records.filter(
                attendance__date__year=year,
                attendance__date__month=month_num
            )
        except:
            pass
    
    total_days = records.count()
    present_days = records.filter(status='present').count()
    absent_days = records.filter(status='absent').count()
    
    attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    return Response({
        'success': True,
        'student': {
            'id': str(student.id),
            'name': student.name,
            'roll': student.roll
        },
        'report': {
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'attendance_percentage': round(attendance_percentage, 2)
        }
    }, status=status.HTTP_200_OK)