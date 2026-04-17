from django import forms
from .models import Dispute

class DisputeForm(forms.ModelForm):
    class Meta:
        model = Dispute
        fields = ['reason', 'proof']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe why this attendance should be corrected...'}),
        }
