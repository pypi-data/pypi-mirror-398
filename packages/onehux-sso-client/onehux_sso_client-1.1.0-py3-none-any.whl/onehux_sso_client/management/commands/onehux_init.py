# onehux_sso_client/management/commands/onehux_init.py

from django.core.management.base import BaseCommand
from pathlib import Path
import shutil

class Command(BaseCommand):
    help = 'Initialize Onehux SSO in your Django project'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            type=str,
            default='accounts',
            help='Django app to create user model in (default: accounts)'
        )
    
    def handle(self, *args, **options):
        app_name = options['app']
        
        # Get template file from package
        template_path = Path(__file__).parent.parent.parent / 'templates' / 'user_model_template.py'
        
        # Destination path
        dest_path = Path.cwd() / app_name / 'models.py'
        
        if dest_path.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'{dest_path} already exists. Use --force to overwrite.'
                )
            )
            return
        
        # Create app directory if needed
        dest_path.parent.mkdir(exist_ok=True)
        
        # Copy template
        shutil.copy(template_path, dest_path)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Created user model at {dest_path}\n'
                f'\nNext steps:\n'
                f'1. Edit {dest_path} and add your custom fields\n'
                f'2. Add to settings.py: AUTH_USER_MODEL = "{app_name}.User"\n'
                f'3. Run: python manage.py makemigrations\n'
                f'4. Run: python manage.py migrate'
            )
        )




