from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Sum, F
from decimal import Decimal

from ..models import FeePayment, Student, Batch
from ..serializers import FeePaymentSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def fee_payment_list_create_view(request):
    """
    GET /api/fees/ - List all fee payments
    POST /api/fees/ - Record a new fee payment
    Headers: Authorization: Bearer <access_token>
    
    Query params for GET:
    - student_id: filter by student
    - batch_id: filter by batch
    - month: filter by month (YYYY-MM)
    
    POST Body: {
        "student": "student_uuid",
        "amount": 5000,
        "payment_date": "2024-01-20T10:30:00Z",
        "notes": "January fee payment"
    }
    """
    if request.method == 'GET':
        payments = FeePayment.objects.filter(user=request.user)
        
        # Filter by student
        student_id = request.query_params.get('student_id')
        if student_id:
            payments = payments.filter(student_id=student_id)
        
        # Filter by batch
        batch_id = request.query_params.get('batch_id')
        if batch_id:
            payments = payments.filter(student__batch_id=batch_id)
        
        # Filter by month
        month = request.query_params.get('month')
        if month:
            try:
                year, month_num = month.split('-')
                payments = payments.filter(
                    payment_date__year=year,
                    payment_date__month=month_num
                )
            except:
                pass
        
        serializer = FeePaymentSerializer(payments, many=True)
        
        # Calculate totals
        total_collected = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        return Response({
            'success': True,
            'count': payments.count(),
            'total_collected': float(total_collected),
            'payments': serializer.data
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = FeePaymentSerializer(data=request.data)
        
        if serializer.is_valid():
            student_id = serializer.validated_data.get('student')
            amount = serializer.validated_data.get('amount')
            
            # Verify student belongs to user
            student = get_object_or_404(Student, id=student_id.id, user=request.user)
            
            # Update student's fees_paid
            student.fees_paid = F('fees_paid') + amount
            student.save()
            student.refresh_from_db()  # Refresh to get actual value
            
            # Save payment record
            serializer.save(user=request.user)
            
            return Response({
                'success': True,
                'message': 'Fee payment recorded successfully',
                'payment': serializer.data,
                'student_fees_status': {
                    'total_fees': float(student.total_fees),
                    'fees_paid': float(student.fees_paid),
                    'fees_due': float(student.fees_due)
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Fee payment failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def fee_payment_detail_view(request, payment_id):
    """
    GET /api/fees/<id>/ - Get payment details
    DELETE /api/fees/<id>/ - Delete payment (reverses the transaction)
    Headers: Authorization: Bearer <access_token>
    """
    payment = get_object_or_404(FeePayment, id=payment_id, user=request.user)
    
    if request.method == 'GET':
        serializer = FeePaymentSerializer(payment)
        return Response({
            'success': True,
            'payment': serializer.data
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'DELETE':
        # Reverse the payment in student record
        student = payment.student
        student.fees_paid = F('fees_paid') - payment.amount
        student.save()
        
        payment.delete()
        
        return Response({
            'success': True,
            'message': 'Fee payment deleted and reversed successfully'
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_fee_status_view(request, student_id):
    """
    Get fee status for a specific student
    GET /api/fees/student/<student_id>/status/
    Headers: Authorization: Bearer <access_token>
    """
    student = get_object_or_404(Student, id=student_id, user=request.user)
    
    # Get all payments for this student
    payments = FeePayment.objects.filter(student=student).order_by('-payment_date')
    
    return Response({
        'success': True,
        'student': {
            'id': str(student.id),
            'name': student.name,
            'roll': student.roll
        },
        'fee_status': {
            'total_fees': float(student.total_fees),
            'fees_paid': float(student.fees_paid),
            'fees_due': float(student.fees_due),
            'payment_percentage': round((float(student.fees_paid) / float(student.total_fees) * 100), 2) if student.total_fees > 0 else 0
        },
        'payment_history': FeePaymentSerializer(payments, many=True).data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def batch_fee_overview_view(request, batch_id):
    """
    Get fee overview for a specific batch
    GET /api/fees/batch/<batch_id>/overview/
    Headers: Authorization: Bearer <access_token>
    """
    batch = get_object_or_404(Batch, id=batch_id, user=request.user)
    students = Student.objects.filter(batch=batch)
    
    total_expected = students.aggregate(total=Sum('total_fees'))['total'] or Decimal('0.00')
    total_collected = students.aggregate(total=Sum('fees_paid'))['total'] or Decimal('0.00')
    total_due = total_expected - total_collected
    
    # Get defaulters
    defaulters = students.filter(total_fees__gt=F('fees_paid')).values(
        'id', 'name', 'roll', 'total_fees', 'fees_paid'
    )
    
    defaulters_list = []
    for student in defaulters:
        defaulters_list.append({
            'id': str(student['id']),
            'name': student['name'],
            'roll': student['roll'],
            'total_fees': float(student['total_fees']),
            'fees_paid': float(student['fees_paid']),
            'fees_due': float(student['total_fees']) - float(student['fees_paid'])
        })
    
    return Response({
        'success': True,
        'batch': {
            'id': str(batch.id),
            'name': batch.name
        },
        'overview': {
            'total_students': students.count(),
            'total_expected': float(total_expected),
            'total_collected': float(total_collected),
            'total_due': float(total_due),
            'collection_percentage': round((float(total_collected) / float(total_expected) * 100), 2) if total_expected > 0 else 0
        },
        'defaulters': defaulters_list
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fee_analytics_view(request):
    """
    Get overall fee analytics for the user
    GET /api/fees/analytics/
    Headers: Authorization: Bearer <access_token>
    
    Query params:
    - month: filter by month (YYYY-MM)
    """
    students = Student.objects.filter(user=request.user)
    
    total_expected = students.aggregate(total=Sum('total_fees'))['total'] or Decimal('0.00')
    total_collected = students.aggregate(total=Sum('fees_paid'))['total'] or Decimal('0.00')
    total_due = total_expected - total_collected
    
    # Monthly collection
    payments = FeePayment.objects.filter(user=request.user)
    
    month = request.query_params.get('month')
    if month:
        try:
            year, month_num = month.split('-')
            monthly_payments = payments.filter(
                payment_date__year=year,
                payment_date__month=month_num
            )
            monthly_collection = monthly_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        except:
            monthly_collection = Decimal('0.00')
    else:
        monthly_collection = Decimal('0.00')
    
    return Response({
        'success': True,
        'analytics': {
            'total_students': students.count(),
            'total_expected_fees': float(total_expected),
            'total_collected_fees': float(total_collected),
            'total_due_fees': float(total_due),
            'collection_percentage': round((float(total_collected) / float(total_expected) * 100), 2) if total_expected > 0 else 0,
            'monthly_collection': float(monthly_collection) if month else None,
            'students_with_dues': students.filter(total_fees__gt=F('fees_paid')).count(),
            'fully_paid_students': students.filter(fees_paid__gte=F('total_fees')).count()
        }
    }, status=status.HTTP_200_OK)