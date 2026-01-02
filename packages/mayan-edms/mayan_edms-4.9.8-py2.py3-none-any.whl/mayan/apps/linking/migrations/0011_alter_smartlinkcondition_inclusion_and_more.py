from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('linking', '0010_auto_20191213_0044')
    ]

    operations = [
        migrations.AlterField(
            model_name='smartlinkcondition', name='inclusion',
            field=models.CharField(
                choices=[('&', 'and'), ('|', 'or')], default='&',
                help_text='The inclusion is ignored for the first item.',
                max_length=16, verbose_name='Inclusion')
        ),
        migrations.AlterField(
            model_name='smartlinkcondition', name='operator',
            field=models.CharField(
                choices=[
                    ('exact', 'is equal to'),
                    ('iexact', 'is equal to (case insensitive)'),
                    ('contains', 'contains'),
                    ('icontains', 'contains (case insensitive)'),
                    ('in', 'is in'), ('gt', 'is greater than'),
                    ('gte', 'is greater than or equal to'),
                    ('lt', 'is less than'),
                    ('lte', 'is less than or equal to'),
                    ('startswith', 'starts with'),
                    ('istartswith', 'starts with (case insensitive)'),
                    ('endswith', 'ends with'),
                    ('iendswith', 'ends with (case insensitive)'),
                    ('regex', 'is in regular expression'),
                    ('iregex', 'is in regular expression (case insensitive)')
                ], max_length=16, verbose_name='Operator'
            )
        )
    ]
