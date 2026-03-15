from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth import get_user_model


class SocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        """
        Called after a successful OAuth handshake, before allauth creates
        or logs in the user.

        Goal: if an account with the same email already exists (e.g. the
        superuser registered via email+password), attach this social login
        to that account silently — no intermediate form, no axes trigger.

        Why NOT sociallogin.connect() here:
            connect() internally calls perform_login() → Django login() →
            axes intercepts it and can return 401. We avoid that entirely by
            only setting sociallogin.user; allauth's own pipeline will call
            perform_login() at the right moment, after axes has already been
            satisfied by the whitelist.
        """
        if sociallogin.is_existing:
            # Already linked to an account — nothing to do.
            return

        email = (sociallogin.account.extra_data.get('email') or '').strip().lower()
        if not email:
            return

        User = get_user_model()
        try:
            existing_user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Brand-new user — allauth will create them via save_user().
            return

        # Point this social login at the existing user.
        # allauth will create the SocialAccount row and log the user in.
        sociallogin.user = existing_user

    def is_auto_signup_allowed(self, request, sociallogin):
        # Google/GitHub have already verified the email — skip the signup form.
        return True

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        if not user.full_name:
            extra = sociallogin.account.extra_data
            first = extra.get('given_name') or extra.get('first_name', '')
            last  = extra.get('family_name') or extra.get('last_name', '')
            full  = f'{first} {last}'.strip() or extra.get('name', '') or user.email
            if full:
                user.full_name = full

        user.is_approved = True
        user.save(update_fields=['full_name', 'is_approved'])
        return user

    def get_connect_redirect_url(self, request, socialaccount):
        return '/accounts/oauth/success/'


class AccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        return '/accounts/oauth/success/'
