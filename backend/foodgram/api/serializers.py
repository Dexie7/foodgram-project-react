import djoser.serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.settings import api_settings

from recipes.models import (Favorite, Ingredient, IngredientRecipeRelation,
                            Recipe, ShoppingCart, Subscription, Tag)
from drf_extra_fields.fields import Base64ImageField

User = get_user_model()


def short_check(request, obj, model):
    return (request.user.is_authenticated and model.objects.filter(
            user=request.user, author=obj).exists())


class CustomUserCreateSerializer(djoser.serializers.UserCreateSerializer):
    id = serializers.PrimaryKeyRelatedField(
        required=False, queryset=User.objects.all())

    class Meta:
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'password')
        model = User


class AuthorSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        request = self.context['request']
        return short_check(request, obj, Subscription)

    class Meta:
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed')
        model = User


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredient


class IngredientRecipeRelationSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient', queryset=Ingredient.objects.all())
    name = serializers.StringRelatedField(source='ingredient.name')
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit')

    class Meta:
        fields = ('id', 'name', 'measurement_unit', 'amount')
        model = IngredientRecipeRelation


class RecipeSerializerList(serializers.ModelSerializer):
    author = AuthorSerializer(required=False, many=False, read_only=True)
    tags = TagSerializer(required=False, many=True, read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def check_user_recipe_in_model(self, obj, model):
        if not self.context['request'].user.is_authenticated:
            return False

        return model.objects.filter(
            recipe=obj, user=self.context['request'].user).exists()

    def get_is_in_shopping_cart(self, obj):
        return self.check_user_recipe_in_model(obj, ShoppingCart)

    def get_is_favorited(self, obj):
        return self.check_user_recipe_in_model(obj, Favorite)

    def get_ingredients(self, obj):
        return IngredientRecipeRelationSerializer(
            IngredientRecipeRelation.objects.filter(recipe=obj).all(),
            many=True).data

    class Meta:
        exclude = ('created', )
        model = Recipe


class RecipeCreateIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        fields = ('id', 'amount')
        model = IngredientRecipeRelation


class CustomUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        if 'request' not in self.context:
            return False
        if not self.context['request'].user.is_authenticated:
            return False
        return Subscription.objects.filter(
            author=obj, user=self.context['request'].user).exists()

    class Meta:
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed')
        model = User


class RecipeShortSerilizer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'image', 'name', 'cooking_time')
        model = Recipe


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = RecipeCreateIngredientSerializer(many=True)
    image = Base64ImageField()
    author = CustomUserSerializer(required=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def check_user_recipe_in_model(self, obj, model):
        if not self.context['request'].user.is_authenticated:
            return False

        return model.objects.filter(
            recipe=obj, user=self.context['request'].user).exists()

    def get_is_in_shopping_cart(self, obj):
        return self.check_user_recipe_in_model(obj, ShoppingCart)

    def get_is_favorited(self, obj):
        return self.check_user_recipe_in_model(obj, Favorite)

    def create_ingredients(self, ingredients, obj):
        IngredientRecipeRelation.objects.bulk_create([
            IngredientRecipeRelation(
                recipe=obj,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ])

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        obj = Recipe.objects.create(**validated_data)
        obj.tags.set(tags)
        self.create_ingredients(ingredients, obj)
        return obj

    def validate(self, data):
        keys = ('ingredients', 'tags', 'text', 'name', 'cooking_time')
        errors = {}
        for key in keys:
            if key not in data:
                errors.update({key: '???????????????????????? ????????'})
        if errors:
            raise serializers.ValidationError(errors, code='field_error')
        ingredients = self.initial_data.get('ingredients')
        unique_ingredients = []
        for ingredient in ingredients:
            if ingredient['id'] in unique_ingredients:
                raise serializers.ValidationError(
                    '?????????????????????? ???? ???????????? ??????????????????????')
            unique_ingredients.append(ingredient['id'])
        try:
            if int(ingredient.get('amount')) <= 0:
                raise serializers.ValidationError(
                    '???????????????????? ???????????? ???????? ??????????????????????????')
        except Exception:
            raise serializers.ValidationError(
                    {'amount': '???????????????????? ???????????? ???????? ?????????????????????????? ????????????'})
        return data

    @transaction.atomic
    def update(self, instance, validated_data):
        obj = instance
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        super().update(instance, validated_data)
        instance.tags.set(tags)
        instance.image = validated_data.get('image', instance.image)
        instance.ingredients.clear()
        IngredientRecipeRelation.objects.filter(recipe=obj).delete()
        self.create_ingredients(ingredients, instance)
        return instance

    def to_representation(self, instance):
        self.fields.pop('ingredients')
        self.fields['tags'] = TagSerializer(many=True)
        representation = super().to_representation(instance)
        representation['ingredients'] = IngredientRecipeRelationSerializer(
            IngredientRecipeRelation.objects.filter(
                recipe=instance).all(), many=True).data
        return representation

    class Meta:
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')
        model = Recipe


class SubscriptionListSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        recipes_limit = int(self.context['request'].GET.get(
            'recipes_limit', api_settings.PAGE_SIZE))
        user = get_object_or_404(User, pk=obj.pk)
        recipes = Recipe.objects.filter(author=user)[:recipes_limit]
        return RecipeShortSerilizer(recipes, many=True).data

    def get_is_subscribed(self, obj):
        request = self.context['request']
        return short_check(request, obj, Subscription)

    class Meta:
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes_count', 'recipes')
        model = User
