"""Command to fill the database with demo users and recipes."""

import uuid
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag

User = get_user_model()

USERS = (
    ('elena.kozlova@yandex.ru', 'elena.kozlova', 'Елена', 'Козлова'),
    ('igor.fedorova@yandex.ru', 'igor.fedorova', 'Игорь', 'Фёдорова'),
    ('tatiana.grigorev@yandex.ru', 'tatiana.grigorev', 'Татьяна', 'Григорьев'),
    ('olga.orlova@yandex.ru', 'olga.orlova', 'Ольга', 'Орлова'),
    ('viktor.orlova@yandex.ru', 'viktor.orlova', 'Виктор', 'Орлова'),
)

# name, author, text, cooking_time, (r, g, b),
# ((ingredient, amount, unit), ...), (tag_slugs, ...)
RECIPES = (
    (
        'Классический борщ',
        'elena.kozlova',
        'Наваристый домашний борщ на говяжьем бульоне. '
        'Сварите мясо до мягкости, добавьте нарезанный картофель и капусту. '
        'Пока варятся овощи, сделайте зажарку из свёклы, моркови и лука '
        'с томатной пастой и уксусом. Соедините всё вместе, посолите, '
        'поперчите и проварите ещё 10 минут. Подавайте со сметаной '
        'и свежим укропом.',
        80,
        (150, 30, 40),
        (
            ('говядина', 400, 'г'),
            ('вода', 3000, 'мл'),
            ('картофель', 400, 'г'),
            ('капуста белокочанная', 200, 'г'),
            ('свекла', 300, 'г'),
            ('морковь', 100, 'г'),
            ('лук репчатый', 20, 'г'),
            ('чеснок', 10, 'г'),
            ('растительное масло', 30, 'мл'),
            ('томатная паста', 100, 'г'),
            ('уксус столовый', 4, 'мл'),
            ('сахар', 5, 'г'),
            ('соль', 10, 'г'),
            ('перец черный молотый', 2, 'г'),
            ('сметана', 50, 'г'),
            ('укроп', 10, 'г'),
        ),
        ('lunch',),
    ),
    (
        'Узбекский плов',
        'igor.fedorova',
        'Сытный узбекский плов из баранины с длиннозерным рисом. '
        'На дне кастрюли обжарьте мясо с луком и морковью в растительном '
        'масле, добавьте зиру, барбарис, кориандр и целый перец чили. '
        'Влейте воду, посолите и доведите до кипения, затем засыпьте рис '
        'и готовьте под крышкой на слабом огне. Перед подачей дайте плову '
        'настояться и украсьте зеленью.',
        150,
        (180, 120, 50),
        (
            ('рис длиннозерный', 250, 'г'),
            ('баранина', 500, 'г'),
            ('морковь', 250, 'г'),
            ('лук репчатый', 150, 'г'),
            ('растительное масло', 50, 'мл'),
            ('вода', 500, 'мл'),
            ('перец чили', 15, 'г'),
            ('чеснок', 5, 'г'),
            ('зира', 18, 'г'),
            ('барбарис', 18, 'г'),
            ('кориандр', 5, 'г'),
            ('соль', 10, 'г'),
            ('зелень', 10, 'г'),
        ),
        ('lunch', 'dinner'),
    ),
    (
        'Тонкие блины на молоке',
        'tatiana.grigorev',
        'Классические тонкие блины на молоке. Взбейте яйца с сахаром и солью, '
        'влейте часть молока, добавьте просеянную муку и перемешайте '
        'до однородности. Разбавьте тесто оставшимся молоком и растительным '
        'маслом, дайте постоять 10 минут и выпекайте на раскалённой сковороде.'
        ' Подавайте горячими со сливочным маслом, сметаной или вареньем.',
        30,
        (230, 180, 120),
        (
            ('молоко', 500, 'мл'),
            ('яйца куриные', 180, 'г'),
            ('мука хлебопекарная', 200, 'г'),
            ('сахар', 50, 'г'),
            ('соль', 4, 'г'),
            ('растительное масло', 34, 'мл'),
            ('сливочное масло', 30, 'г'),
        ),
        ('breakfast',),
    ),
    (
        'Классические сырники',
        'olga.orlova',
        'Нежные сырники из творога на завтрак. Смешайте творог с яйцами, '
        'сахаром, ванилином и мукой до однородного теста. Сформируйте сырники,'
        ' обваляйте в муке и обжарьте на растительном масле с двух сторон '
        'до золотистой корочки. Подавайте со сметаной, сгущёнкой'
        ' или вареньем.',
        45,
        (240, 220, 180),
        (
            ('творог', 550, 'г'),
            ('яйца куриные', 120, 'г'),
            ('сахар', 60, 'г'),
            ('мука хлебопекарная', 100, 'г'),
            ('ванилин', 5, 'г'),
            ('соль', 1, 'г'),
            ('растительное масло', 30, 'мл'),
        ),
        ('breakfast',),
    ),
    (
        'Традиционный оливье',
        'viktor.orlova',
        'Классический салат оливье с варёной колбасой. Отварите и нарежьте '
        'кубиками картофель, морковь и яйца, добавьте колбасу, солёные огурцы '
        'и зелёный горошек. Заправьте салат майонезом, посолите и поперчите '
        'по вкусу. Подавайте охлаждённым, украсив свежей зеленью.',
        50,
        (200, 190, 150),
        (
            ('картофель', 360, 'г'),
            ('морковь', 200, 'г'),
            ('яйца куриные', 360, 'г'),
            ('колбаса вареная', 300, 'г'),
            ('огурцы соленые', 180, 'г'),
            ('горошек зеленый консервированный', 300, 'г'),
            ('майонез', 300, 'г'),
            ('соль', 10, 'г'),
            ('перец черный молотый', 2, 'г'),
            ('зелень', 10, 'г'),
        ),
        ('dinner',),
    ),
    (
        'Домашние пельмени',
        'elena.kozlova',
        'Сытные домашние пельмени из свинины и говядины. '
        'Замесите крутое тесто из муки, воды, яйца и соли, '
        'дайте ему отдохнуть 30 минут. Пропустите через мясорубку свинину, '
        'говядину и лук, посолите и поперчите фарш. Раскатайте тесто, '
        'вырежьте кружки, выложите начинку и слепите пельмени. '
        'Варите в кипящей подсоленной воде 7 минут после всплытия '
        'и подавайте со сметаной и сливочным маслом.',
        120,
        (220, 160, 110),
        (
            ('мука хлебопекарная', 400, 'г'),
            ('вода', 200, 'мл'),
            ('яйца куриные', 100, 'г'),
            ('свинина', 400, 'г'),
            ('говядина', 300, 'г'),
            ('лук репчатый', 150, 'г'),
            ('соль', 10, 'г'),
            ('перец черный молотый', 3, 'г'),
            ('сливочное масло', 50, 'г'),
            ('сметана', 100, 'г'),
        ),
        ('dinner',),
    ),
    (
        'Куриный суп с лапшой',
        'olga.orlova',
        'Лёгкий куриный суп с домашней лапшой. '
        'Сварите курицу до мягкости, достаньте мясо и разберите его. '
        'В бульон добавьте нарезанный картофель и обжаренные с луком '
        'морковь. Верните мясо, засыпьте лапшу и варите до готовности. '
        'Посолите, поперчите, добавьте лавровый лист и свежий укроп. '
        'Подавайте горячим.',
        60,
        (200, 150, 90),
        (
            ('курица', 500, 'г'),
            ('вода', 2000, 'мл'),
            ('картофель', 300, 'г'),
            ('морковь', 100, 'г'),
            ('лук репчатый', 80, 'г'),
            ('лапша', 150, 'г'),
            ('соль', 10, 'г'),
            ('перец черный молотый', 2, 'г'),
            ('укроп', 10, 'г'),
            ('лавровый лист', 2, 'г'),
        ),
        ('lunch',),
    ),
    (
        'Драники картофельные',
        'viktor.orlova',
        'Хрустящие драники из картофеля. Натрите картофель на мелкой тёрке, '
        'отожмите лишнюю жидкость, добавьте тёртый лук, яйцо, муку и соль. '
        'Хорошо перемешайте и выложите ложкой на раскалённую сковороду '
        'с растительным маслом. Обжарьте с двух сторон до золотистой '
        'корочки. Подавайте горячими со сметаной и чесноком.',
        40,
        (180, 130, 80),
        (
            ('картофель', 600, 'г'),
            ('лук репчатый', 100, 'г'),
            ('яйца куриные', 60, 'г'),
            ('мука хлебопекарная', 40, 'г'),
            ('соль', 5, 'г'),
            ('растительное масло', 30, 'мл'),
            ('сметана', 100, 'г'),
            ('чеснок', 10, 'г'),
        ),
        ('dinner',),
    ),
)

