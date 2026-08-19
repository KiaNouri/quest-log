from django import forms

from apps.reviews.models import Review


class ReviewForm(forms.ModelForm):
    """
    `user`, `game`, and `quest` are all set by the view (from the logged-in
    user and the quest being reviewed)
    """

    class Meta:
        model = Review
        fields = ("rating", "text", "hours_played")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["text"].widget = forms.Textarea(
            attrs={"rows": 6, "placeholder": "What do you think?"}
        )
