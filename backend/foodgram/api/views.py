from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView, Response

from api.filters import IngredientsSearchFilter, RecipeFilter
from api.pagination import CustomPageNumberPagination
from api.permissions import RecipePermissions
from api.serializers import (IngredientSerializer,
                             RecipeCreateUpdateSerializer,
                             RecipeSerializerList, RecipeShortSerilizer,
                             SubscriptionListSerializer, TagSerializer)
from core import pdf
from recipes.models import (Favorite, Ingredient, IngredientRecipeRelation,
                            Recipe, ShoppingCart, Subscription, Tag)

from .mixins import ListRetrieveViewSet

User = get_user_model()


class TagViewSet(ListRetrieveViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    pagination_class = None


class IngredientViewSet(ListRetrieveViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer

    filter_backends = (IngredientsSearchFilter,)
    search_fields = ('^name',)

    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()

    permission_classes = (RecipePermissions,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeSerializerList

        return RecipeCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class SubscriptionsManageView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        pk = kwargs.get('pk')

        author = get_object_or_404(User, pk=pk)
        user = request.user

        if author == user:
            return Response(
                {'errors': '???? ???? ???????????? ?????????????????????????? ???? ????????'},
                status=status.HTTP_400_BAD_REQUEST)

        if Subscription.objects.filter(author=author, user=user).exists():
            return Response(
                {'errors': '???? ?????? ?????????????????? ???? ?????????? ????????????????????????'},
                status=status.HTTP_400_BAD_REQUEST)

        obj = Subscription(author=author, user=user)
        obj.save()

        serializer = SubscriptionListSerializer(
            author, context={'request': request})

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        pk = kwargs.get('pk')

        user = request.user
        author = get_object_or_404(User, id=pk)

        try:
            Subscription.objects.get(author=author, user=user).delete()
        except Subscription.DoesNotExist:
            return Response(
                {'errors': '???? ???? ?????????????????? ???? ?????????? ????????????????????????'},
                status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)


class ListFollowViewSet(generics.ListAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubscriptionListSerializer

    def get_queryset(self):
        user = self.request.user
        return User.objects.filter(subscripters__user=user)


def make_pdf(header, data, filename, http_status):
    site_name = settings.SITE_NAME

    pdf_data = [
        (pdf.Constant.DT_CAPTION, '?????? ???????????? ??????????????:'),
        (pdf.Constant.DT_EMPTYLINE, '')
    ]

    for ingredient in data:
        pdf_data.append((
            pdf.Constant.DT_TEXT,
            '??? {name} - {amount} {unit}'.format(
                name=ingredient['ingredient__name'],
                amount=ingredient['amount_sum'],
                unit=ingredient['ingredient__measurement_unit']
            )))

    pdf_obj = pdf.PDFMaker()
    pdf_obj.data = pdf_data
    pdf_obj.footer_text = f'???????????? ?????????????? ???????????????????????? ???? ?????????? {site_name}'

    content = pdf_obj.pdf_render()

    response = HttpResponse(
        content=content,
        content_type='application/pdf',
        status=http_status)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def download_shopping_cart(request):
    recipes = request.user.shopping_cart.all().values('recipe_id')
    ingredients = IngredientRecipeRelation.objects.filter(recipe__in=recipes)

    if not ingredients:
        return Response(
            {'errors': '?????? ???????????? ?????? ?????????????? ????????????'},
            status=status.HTTP_204_NO_CONTENT)

    total_ingredients = ingredients.values(
        'ingredient__name', 'ingredient__measurement_unit').order_by(
        'ingredient__name').annotate(amount_sum=Sum('amount'))

    return make_pdf(
        ('????????????????????????', '????????????????????', '????.??????????????????'), total_ingredients,
        'shoppingcart.pdf', status.HTTP_200_OK)


class ShoppingCartManageView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    main_model = ShoppingCart
    err_messages = {
        'recipe_not_in_list': '?????????? ?????????????? ?????? ?? ?????????? ???????????? ??????????????',
        'recipe_in_list': '???????? ???????????? ?????? ?? ?????????? ???????????? ??????????????'
    }

    def post(self, request, *args, **kwargs):
        pk = kwargs.get('pk', None)

        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if self.main_model.objects.filter(recipe=recipe, user=user).exists():
            return Response(
                {'errors': self.err_messages['recipe_in_list']},
                status=status.HTTP_400_BAD_REQUEST)

        obj = self.main_model(recipe=recipe, user=user)
        obj.save()

        serializer = RecipeShortSerilizer(recipe)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        pk = kwargs.get('pk', None)

        recipe = get_object_or_404(Recipe, id=pk)

        try:
            self.main_model.objects.get(
                recipe=recipe, user=request.user).delete()
        except self.main_model.DoesNotExist:
            return Response(
                {'errors': self.err_messages['recipe_not_in_list']},
                status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteManageView(ShoppingCartManageView):
    main_model = Favorite
    err_messages = {
        'recipe_not_in_list': '?????????? ?????????????? ?????? ?? ?????????? ??????????????????',
        'recipe_in_list': '???????? ???????????? ?????? ?? ?????????? ??????????????????'
    }
