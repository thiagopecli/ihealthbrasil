from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0013_rename_products_car_user_id_14b744_idx_products_ca_user_id_f5341b_idx_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productpackageinsert",
            name="language",
            field=models.CharField(
                choices=[
                    ("pt_BR", "Português (Brasil)"),
                    ("en_US", "Inglês (USA)"),
                    ("es_ES", "Espanhol (Espanha)"),
                    ("fr_FR", "Frances (Franca)"),
                ],
                default="pt_BR",
                max_length=10,
            ),
        ),
    ]
