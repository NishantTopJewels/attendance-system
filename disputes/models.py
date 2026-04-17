from django.db import models
from students.models import Student
from attendance.models import Attendance

class Dispute(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='disputes')
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='disputes')
    date = models.DateField()
    reason = models.TextField()
    proof = models.FileField(upload_to='disputes/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'date'], name='unique_student_date_dispute')
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Dispute by {self.student.first_name} for {self.date}"
