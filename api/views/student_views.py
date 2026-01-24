# from rest_framework import status
# from rest_framework.decorators import api_view, permission_classes, parser_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from django.shortcuts import get_object_or_404
# from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
# from ..models import Student, Batch
# from ..serializers import StudentSerializer


# # @api_view(['GET', 'POST'])
# # @permission_classes([IsAuthenticated])
# # def student_list_create_view(request):
# #     """
# #     GET /api/students/ - List all students for current user
# #     POST /api/students/ - Create a new student
# #     Headers: Authorization: Bearer <access_token>
    
# #     Query params for GET:
# #     - batch_id: filter by batch
# #     - search: search by name or phone
    
# #     POST Body: {
# #         "batch": "batch_uuid",
# #         "name": "John Doe",
# #         "phone": "1234567890",
# #         "roll": "101",
# #         "total_fees": 12000,
# #         "fees_paid": 5000
# #     }
# #     """
# #     if request.method == 'GET':
# #         students = Student.objects.filter(user=request.user)
        
# #         # Filter by batch if provided
# #         batch_id = request.query_params.get('batch_id')
# #         if batch_id:
# #             students = students.filter(batch_id=batch_id)
        
# #         # Search by name or phone
# #         search = request.query_params.get('search')
# #         if search:
# #             students = students.filter(name__icontains=search) | students.filter(phone__icontains=search)
        
# #         serializer = StudentSerializer(students, many=True)
# #         return Response({
# #             'success': True,
# #             'count': students.count(),
# #             'students': serializer.data
# #         }, status=status.HTTP_200_OK)
    
# #     elif request.method == 'POST':
# #         serializer = StudentSerializer(data=request.data)
        
# #         if serializer.is_valid():
# #             # Verify batch belongs to user
# #             batch_id = serializer.validated_data.get('batch')
# #             if batch_id and not Batch.objects.filter(id=batch_id.id, user=request.user).exists():
# #                 return Response({
# #                     'success': False,
# #                     'message': 'Invalid batch'
# #                 }, status=status.HTTP_400_BAD_REQUEST)
            
# #             serializer.save(user=request.user)
# #             return Response({
# #                 'success': True,
# #                 'message': 'Student created successfully',
# #                 'student': serializer.data
# #             }, status=status.HTTP_201_CREATED)
        
# #         return Response({
# #             'success': False,
# #             'message': 'Student creation failed',
# #             'errors': serializer.errors
# #         }, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['GET', 'POST'])
# @permission_classes([IsAuthenticated])
# # This line is crucial! It tells Django to accept Files (MultiPart) and Text (Form/JSON)
# @parser_classes([MultiPartParser, FormParser, JSONParser]) 
# def student_list_create_view(request):
#     """
#     GET /api/students/ - List all students
#     POST /api/students/ - Create a new student (Now supports Images)
#     """
#     if request.method == 'GET':
#         students = Student.objects.filter(user=request.user)
        
#         batch_id = request.query_params.get('batch_id')
#         if batch_id:
#             students = students.filter(batch_id=batch_id)
        
#         search = request.query_params.get('search')
#         if search:
#             students = students.filter(name__icontains=search) | students.filter(phone__icontains=search)
        
#         serializer = StudentSerializer(students, many=True)
#         return Response({
#             'success': True,
#             'count': students.count(),
#             'students': serializer.data
#         }, status=status.HTTP_200_OK)
    
#     elif request.method == 'POST':
#         # request.data handles both JSON and Multipart automatically now
#         serializer = StudentSerializer(data=request.data)
        
#         if serializer.is_valid():
#             # Verify batch belongs to user
#             batch_obj = serializer.validated_data.get('batch')
#             if batch_obj and not Batch.objects.filter(id=batch_obj.id, user=request.user).exists():
#                 return Response({
#                     'success': False,
#                     'message': 'Invalid batch selected'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             # Save with user (and image if provided in request.data)
#             serializer.save(user=request.user)
            
#             return Response({
#                 'success': True,
#                 'message': 'Student created successfully',
#                 'student': serializer.data
#             }, status=status.HTTP_201_CREATED)
        
#         # If it fails, print errors to console so you can see why in your terminal
#         print("Serializer Errors:", serializer.errors) 
        
#         return Response({
#             'success': False,
#             'message': 'Student creation failed',
#             'errors': serializer.errors
#         }, status=status.HTTP_400_BAD_REQUEST)




# @api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
# @permission_classes([IsAuthenticated])
# def student_detail_view(request, student_id):
#     """
#     GET /api/students/<id>/ - Get student details
#     PUT/PATCH /api/students/<id>/ - Update student
#     DELETE /api/students/<id>/ - Delete student
#     Headers: Authorization: Bearer <access_token>
#     """
#     student = get_object_or_404(Student, id=student_id, user=request.user)
    
#     if request.method == 'GET':
#         serializer = StudentSerializer(student)
#         return Response({
#             'success': True,
#             'student': serializer.data
#         }, status=status.HTTP_200_OK)
    
