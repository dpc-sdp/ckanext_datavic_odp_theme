ckan.module('-datavic-odp-auth-login-form', function ($){
    setTimeout(() => {
        const authLoginFormModule = ckan.module.registry["auth-login-form"];
        if (!authLoginFormModule) return;
    
        const modulePrototype = authLoginFormModule.prototype;
        const originalShowError = modulePrototype._showError;

        if (originalShowError) {
            modulePrototype._showError = function(message) {
                const errorMessages = {
                    "Invalid reCAPTCHA": "CAPTCHA verification failed. Please try again.",
                    "Invalid login or password": "Login failed. Incorrect username or password.",
                    "The verification code is invalid": "Invalid verification code. Please request a new code.",
                    "The verification code has expired": "Invalid verification code. Please request a new code."
                };

                message = errorMessages[message] || message;
                return originalShowError.call(this, message);
            };
        }
    }, 100);
})
