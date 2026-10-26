document.addEventListener("DOMContentLoaded", function () {
    const authWrapper = document.getElementById("authWrapper");

    if (!authWrapper) {
        return;
    }

    const registerButtons = document.querySelectorAll(
        ".register-trigger"
    );

    const loginButtons = document.querySelectorAll(
        ".login-trigger"
    );

    const loginPanel = document.querySelector(
        ".credentials-panel.signin"
    );

    const registerPanel = document.querySelector(
        ".credentials-panel.signup"
    );

    const loginWelcome = document.querySelector(
        ".welcome-section.signin"
    );

    const registerWelcome = document.querySelector(
        ".welcome-section.signup"
    );

    /*
     * تحديث الحقول حتى تتحرك التسمية إلى الأعلى
     * عندما يحتوي الحقل على قيمة.
     */
    function updateFieldState(input) {
        const fieldWrapper = input.closest(".field-wrapper");

        if (!fieldWrapper) {
            return;
        }

        if (input.value.trim() !== "") {
            fieldWrapper.classList.add("has-value");
        } else {
            fieldWrapper.classList.remove("has-value");
        }
    }

    const textInputs = document.querySelectorAll(
        ".field-wrapper input"
    );

    textInputs.forEach(function (input) {
        updateFieldState(input);

        input.addEventListener("input", function () {
            updateFieldState(input);
        });

        input.addEventListener("change", function () {
            updateFieldState(input);
        });

        input.addEventListener("blur", function () {
            updateFieldState(input);
        });
    });

    /*
     * تحديد النموذج الظاهر:
     * false = تسجيل الدخول
     * true  = إنشاء حساب
     */
    function setRegisterMode(registerMode, focusField = true) {
        authWrapper.classList.toggle(
            "toggled",
            registerMode
        );

        if (loginPanel) {
            loginPanel.setAttribute(
                "aria-hidden",
                registerMode ? "true" : "false"
            );
        }

        if (registerPanel) {
            registerPanel.setAttribute(
                "aria-hidden",
                registerMode ? "false" : "true"
            );
        }

        if (loginWelcome) {
            loginWelcome.setAttribute(
                "aria-hidden",
                registerMode ? "true" : "false"
            );
        }

        if (registerWelcome) {
            registerWelcome.setAttribute(
                "aria-hidden",
                registerMode ? "false" : "true"
            );
        }

        document.title = registerMode
            ? "إنشاء حساب | CityVoice"
            : "تسجيل الدخول | CityVoice";

        if (!focusField) {
            return;
        }

        window.setTimeout(function () {
            const activePanel = registerMode
                ? registerPanel
                : loginPanel;

            const firstInput = activePanel?.querySelector(
                "input:not([type='hidden'])"
            );

            if (firstInput) {
                firstInput.focus({
                    preventScroll: true
                });
            }
        }, 700);
    }

    /*
     * الانتقال إلى إنشاء الحساب.
     */
    registerButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            setRegisterMode(true);
        });
    });

    /*
     * العودة إلى تسجيل الدخول.
     */
    loginButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            setRegisterMode(false);
        });
    });

    /*
     * إظهار وإخفاء كلمات المرور.
     */
    const passwordButtons = document.querySelectorAll(
        ".password-toggle"
    );

    passwordButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            const passwordField = button.closest(
                ".password-field"
            );

            const passwordInput = passwordField?.querySelector(
                "input"
            );

            if (!passwordInput) {
                return;
            }

            const passwordIsHidden =
                passwordInput.type === "password";

            passwordInput.type = passwordIsHidden
                ? "text"
                : "password";

            button.textContent = passwordIsHidden
                ? "إخفاء"
                : "إظهار";

            button.setAttribute(
                "aria-label",
                passwordIsHidden
                    ? "إخفاء كلمة المرور"
                    : "إظهار كلمة المرور"
            );

            passwordInput.focus({
                preventScroll: true
            });
        });
    });

    /*
     * عند رجوع المتصفح للصفحة، نعيد فحص القيم؛
     * لأن المتصفح قد يملأها تلقائيًا.
     */
    window.addEventListener("pageshow", function () {
        textInputs.forEach(function (input) {
            updateFieldState(input);
        });
    });

    /*
     * إذا كانت الصفحة تحتوي على أخطاء في إنشاء الحساب،
     * سيضع Django الفئة toggled في HTML ونبقى في نفس القسم.
     */
    const registerModeInitially =
        authWrapper.classList.contains("toggled");

    setRegisterMode(
        registerModeInitially,
        false
    );

    /*
     * إعادة فحص الحقول بعد الإكمال التلقائي من المتصفح.
     */
    window.setTimeout(function () {
        textInputs.forEach(function (input) {
            updateFieldState(input);
        });
    }, 500);
});