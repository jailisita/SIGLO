from django.contrib.auth.decorators import user_passes_test

def admin_required(view_func):
    return user_passes_test(
        lambda u: u.is_authenticated and getattr(u, 'role', None) in ['ADMIN', 'EXECUTIVE'],
        login_url='/login/'
    )(view_func)


def client_required(view_func):
    return user_passes_test(
        lambda u: u.is_authenticated and getattr(u, 'role', None) == 'CLIENT',
        login_url='/login/'
    )(view_func)
