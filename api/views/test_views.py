from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Avg

from ..models import Test, TestMark, Batch, Student
from ..serializers import TestSerializer, TestMarkSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def test_list_create_view(request):
    """
    GET /api/tests/ - List all tests
    POST /api/tests/ - Create a new test
    Headers: Authorization: Bearer <access_token>
    
    Query params for GET:
    - batch_id: filter by batch
    
    POST Body: {
        "batch": "batch_uuid",
        "name": "Physics Weekly Test",
        "date": "2024-01-25",
        "total_marks": 100,
        "duration": 3,
        "board": "CBSE"
    }
    """
    if request.method == 'GET':
        tests = Test.objects.filter(user=request.user)
        
        # Filter by batch
        batch_id = request.query_params.get('batch_id')
        if batch_id:
            tests = tests.filter(batch_id=batch_id)
        
        serializer = TestSerializer(tests, many=True)
        return Response({
            'success': True,
            'count': tests.count(),
            'tests': serializer.data
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = TestSerializer(data=request.data)
        
        if serializer.is_valid():
            # Verify batch belongs to user
            batch_id = serializer.validated_data.get('batch')
            get_object_or_404(Batch, id=batch_id.id, user=request.user)
            
            serializer.save(user=request.user)
            return Response({
                'success': True,
                'message': 'Test created successfully',
                'test': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Test creation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def test_detail_view(request, test_id):
    """
    GET /api/tests/<id>/ - Get test details
    PUT/PATCH /api/tests/<id>/ - Update test
    DELETE /api/tests/<id>/ - Delete test
    Headers: Authorization: Bearer <access_token>
    """
    test = get_object_or_404(Test, id=test_id, user=request.user)
    
    if request.method == 'GET':
        serializer = TestSerializer(test)
        return Response({
            'success': True,
            'test': serializer.data
        }, status=status.HTTP_200_OK)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = TestSerializer(test, data=request.data, partial=request.method == 'PATCH')
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Test updated successfully',
                'test': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Test update failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        test.delete()
        return Response({
            'success': True,
            'message': 'Test deleted successfully'
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_marks_bulk_create_view(request, test_id):
    """
    Add/Update marks for multiple students in a test
    POST /api/tests/<test_id>/marks/bulk/
    Headers: Authorization: Bearer <access_token>
    
    Body: {
        "marks": [
            {"student": "student_uuid", "marks_obtained": 85},
            {"student": "student_uuid", "marks_obtained": 92}
        ]
    }
    """
    test = get_object_or_404(Test, id=test_id, user=request.user)
    marks_data = request.data.get('marks', [])
    
    if not marks_data:
        return Response({
            'success': False,
            'message': 'No marks data provided'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    created_marks = []
    errors = []
    
    for mark_data in marks_data:
        student_id = mark_data.get('student')
        marks_obtained = mark_data.get('marks_obtained')
        
        try:
            student = Student.objects.get(id=student_id, user=request.user)
            
            # Update if exists, create if not
            mark, created = TestMark.objects.update_or_create(
                test=test,
                student=student,
                defaults={'marks_obtained': marks_obtained}
            )
            
            created_marks.append(TestMarkSerializer(mark).data)
        except Student.DoesNotExist:
            errors.append(f"Student {student_id} not found")
        except Exception as e:
            errors.append(f"Error for student {student_id}: {str(e)}")
    
    return Response({
        'success': len(errors) == 0,
        'message': f'{len(created_marks)} marks recorded successfully',
        'marks': created_marks,
        'errors': errors if errors else None
    }, status=status.HTTP_200_OK if len(errors) == 0 else status.HTTP_207_MULTI_STATUS)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_marks_list_view(request, test_id):
    """
    Get all marks for a specific test
    GET /api/tests/<test_id>/marks/
    Headers: Authorization: Bearer <access_token>
    """
    test = get_object_or_404(Test, id=test_id, user=request.user)
    marks = TestMark.objects.filter(test=test)
    
    serializer = TestMarkSerializer(marks, many=True)
    
    # Calculate statistics
    if marks.exists():
        avg_marks = marks.aggregate(avg=Avg('marks_obtained'))['avg']
        highest_marks = marks.order_by('-marks_obtained').first()
        lowest_marks = marks.order_by('marks_obtained').first()
    else:
        avg_marks = 0
        highest_marks = None
        lowest_marks = None
    
    return Response({
        'success': True,
        'test': {
            'id': str(test.id),
            'name': test.name,
            'total_marks': test.total_marks
        },
        'statistics': {
            'total_students': marks.count(),
            'average_marks': round(float(avg_marks), 2) if avg_marks else 0,
            'highest_marks': float(highest_marks.marks_obtained) if highest_marks else 0,
            'lowest_marks': float(lowest_marks.marks_obtained) if lowest_marks else 0,
            'pass_percentage': round(
                (marks.filter(marks_obtained__gte=test.total_marks * 0.33).count() / marks.count() * 100), 2
            ) if marks.count() > 0 else 0
        },
        'marks': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_test_report_view(request, student_id):
    """
    Get test report for a specific student
    GET /api/tests/student/<student_id>/report/
    Headers: Authorization: Bearer <access_token>
    """
    student = get_object_or_404(Student, id=student_id, user=request.user)
    
    marks = TestMark.objects.filter(student=student).select_related('test')
    
    report = []
    total_percentage = 0
    
    for mark in marks:
        percentage = mark.percentage
        total_percentage += percentage
        
        report.append({
            'test_id': str(mark.test.id),
            'test_name': mark.test.name,
            'test_date': mark.test.date,
            'total_marks': mark.test.total_marks,
            'marks_obtained': float(mark.marks_obtained),
            'percentage': round(percentage, 2)
        })
    
    avg_percentage = (total_percentage / marks.count()) if marks.count() > 0 else 0
    
    return Response({
        'success': True,
        'student': {
            'id': str(student.id),
            'name': student.name,
            'roll': student.roll
        },
        'summary': {
            'total_tests': marks.count(),
            'average_percentage': round(avg_percentage, 2)
        },
        'tests': report
    }, status=status.HTTP_200_OK)