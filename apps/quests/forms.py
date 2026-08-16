from django import forms

from apps.quests.models import Challenge, Quest


class ChallengeMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, challenge):
        return f"{challenge.name} — {challenge.get_difficulty_display()} · {challenge.xp_value} XP"


class QuestForm(forms.ModelForm):
    """
    Only exposes challenge selection. `user` and `game` are set by the view
    (game comes from ?game=<slug>, user from request.user) — neither should
    be user-editable form fields.
    """

    challenges = ChallengeMultipleChoiceField(
        queryset=Challenge.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Optional - pick any challenges you want to attach to this quest.",
    )

    class Meta:
        model = Quest
        fields = ()
