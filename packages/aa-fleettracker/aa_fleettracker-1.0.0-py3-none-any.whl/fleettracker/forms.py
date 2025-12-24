from django import forms

class TakeSnapshotForm(forms.Form):
    label = forms.CharField(
        required=False,
        max_length=120,
        help_text="Optional fleet name.",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "np. BLOPS formup"}),
    )
