import getpass
import random
import string
from raystack.core.management.base import BaseCommand, CommandError

def _get_hash_password():
    """Lazy import hash_password from installed apps."""
    try:
        # Try to import from installed apps
        from raystack.conf import get_settings
        settings = get_settings()
        
        for app_path in getattr(settings, 'INSTALLED_APPS', []):
            if 'auth' in app_path.lower() and 'account' in app_path.lower():
                try:
                    # Try utils submodule
                    utils_path = app_path + '.utils'
                    module = __import__(utils_path, fromlist=['hash_password'])
                    if hasattr(module, 'hash_password'):
                        return module.hash_password
                except (ImportError, AttributeError):
                    continue
    except Exception:
        pass
    
    # If not found, raise error
    raise ImportError(
        "hash_password function not found. Make sure you have an auth app with "
        "hash_password in your INSTALLED_APPS (e.g., apps.admin.auth.accounts)."
    )


class Command(BaseCommand):
    help = (
        "Creates a superuser account (a user with all permissions). "
        "This is equivalent to calling create_user() with is_superuser=True."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            help="Username for the superuser",
        )
        parser.add_argument(
            "--email",
            help="Email address for the superuser",
        )
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_true",
            help="Tells Raystack to NOT prompt the user for input of any kind. "
            "You must use --username with --noinput, along with an option for "
            "any other required field. Superusers created with --noinput will "
            "not be able to log in until they're given a valid password.",
        )

    def handle(self, **options):
        username = options.get("username")
        email = options.get("email")
        noinput = options.get("noinput")

        # Import all models for registration in ModelMeta
        self._import_all_models()
        
        # Check model registration
        try:
            from raystack.core.database.models import ModelMeta
            self.stdout.write(f'Registered models: {len(ModelMeta._registry)}')
            for model_name, model in ModelMeta._registry.items():
                self.stdout.write(f'  - {model_name}: {model.objects}')
        except ImportError as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to import database module: {e}')
            )
            return

        # Try to get the User model - search in INSTALLED_APPS
        UserModel = None
        try:
            from raystack.conf import get_settings
            settings = get_settings()
            
            # Try to import from installed apps
            for app_path in getattr(settings, 'INSTALLED_APPS', []):
                if 'auth' in app_path.lower() and 'user' in app_path.lower():
                    try:
                        # Try models submodule
                        models_path = app_path + '.models'
                        try:
                            module = __import__(models_path, fromlist=['UserModel'])
                            if hasattr(module, 'UserModel'):
                                UserModel = module.UserModel
                                break
                        except ImportError:
                            pass
                        
                        # Try direct import
                        module = __import__(app_path, fromlist=['UserModel'])
                        if hasattr(module, 'UserModel'):
                            UserModel = module.UserModel
                            break
                    except (ImportError, AttributeError):
                        continue
            
            if not UserModel:
                raise CommandError(
                    "Could not find User model. Make sure you have a User model "
                    "defined in your apps (e.g., apps.admin.auth.users.models.UserModel)."
                )
        except ImportError:
            raise CommandError(
                "Could not import User model. Make sure your apps are properly configured."
            )

        # Try to get the Group model - search in INSTALLED_APPS
        GroupModel = None
        try:
            from raystack.conf import get_settings
            settings = get_settings()
            
            # Try to import from installed apps
            for app_path in getattr(settings, 'INSTALLED_APPS', []):
                if 'auth' in app_path.lower() and 'group' in app_path.lower():
                    try:
                        # Try models submodule
                        models_path = app_path + '.models'
                        try:
                            module = __import__(models_path, fromlist=['GroupModel'])
                            if hasattr(module, 'GroupModel'):
                                GroupModel = module.GroupModel
                                break
                        except ImportError:
                            pass
                        
                        # Try direct import
                        module = __import__(app_path, fromlist=['GroupModel'])
                        if hasattr(module, 'GroupModel'):
                            GroupModel = module.GroupModel
                            break
                    except (ImportError, AttributeError):
                        continue
            if not GroupModel:
                GroupModel = None
        except ImportError:
            GroupModel = None

        # Create the superuser
        if noinput:
            if not username:
                raise CommandError("You must use --username with --noinput.")
            if not email:
                raise CommandError("You must use --email with --noinput.")
            
            password = self._get_random_password()
            self.stdout.write(
                f"Superuser created successfully with password: {password}"
            )
        else:
            username = self._get_username(username)
            email = self._get_email(email)
            password = self._get_password()

        # Run async operations
        import asyncio
        
        async def create_superuser_sync():
            # Check if user already exists
            existing_user = await UserModel.objects.filter(email=email).first()
            if existing_user:
                raise CommandError(f"User with email '{email}' already exists.")

            # Hash the password using the unified utility
            hash_password_func = _get_hash_password()
            hashed_password = await hash_password_func(password)

            # Get or create group
            group_id = None
            if GroupModel:
                group = await GroupModel.objects.filter(id=1).first()
                if not group:
                    # Create group through ORM
                    try:
                        group = await GroupModel.objects.create(
                            name="Admin",
                            description="Administrator group"
                        )
                        group_id = group.id
                    except Exception as e:
                        # Group already exists or other error, assume ID 1
                        self.stdout.write(self.style.WARNING(f"Warning: Could not create Admin group, assuming ID 1: {e}"))
                        group_id = 1
                else:
                    group_id = group.id
            else:
                group_id = 1 # Fallback if GroupModel is not available

            # Create the superuser using ORM
            try:
                # Create user using the ORM's create method
                await UserModel.objects.create(
                    name=username,
                    email=email,
                    password_hash=hashed_password,
                    age=0, # Default value, adjust as needed
                    organization="Admin",
                    group=group_id,
                    is_active=True,
                    is_superuser=True
                )
                self.stdout.write(f"Superuser '{username}' created successfully.")
            except Exception as e:
                raise CommandError(f"Error creating superuser: {e}")

        # Run the sync function
        # Temporarily override should_use_async to use synchronous operations
        try:
            import raystack.core.database.query
            original_should_use_async = raystack.core.database.query.should_use_async
        except ImportError as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to import database module: {e}')
            )
            return
        
        def force_sync():
            return False
        
        raystack.core.database.query.should_use_async = force_sync
        
        try:
            asyncio.get_event_loop().run_until_complete(create_superuser_sync())
        finally:
            # Restore original function
            raystack.core.database.query.should_use_async = original_should_use_async
    
    def _import_all_models(self):
        """Imports all models for registration in ModelMeta"""
        try:
            # Import models from contrib
            # Try to import auth models from installed apps
            try:
                from raystack.conf import get_settings
                settings = get_settings()
                for app_path in getattr(settings, 'INSTALLED_APPS', []):
                    if 'auth' in app_path.lower():
                        try:
                            # Try to import models submodule
                            models_path = app_path + '.models'
                            __import__(models_path)
                        except ImportError:
                            pass
            except Exception:
                pass
            # Admin models are now in project apps, not in framework
            
            # Import models from project apps
            try:
                import apps.home.models
            except ImportError:
                pass
                
        except ImportError as e:
                            self.stdout.write(
                    self.style.WARNING(f'Warning: failed to import some models: {e}')
                )

    def _get_username(self, username=None):
        """Get username from user input."""
        while not username:
            username = input("Username: ").strip()
            if not username:
                self.stdout.write("Username cannot be blank.")
        return username

    def _get_email(self, email=None):
        """Get email from user input."""
        while not email:
            email = input("Email address: ").strip()
            if not email:
                self.stdout.write("Email address cannot be blank.")
            elif "@" not in email:
                self.stdout.write("Enter a valid email address.")
                email = ""
        return email

    def _get_password(self):
        """Get password from user input."""
        while True:
            password = getpass.getpass("Password: ")
            if not password:
                self.stdout.write("Password cannot be blank.")
                continue
            
            password_confirm = getpass.getpass("Password (again): ")
            if password != password_confirm:
                self.stdout.write("Passwords don't match.")
                continue
            
            if len(password) < 8:
                self.stdout.write(
                    "Password is too short. It must contain at least 8 characters."
                )
                continue
            
            return password

    def _get_random_password(self):
        """Generate a random password for --noinput mode."""
        # Generate a random password
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(random.choice(chars) for _ in range(12))
        return password 