IMAGE_WIDTH = 1200
IMAGE_HEIGHT = 800
MAX_RGB_CHANNEL = 255


class Command(BaseCommand):
    """Fill the database with demo users and recipes."""

    help = 'Fill the database with demo users and recipes.'

    def handle(self, *args, **options):
        """Create users, recipes, images and recipe ingredients."""
        users = self._create_users()
        self._create_recipes(users)
        users_count = len(users)
        recipes_count = len(RECIPES)
        message = (
            'Demo data ready: ' + str(users_count) + ' users, '
            + str(recipes_count) + ' recipes.'
        )
        self.stdout.write(self.style.SUCCESS(message))

    def _create_users(self):
        """Create demo users idempotently and return a username map."""
        users = {}
        for email, username, first_name, last_name in USERS:
            user, _ = User.objects.get_or_create(
                email=email,
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                },
            )
            user.set_password('MySecretPas$word')
            user.save()
            users[username] = user
        return users

    def _create_recipes(self, users):
        """Create demo recipes with generated images idempotently."""
        for name, author_username, text, cooking_time, rgb, ingredients, \
                tag_slugs in RECIPES:
            recipe, created = Recipe.objects.get_or_create(
                name=name,
                defaults={
                    'author': users[author_username],
                    'text': text,
                    'cooking_time': cooking_time,
                },
            )
            if created:
                image_code = uuid.uuid4().hex[:8]
                recipe.image.save(
                    'recipe_' + image_code + '.jpg',
                    self._make_image(rgb),
                )
            recipe.tags.set(Tag.objects.filter(slug__in=tag_slugs))
            self._set_ingredients(recipe, ingredients)
            recipe.save()

    def _set_ingredients(self, recipe, ingredients):
        """Replace the recipe ingredients with the given ones."""
        recipe.recipe_ingredients.all().delete()
        rows = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=unit,
                )[0],
                amount=amount,
            )
            for name, amount, unit in ingredients
        ]
        RecipeIngredient.objects.bulk_create(rows)

    @staticmethod
    def _make_image(rgb):
        """Generate a vertical gradient JPEG image."""
        image = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT))
        draw = ImageDraw.Draw(image)
        base = tuple(MAX_RGB_CHANNEL - channel for channel in rgb)
        for y_index in range(IMAGE_HEIGHT):
            ratio = y_index / IMAGE_HEIGHT
            color = tuple(
                int(channel + (target - channel) * ratio)
                for channel, target in zip(rgb, base)
            )
            draw.line(
                ((0, y_index), (IMAGE_WIDTH, y_index)),
                fill=color,
            )
        buffer = BytesIO()
        image.save(buffer, format='JPEG')
        return ContentFile(buffer.getvalue())
