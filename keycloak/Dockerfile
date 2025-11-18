FROM quay.io/keycloak/keycloak:21.1.1

# (опционально) базовые переменные, если хотите задать прямо в образе
ENV KC_DB=postgres

# 1. Кладём провайдеры в /opt/keycloak/providers
# Скачайте заранее:
#  - keycloak-russian-providers-21.1.1.rsp.jar
#  - json-path-2.7.0.jar
#  - json-smart-2.4.7.jar
COPY keycloak-russian-providers.jar /opt/keycloak/providers/keycloak-russian-providers.jar
COPY json-path-2.7.0.jar /opt/keycloak/providers/json-path-2.7.0.jar
COPY json-smart-2.4.7.jar /opt/keycloak/providers/json-smart-2.4.7.jar

# 2. Обновлённый keycloak-admin-ui для 21.1.1.rsp (см. README репозитория):contentReference[oaicite:5]{index=5}
# скачайте jar и положите рядом с Dockerfile
COPY keycloak-admin-ui-21.1.1.rsp.jar /opt/keycloak/lib/lib/main/org.keycloak.keycloak-admin-ui-21.1.1.jar

# 3. Пересобираем Keycloak с новыми провайдерами
RUN /opt/keycloak/bin/kc.sh build
