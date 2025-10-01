# Комментарии к работе

Заменить Code Grant на PKCE можно несколькими способами:

- Изменить конфигурацию `realm-export.json`. В работе использован этот способ
- В интерфейсе Keycloak в Admin Console выбрать realm `reports-realm`. В разделе _Clients_ выбрать пользователя `reports-frontend`. На вкладке _Settings_ убрать галочку _Direct access grants_, на вкладке _Advanced_ найти пункт _Proof Key for Code Exchange Code Challenge Method_, изменить значение на _S256_ и сохранить.

