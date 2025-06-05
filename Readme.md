### Запуск

```sh
docker-compose up -d
```
### Frontend
```sh
http://localhost:3000
```
### Ролевая таблица пользователей
| Пользователь | Пароль | Имеет роли | Имеет доступ к /report
| ------ | ------ |------ |------ |
| user1 | password123 | user |  нет
| user2 | password123 | user | нет
| admin1 | admin123 | administrator | нет
| prothetic1 | prothetic123 | prothetic_user | да
| prothetic2 | prothetic123 | prothetic_user | да
| prothetic3 | prothetic123 | prothetic_user | да
