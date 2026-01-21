from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from ..models import Batch
from ..serializers import BatchSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def batch_list_create_view(request):
    """
    GET /api/batches/ - List all batches for current user
    POST /api/batches/ - Create a new batch
    Headers: Authorization: Bearer <access_token>
    
    POST Body: {
        "name": "Class 10 - Science",
        "timing": "4:00 PM"
    }
    """
    if request.method == 'GET':
        batches = Batch.objects.filter(user=request.user)
        serializer = BatchSerializer(batches, many=True)
        return Response({
            'success': True,
            'count': batches.count(),
            'batches': serializer.data
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = BatchSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                'success': True,
                'message': 'Batch created successfully',
                'batch': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Batch creation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def batch_detail_view(request, batch_id):
    """
    GET /api/batches/<id>/ - Get batch details
    PUT/PATCH /api/batches/<id>/ - Update batch
    DELETE /api/batches/<id>/ - Delete batch
    Headers: Authorization: Bearer <access_token>
    """
    batch = get_object_or_404(Batch, id=batch_id, user=request.user)
    
    if request.method == 'GET':
        serializer = BatchSerializer(batch)
        return Response({
            'success': True,
            'batch': serializer.data
        }, status=status.HTTP_200_OK)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = BatchSerializer(batch, data=request.data, partial=request.method == 'PATCH')
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Batch updated successfully',
                'batch': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Batch update failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        batch.delete()
        return Response({
            'success': True,
            'message': 'Batch deleted successfully'
        }, status=status.HTTP_200_OK)