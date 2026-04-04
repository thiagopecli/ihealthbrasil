import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

RESULTS = []


def add_result(name, ok, detail):
    RESULTS.append((name, ok, detail))


def ensure_admin_user():
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    password = "SmokeTest@123"
    username_field = user_model.USERNAME_FIELD
    identifier_value = "smoke_admin"
    if username_field == "email":
        identifier_value = "smoke_admin@example.com"

    user = user_model.objects.filter(**{username_field: identifier_value}).first()

    if not user:
        kwargs = {username_field: identifier_value}
        required = list(getattr(user_model, "REQUIRED_FIELDS", []))
        model_fields = {field.name for field in user_model._meta.fields}

        for field in required:
            if field not in kwargs:
                if field == "email":
                    kwargs[field] = "smoke_admin@example.com"
                else:
                    kwargs[field] = f"smoke_{field}"

        if "email" in model_fields and "email" not in kwargs:
            kwargs["email"] = "smoke_admin@example.com"

        user = user_model._default_manager.create_superuser(password=password, **kwargs)
    else:
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save(update_fields=["is_staff", "is_superuser", "password"])

    return user, password, username_field, identifier_value


def main():
    from django.conf import settings
    from rest_framework.test import APIClient

    if "testserver" not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ["testserver"]

    _, password, username_field, identifier_value = ensure_admin_user()
    client = APIClient()

    response = client.get("/api/categories/")
    add_result("GET /api/categories/ (public)", response.status_code == 200, f"status={response.status_code}")

    response = client.post("/api/categories/", {"name": "cat-anon", "description": "x"}, format="json")
    add_result(
        "POST /api/categories/ sem auth bloqueado",
        response.status_code in (401, 403),
        f"status={response.status_code}",
    )

    login_payload = {username_field: identifier_value, "password": password}
    response = client.post("/api/auth/token/", login_payload, format="json")

    # Fallback para implementacoes que esperam explicitamente email/username
    if response.status_code != 200 and username_field != "email":
        response = client.post(
            "/api/auth/token/",
            {"email": "smoke_admin@example.com", "password": password},
            format="json",
        )
    if response.status_code != 200 and username_field != "username":
        response = client.post(
            "/api/auth/token/",
            {"username": "smoke_admin", "password": password},
            format="json",
        )

    access = None
    if response.status_code == 200 and isinstance(response.data, dict):
        access = response.data.get("access")

    add_result("POST /api/auth/token/", response.status_code == 200 and bool(access), f"status={response.status_code}")

    if not access:
        add_result("Fluxo autenticado", False, "Token nao obtido; testes autenticados nao executados")
        return

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    response = client.post(
        "/api/categories/",
        {"name": "analgesicos-smoke", "description": "categoria smoke"},
        format="json",
    )
    add_result("POST /api/categories/ com admin", response.status_code in (200, 201), f"status={response.status_code}")

    response = client.get("/api/products/?search=analgesico&ordering=price&page=1&page_size=10")
    add_result("GET /api/products/ com query params", response.status_code == 200, f"status={response.status_code}")

    response = client.get("/api/products/requires_prescription/")
    add_result(
        "GET /api/products/requires_prescription/", response.status_code == 200, f"status={response.status_code}"
    )

    response = client.get("/api/auth/me/")
    add_result("GET /api/auth/me/ autenticado", response.status_code == 200, f"status={response.status_code}")


if __name__ == "__main__":
    main()

    print("\n===== SMOKE TEST RESULT =====")
    for name, ok, detail in RESULTS:
        status = "OK" if ok else "FAIL"
        print(f"[{status}] {name} -> {detail}")

    failed = [item for item in RESULTS if not item[1]]
    print("-----------------------------")
    print(f"Total: {len(RESULTS)} | Falhas: {len(failed)}")
    if failed:
        print("Falhas detectadas:")
        for name, _, detail in failed:
            print(f"- {name}: {detail}")
