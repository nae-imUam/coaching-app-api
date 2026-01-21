from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Batch, Student, Attendance, AttendanceRecord, FeePayment, Test, TestMark


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['phone', 'name', 'institute_name', 'is_active', 'is_staff', 'created_at']
    list_filter = ['is_active', 'is_staff', 'created_at']
    search_fields = ['phone', 'name', 'institute_name', 'email']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal Info', {'fields': ('name', 'institute_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'name', 'institute_name', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'timing', 'student_count', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['name', 'user__name', 'user__institute_name']
    readonly_fields = ['created_at', 'updated_at']
    
    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = 'Students'


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['name', 'roll', 'batch', 'phone', 'total_fees', 'fees_paid', 'fees_due', 'created_at']
    list_filter = ['batch', 'created_at', 'user']
    search_fields = ['name', 'roll', 'phone', 'user__name']
    readonly_fields = ['created_at', 'updated_at', 'fees_due']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['batch', 'date', 'user', 'record_count', 'created_at']
    list_filter = ['date', 'batch', 'user', 'created_at']
    search_fields = ['batch__name', 'user__name']
    readonly_fields = ['created_at', 'updated_at']
    
    def record_count(self, obj):
        return obj.records.count()
    record_count.short_description = 'Records'


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'attendance', 'status']
    list_filter = ['status', 'attendance__date']
    search_fields = ['student__name', 'attendance__batch__name']


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ['student', 'amount', 'payment_date', 'user', 'created_at']
    list_filter = ['payment_date', 'created_at', 'user']
    search_fields = ['student__name', 'user__name', 'notes']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ['name', 'batch', 'date', 'total_marks', 'duration', 'board', 'created_at']
    list_filter = ['date', 'board', 'batch', 'user', 'created_at']
    search_fields = ['name', 'batch__name', 'user__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TestMark)
class TestMarkAdmin(admin.ModelAdmin):
    list_display = ['student', 'test', 'marks_obtained', 'percentage', 'created_at']
    list_filter = ['test', 'created_at']
    search_fields = ['student__name', 'test__name']
    readonly_fields = ['created_at', 'updated_at', 'percentage']