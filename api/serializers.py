from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Batch, Student, Attendance, AttendanceRecord, FeePayment, Test, TestMark
import uuid


class UserSerializer(serializers.ModelSerializer):
    phone = serializers.CharField()
    
    class Meta:
        model = User
        fields = ['id', 'phone', 'name', 'institute_name', 'email', 'created_at']
        read_only_fields = ['id', 'created_at']


class RegisterSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['phone', 'name', 'institute_name', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            phone=validated_data['phone'],
            password=validated_data['password'],
            name=validated_data['name'],
            institute_name=validated_data['institute_name'],
            email=validated_data.get('email', '')
        )
        return user


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    
    def validate(self, data):
        phone = data.get('phone')
        password = data.get('password')
        
        if phone and password:
            user = authenticate(request=self.context.get('request'), username=phone, password=password)
            
            if not user:
                raise serializers.ValidationError('Invalid phone number or password.')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            
        else:
            raise serializers.ValidationError('Must include "phone" and "password".')
        
        data['user'] = user
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)


class BatchSerializer(serializers.ModelSerializer):
    student_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Batch
        fields = ['id', 'name', 'timing', 'student_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_student_count(self, obj):
        return obj.students.count()


# class StudentSerializer(serializers.ModelSerializer):
#     batch_name = serializers.CharField(source='batch.name', read_only=True)
#     fees_due = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
#     phone = serializers.CharField()
#     profile_pic = serializers.ImageField(required=False, allow_null=True)
    
#     class Meta:
#         model = Student
#         fields = ['id', 'batch', 'batch_name', 'name', 'phone', 'roll', 'total_fees', 
#                   'fees_paid', 'fees_due', 'profile_pic', 'created_at', 'updated_at']
#         read_only_fields = ['id', 'fees_due', 'created_at', 'updated_at']



# In serializers.py - Update StudentSerializer

class StudentSerializer(serializers.ModelSerializer):
    batch_name = serializers.CharField(source='batch.name', read_only=True)
    fees_due = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    phone = serializers.CharField()
    # Make profile_pic completely optional - don't include in validation if not a file
    profile_pic = serializers.ImageField(required=False, allow_null=True, use_url=True)
    
    class Meta:
        model = Student
        fields = ['id', 'batch', 'batch_name', 'name', 'phone', 'roll', 'total_fees', 
                  'fees_paid', 'fees_due', 'profile_pic', 'created_at', 'updated_at']
        read_only_fields = ['id', 'fees_due', 'created_at', 'updated_at']
    
    def to_internal_value(self, data):
        # CRITICAL FIX: Remove profile_pic from data if it's not a valid file
        if 'profile_pic' in data:
            profile_pic = data.get('profile_pic')
            # If it's None, empty string, or not a file object, remove it
            if not profile_pic or not hasattr(profile_pic, 'read'):
                data = data.copy()
                data.pop('profile_pic', None)
        
        return super().to_internal_value(data)







class AttendanceRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    
    class Meta:
        model = AttendanceRecord
        fields = ['id', 'student', 'student_name', 'status']


class AttendanceSerializer(serializers.ModelSerializer):
    records = AttendanceRecordSerializer(many=True)
    batch_name = serializers.CharField(source='batch.name', read_only=True)
    
    class Meta:
        model = Attendance
        fields = ['id', 'batch', 'batch_name', 'date', 'records', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        records_data = validated_data.pop('records')
        attendance = Attendance.objects.create(**validated_data)
        
        for record_data in records_data:
            AttendanceRecord.objects.create(attendance=attendance, **record_data)
        
        return attendance
    
    def update(self, instance, validated_data):
        records_data = validated_data.pop('records', None)
        
        instance.batch = validated_data.get('batch', instance.batch)
        instance.date = validated_data.get('date', instance.date)
        instance.save()
        
        if records_data is not None:
            # Delete existing records and create new ones
            instance.records.all().delete()
            for record_data in records_data:
                AttendanceRecord.objects.create(attendance=instance, **record_data)
        
        return instance


class FeePaymentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    
    class Meta:
        model = FeePayment
        fields = ['id', 'student', 'student_name', 'amount', 'payment_date', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']


class TestMarkSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    class Meta:
        model = TestMark
        fields = ['id', 'student', 'student_name', 'marks_obtained', 'percentage']


class TestSerializer(serializers.ModelSerializer):
    batch_name = serializers.CharField(source='batch.name', read_only=True)
    marks = TestMarkSerializer(many=True, read_only=True)
    average_marks = serializers.SerializerMethodField()
    
    class Meta:
        model = Test
        fields = ['id', 'batch', 'batch_name', 'name', 'date', 'total_marks', 'duration', 
                  'board', 'marks', 'average_marks', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_average_marks(self, obj):
        marks = obj.marks.all()
        if marks.exists():
            total = sum([float(m.marks_obtained) for m in marks])
            return round(total / marks.count(), 2)
        return 0