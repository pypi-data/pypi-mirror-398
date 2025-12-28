from rest_framework import authentication, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from dictionary.models import Entry
from dictionary.services.replacement_internal import replace_text_internal


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

        include_categories = request.data.get("include_categories", None)
        exclude_categories = request.data.get("exclude_categories", None)

        if include_categories is not None and not isinstance(include_categories, list):
            return Response(
                {"detail": "include_categories must be a list"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if exclude_categories is not None and not isinstance(exclude_categories, list):
            return Response(
                {"detail": "exclude_categories must be a list"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if include_categories == []:
            include_categories = None
        if exclude_categories == []:
            exclude_categories = None

        output = replace_text_internal(
            text,
            include_categories=include_categories,
            exclude_categories=exclude_categories,
        )
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
