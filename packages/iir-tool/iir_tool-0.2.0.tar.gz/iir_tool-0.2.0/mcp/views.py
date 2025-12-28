from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token

from dictionary.services.replacement import replace_text


class ReplaceAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        auth_header = request.headers.get("Authorization", "")
        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != "Token":
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        token_key = parts[1]
        if not Token.objects.filter(key=token_key).exists():
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        text = request.data.get("text")
        if not isinstance(text, str):
            return Response({"detail": "text is required"}, status=status.HTTP_400_BAD_REQUEST)

        output = replace_text(text)
        return Response({"text": output})
