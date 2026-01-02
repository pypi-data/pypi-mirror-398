from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('locales', '0011_alter_userlocaleprofile_language')
    ]

    operations = [
        migrations.AlterField(
            model_name='userlocaleprofile', name='language',
            field=models.CharField(
                choices=[
                    ('sq', 'Albanian'), ('ar', 'Arabic'),
                    ('ar-eg', 'Arabic (Egypt)'),
                    ('hy-am', 'Armenian (Armenia)'), ('bs', 'Bosnian'),
                    ('bg', 'Bulgarian'), ('bg-bg', 'Bulgarian (Bulgaria)'),
                    ('ca', 'Catalan'), ('zh-cn', 'Chinese (China)'),
                    ('zh-hans', 'Chinese (Simplified)'),
                    ('zh-tw', 'Chinese (Taiwan)'), ('hr', 'Croatian'),
                    ('cs', 'Czech'), ('da', 'Danish'), ('nl', 'Dutch'),
                    ('en', 'English'), ('fr', 'French'),
                    ('fr-fr', 'French (France)'), ('de', 'German'),
                    ('de-at', 'German (Austria)'),
                    ('de-de', 'German (Germany)'), ('el', 'Greek'),
                    ('el-gr', 'Greek (Greece)'), ('he-il', 'Hebrew (Israel)'),
                    ('hu', 'Hungarian'), ('hu-hu', 'Hungarian (Hungary)'),
                    ('hu-sk', 'Hungarian (Slovakia)'), ('id', 'Indonesian'),
                    ('it', 'Italian'), ('ja', 'Japanese'), ('lv', 'Latvian'),
                    ('mn-mn', 'Mongolian (Mongolia)'), ('fa', 'Persian'),
                    ('fa-ir', 'Persian (Iran)'), ('pl', 'Polish'),
                    ('pt', 'Portuguese'), ('pt-br', 'Portuguese (Brazil)'),
                    ('ro-ro', 'Romanian (Romania)'), ('ru', 'Russian'),
                    ('ru-ru', 'Russian (Russia)'), ('sl', 'Slovenian'),
                    ('es', 'Spanish'), ('es-ec', 'Spanish (Ecuador)'),
                    ('es-mx', 'Spanish (Mexico)'),
                    ('es-pr', 'Spanish (Puerto Rico)'),
                    ('es-es', 'Spanish (Spain)'), ('th', 'Thai'),
                    ('bo', 'Tibetan'), ('tr', 'Turkish'),
                    ('tr-tr', 'Turkish (Turkey)'), ('uk', 'Ukrainian'),
                    ('uk-ua', 'Ukrainian (Ukraine)'), ('vi', 'Vietnamese')
                ], max_length=8, verbose_name='Language'
            )
        )
    ]