#     elif request.method in ['PUT', 'PATCH']:
#         serializer = StudentSerializer(student, data=request.data, partial=request.method == 'PATCH')
        
#         if serializer.is_valid():
#             serializer.save()
#             return Response({
#                 'success': True,
#                 'message': 'Student updated successfully',
#                 'student': serializer.data
#             }, status=status.HTTP_200_OK)
        
#         return Response({
#             'success': False,
#             'message': 'Student update failed',
#             'errors': serializer.errors
#         }, status=status.HTTP_400_BAD_REQUEST)
    
#     elif request.method == 'DELETE':
#         student.delete()
#         return Response({
#             'success': True,
#             'message': 'Student deleted successfully'
#         }, status=status.HTTP_200_OK)


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def student_upload_profile_pic_view(request, student_id):
#     """
#     Upload profile picture for student
#     POST /api/students/<id>/upload-profile-pic/
#     Headers: Authorization: Bearer <access_token>
#     Body: multipart/form-data with 'profile_pic' file
#     """
#     student = get_object_or_404(Student, id=student_id, user=request.user)
    
#     if 'profile_pic' not in request.FILES:
#         return Response({
#             'success': False,
#             'message': 'No file provided'
#         }, status=status.HTTP_400_BAD_REQUEST)
    
#     student.profile_pic = request.FILES['profile_pic']
#     student.save()
    
#     serializer = StudentSerializer(student)
#     return Response({
#         'success': True,
#         'message': 'Profile picture uploaded successfully',
#         'student': serializer.data
#     }, status=status.HTTP_200_OK)




from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from ..models import Student, Batch
from ..serializers import StudentSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
# Remove parser_classes - let DRF auto-detect based on Content-Type
def student_list_create_view(request):
    """
    GET /api/students/ - List all students
    POST /api/students/ - Create a new student
    Supports both JSON and multipart/form-data
    """
    if request.method == 'GET':
        students = Student.objects.filter(user=request.user)
        
        batch_id = request.query_params.get('batch_id')
        if batch_id:
            students = students.filter(batch_id=batch_id)
        
        search = request.query_params.get('search')
        if search:
            students = students.filter(name__icontains=search) | students.filter(phone__icontains=search)
        
        serializer = StudentSerializer(students, many=True)
        return Response({
            'success': True,
            'count': students.count(),
            'students': serializer.data
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        # Create a mutable copy of request.data
        data = request.data.copy()
        
        # Handle profile_pic - it might be in FILES or DATA depending on request type
        if 'profile_pic' in request.FILES:
            # Multipart request - file is in request.FILES
            data['profile_pic'] = request.FILES['profile_pic']
        elif 'profile_pic' in data and data['profile_pic'] == '':
            # JSON request with empty string - remove it
            data.pop('profile_pic', None)
        
        serializer = StudentSerializer(data=data)
        
        if serializer.is_valid():
            # Verify batch belongs to user
            batch_obj = serializer.validated_data.get('batch')
            if batch_obj and not Batch.objects.filter(id=batch_obj.id, user=request.user).exists():
                return Response({
                    'success': False,
                    'message': 'Invalid batch selected'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Save student
            serializer.save(user=request.user)
            
            return Response({
                'success': True,
                'message': 'Student created successfully',
                'student': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        print("Serializer Errors:", serializer.errors) 
        
        return Response({
            'success': False,
            'message': 'Student creation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def student_detail_view(request, student_id):
    """
    GET /api/students/<id>/ - Get student details
    PUT/PATCH /api/students/<id>/ - Update student
    DELETE /api/students/<id>/ - Delete student
    """
    student = get_object_or_404(Student, id=student_id, user=request.user)
    
    if request.method == 'GET':
        serializer = StudentSerializer(student)
        return Response({
            'success': True,
            'student': serializer.data
        }, status=status.HTTP_200_OK)
    
    elif request.method in ['PUT', 'PATCH']:
        # Handle file upload for update too
        data = request.data.copy()
        
        if 'profile_pic' in request.FILES:
            data['profile_pic'] = request.FILES['profile_pic']
        elif 'profile_pic' in data and data['profile_pic'] == '':
            data.pop('profile_pic', None)
        
        serializer = StudentSerializer(student, data=data, partial=request.method == 'PATCH')
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Student updated successfully',
                'student': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Student update failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        student.delete()
        return Response({
            'success': True,
            'message': 'Student deleted successfully'
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def student_upload_profile_pic_view(request, student_id):
    """
    Upload profile picture for student
    POST /api/students/<id>/upload-profile-pic/
    Body: multipart/form-data with 'profile_pic' file
    """
    student = get_object_or_404(Student, id=student_id, user=request.user)
    
    if 'profile_pic' not in request.FILES:
        return Response({
            'success': False,
            'message': 'No file provided'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    student.profile_pic = request.FILES['profile_pic']
    student.save()
    
    serializer = StudentSerializer(student)
    return Response({
        'success': True,
        'message': 'Profile picture uploaded successfully',
        'student': serializer.data
    }, status=status.HTTP_200_OK)
