from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone
import uuid


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('Users must have a phone number')
        
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = PhoneNumberField(unique=True, region='IN')
    name = models.CharField(max_length=255)
    institute_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Password reset
    reset_token = models.CharField(max_length=100, blank=True, null=True)
    reset_token_created = models.DateTimeField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['name', 'institute_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.name} - {self.phone}"


class Batch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='batches')
    name = models.CharField(max_length=255)
    timing = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'batches'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Student(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='students')
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, related_name='students')
    
    name = models.CharField(max_length=255)
    phone = PhoneNumberField(region='IN')
    roll = models.CharField(max_length=50, blank=True)
    
    total_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fees_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    profile_pic = models.ImageField(upload_to='student_profiles/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'students'
        ordering = ['name']
        unique_together = ['user', 'roll']

    def __str__(self):
        return f"{self.name} - {self.roll}"

    @property
    def fees_due(self):
        return self.total_fees - self.fees_paid


class Attendance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendances'
        ordering = ['-date']
        unique_together = ['user', 'batch', 'date']

    def __str__(self):
        return f"{self.batch.name} - {self.date}"


class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='records')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='absent')

    class Meta:
        db_table = 'attendance_records'
        unique_together = ['attendance', 'student']

    def __str__(self):
        return f"{self.student.name} - {self.status}"


class FeePayment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fee_payments')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fee_payments'
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.student.name} - ₹{self.amount}"


class Test(models.Model):
    BOARD_CHOICES = [
        ('CBSE', 'CBSE'),
        ('Bihar Board', 'Bihar Board'),
        ('ICSE', 'ICSE'),
        ('State Board', 'State Board'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tests')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='tests')
    
    name = models.CharField(max_length=255)
    date = models.DateField()
    total_marks = models.IntegerField()
    duration = models.DecimalField(max_digits=4, decimal_places=2)  # in hours
    board = models.CharField(max_length=50, choices=BOARD_CHOICES, default='CBSE')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tests'
        ordering = ['-date']

    def __str__(self):
        return self.name


class TestMark(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='marks')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='test_marks')
    
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'test_marks'
        unique_together = ['test', 'student']

    def __str__(self):
        return f"{self.student.name} - {self.marks_obtained}/{self.test.total_marks}"

    @property
    def percentage(self):
        return (self.marks_obtained / self.test.total_marks) * 100 if self.test.total_marks > 0 else 0