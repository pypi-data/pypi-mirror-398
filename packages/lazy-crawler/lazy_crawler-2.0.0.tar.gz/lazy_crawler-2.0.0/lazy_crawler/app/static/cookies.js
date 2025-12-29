/**
 * Cookie Consent Manager
 */
class CookieConsent {
    constructor() {
        this.banner = document.getElementById('cookie-consent-banner');
        this.acceptBtn = document.getElementById('cookie-accept');
        this.prefsBtn = document.getElementById('cookie-preferences');
        this.cookieName = 'crawlio_cookie_consent';

        if (this.banner && !this.getCookie(this.cookieName)) {
            this.init();
        }
    }

    init() {
        // Delay appearance slightly for better UX
        setTimeout(() => {
            this.banner.style.display = 'block';
        }, 1000);

        this.acceptBtn.addEventListener('click', () => this.acceptAll());
        this.prefsBtn.addEventListener('click', () => this.openPreferences());
    }

    acceptAll() {
        this.setCookie(this.cookieName, 'accepted', 365);
        this.banner.style.opacity = '0';
        setTimeout(() => {
            this.banner.style.display = 'none';
        }, 500);
    }

    openPreferences() {
        // In a real app, this would open a modal
        alert('Cookie preferences would be managed here.');
    }

    setCookie(name, value, days) {
        let expires = "";
        if (days) {
            const date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = "; expires=" + date.toUTCString();
        }
        document.cookie = name + "=" + (value || "") + expires + "; path=/; SameSite=Lax";
    }

    getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) == ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }
}

// Initialize on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    new CookieConsent();
});
