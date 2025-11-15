from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Habit


class HabitSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Habit
        fields = (
            "id",
            "user",
            "place",
            "action",
            "is_pleasant",
            "related_habit",
            "reward",
            "is_public",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def validate_related_habit(self, value: Habit | None) -> Habit | None:
        request = self.context["request"]
        if value and value.user != request.user:
            raise serializers.ValidationError(
                "Связанные привычки должны принадлежать пользователю."
            )
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        base_data = {}
        if self.instance:
            for field in self.instance._meta.concrete_fields:
                if (
                    field.is_relation
                    and field.many_to_one
                    and field.remote_field.parent_link
                ):
                    continue
                if field.attname == "id":
                    continue
                base_data[field.name] = getattr(self.instance, field.name)

        data = {**base_data, **attrs}
        if "user" not in data:
            data["user"] = self.context["request"].user

        instance = Habit(**data)
        try:
            instance.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict or exc.messages)
        return attrs

    def create(self, validated_data):
        return Habit.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
