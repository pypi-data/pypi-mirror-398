from rest_framework import authentication, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from dictionary.models import Entry
from dictionary.replacement import replace


class ReplaceAPIView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        text = request.data.get("text")
        if not isinstance(text, str):
            return Response(
                {"detail": "text is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        include_categories = request.data.get("include_categories") or []
        exclude_categories = request.data.get("exclude_categories") or []

        if include_categories and not isinstance(include_categories, list):
            return Response(
                {"detail": "include_categories must be a list"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if exclude_categories and not isinstance(exclude_categories, list):
            return Response(
                {"detail": "exclude_categories must be a list"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        entries = Entry.objects.filter(is_active=True)
        if include_categories:
            entries = entries.filter(category__in=include_categories)
        elif exclude_categories:
            entries = entries.exclude(category__in=exclude_categories)

        output = replace(text, entries=entries.iterator())
        return Response({"text": output})


class CategoriesAPIView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        categories = list(
            Entry.objects.filter(is_active=True)
            .values_list("category", flat=True)
            .distinct()
            .order_by("category")
        )
        return Response({"categories": categories})
