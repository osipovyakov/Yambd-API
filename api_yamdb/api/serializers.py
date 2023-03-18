import re

from django.http import Http404
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from reviews.models import Category, Comment, Genre, Review, Title, User


class SignupSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=254)

    def validate_username(self, value):
        pattern = re.compile('^[\\w]{3,}')
        if re.match(pattern=pattern, string=value) is None:
            raise serializers.ValidationError('Имя запрещено!')

        if value == 'me':
            raise serializers.ValidationError('Имя "me" запрещено!')
        return value

    def validate(self, data):
        username = data.get('username', None)
        email = data.get('email', None)

        if User.objects.filter(email=email, username=username).exists():
            return data

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                'email занят.'
            )
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                'username занят.'
            )
        return data

    class Meta:
        model = User
        fields = ('username', 'email',)


class UserSerializer(serializers.ModelSerializer):

    def validate_username(self, value):
        pattern = re.compile('^[\\w]{3,}')
        if re.match(pattern=pattern, string=value) is None:
            raise serializers.ValidationError('Имя запрещено!')
        if value.lower() == 'me':
            raise serializers.ValidationError(
                'username не может быть me, Me, ME, mE'
            )
        return value

    def validate_email(self, value):
        if len(value) >= 254:
            raise serializers.ValidationError(
                'email слишком длинный!'
            )
        return value

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role',
        )
        lookup_field = 'username'
        read_only_fields = ('password',)


class TokenSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, write_only=True)
    confirmation_code = serializers.CharField(max_length=50, write_only=True,
                                              source='password')
    token = serializers.CharField(max_length=255, read_only=True)

    def validate_username(self, value):
        if not User.objects.filter(username=value).exists():
            raise Http404('Пользователь не найден!')
        pattern = re.compile('^[\\w]{3,}')
        if not pattern.match(value):
            raise serializers.ValidationError('Имя запрещено!')
        return value

    class Meta:
        model = User
        fields = ('username', 'confirmation_code')


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('name', 'slug',)


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genre
        fields = ('name', 'slug',)


class TitleReadSerializer(serializers.ModelSerializer):
    genre = GenreSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = Title
        fields = (
            'id',
            'name',
            'year',
            'category',
            'genre',
            'description',
            'rating',
        )


class TitleRecSerializer(serializers.ModelSerializer):
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(), slug_field='slug', many=True
    )
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(), slug_field='slug'
    )

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'category', 'genre', 'description',)


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )
    default = serializers.CurrentUserDefault()

    def validate(self, data):
        request = self.context['request']
        author = request.user
        title_id = self.context.get('view').kwargs.get('title_id')
        title = get_object_or_404(Title, pk=title_id)
        if (
            request.method == 'POST'
            and Review.objects.filter(title=title, author=author).exists()
        ):
            raise serializers.ValidationError(
                'Можно оставить только один отзыв'
            )
        return data

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date', 'title')


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')
