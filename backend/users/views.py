from django.contrib.auth import get_user_model
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from users.models import Subscription
from users.serializers import (
    AvatarSerializer,
    UserWithRecipesSerializer,
)

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    """User viewset extended with subscriptions and avatar."""

    def get_permissions(self):
        """Allow anonymous users to view profiles."""
        if self.action == 'retrieve':
            return [AllowAny()]
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def subscribe(self, request, id=None):
        """Subscribe the current user to another user."""
        author = self.get_object()
        user = request.user
        if user == author:
            return Response(
                {'detail': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        _, created = Subscription.objects.get_or_create(
            user=user,
            author=author,
        )
        if not created:
            return Response(
                {'detail': 'Вы уже подписаны.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = UserWithRecipesSerializer(
            author,
            context=self.get_serializer_context(),
        )
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        """Unsubscribe the current user from another user."""
        author = self.get_object()
        deleted, _ = Subscription.objects.filter(
            user=request.user,
            author=author,
        ).delete()
        if not deleted:
            return Response(
                {'detail': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        """Return users the current user is subscribed to."""
        authors = User.objects.filter(
            following__user=request.user,
        )
        page = self.paginate_queryset(authors)
        serializer = UserWithRecipesSerializer(
            page,
            many=True,
            context=self.get_serializer_context(),
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
    )
    def me_avatar(self, request):
        """Set or delete the avatar of the current user."""
        if request.method == 'DELETE':
            if request.user.avatar:
                request.user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.avatar = serializer.validated_data['avatar']
        request.user.save()
        return Response(
            {'avatar': request.user.avatar.url},
            status=status.HTTP_200_OK,
        )
