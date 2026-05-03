from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from SIGLO.mock_utils import MockModel

class MockUser(MockModel):
    is_active = True
    is_staff = True
    is_superuser = False
    
    def get_full_name(self):
        return f"{getattr(self, 'first_name', '')} {getattr(self, 'last_name', '')}".strip() or self.username
    
    def check_password(self, password):
        return password == getattr(self, 'mock_password', 'admin123')
    
    def has_perm(self, perm, obj=None):
        return self.is_superuser or (self.is_staff and self.role in ['ADMIN', 'EXECUTIVE'])
    
    def has_module_perms(self, app_label):
        return self.is_superuser or (self.is_staff and self.role in ['ADMIN', 'EXECUTIVE'])

MOCK_USERS = {
    'admin': MockUser(id=1, username='admin', email='admin@siglo.com', role='ADMIN', first_name='Admin', last_name='Siglo', mock_password='admin123'),
    'client': MockUser(id=2, username='client', email='client@siglo.com', role='CLIENT', first_name='Juan', last_name='Perez', mock_password='client123'),
}

class MockBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Allow login by username or email
        user = MOCK_USERS.get(username)
        if not user:
            # Check by email
            for u in MOCK_USERS.values():
                if u.email == username:
                    user = u
                    break
        
        if user and user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        user_id = int(user_id)
        for user in MOCK_USERS.values():
            if user.id == user_id:
                return user
        return None
