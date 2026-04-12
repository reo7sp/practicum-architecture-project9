# practicum-architecture-project9

## Задание 1. Повышение безопасности системы

Диаграмма:
![](docs/BionicPRO_C4_model.drawio.svg)

Инструкция:
1. Запустите:
```bash
docker compose up
```
2. Откройте: http://localhost:3000
3. Нажмите `Login with Keycloak`.
4. Войдите под одним из пользователей:

| Логин | Пароль | Комментарий |
|---|---|---|
| `user1` | `password123` | Обычный пользователь |
| `admin1` | `admin123` | Администратор |
| `prothetic1` | `prothetic123` | Пользователь сервиса протезов |

5. Настройте OTP.
6. Нажмите `Получить отчёт`.
7. Экспорт keycloak realm:
```bash
docker exec practicum-architecture-project9-keycloak-1 /opt/keycloak/bin/kc.sh export --dir /tmp/export --realm reports-realm --users realm_file
docker cp practicum-architecture-project9-keycloak-1:/tmp/export/reports-realm-realm.json keycloak/keycloak-results-export.json
```

## Задание 2. Разработка сервиса отчётов

Диаграмма:
![](docs/BionicPRO_C4_model_task2.drawio.svg)

Инструкция:
1. Запустите:
```bash
docker compose up
```
2. Откройте Airflow: http://localhost:8081
3. Войдите: admin / admin.
4. Найдите DAG `reports_etl`.
5. Нажмите toggle для включения DAG.
6. Нажмите `Trigger DAG`.
7. Откройте UI: http://localhost:3000
8. Нажмите `Login with Keycloak`.
9. Войдите под одним из пользователей из таблицы выше.
10. Настройте OTP.
11. Выберите период.
12. Нажмите `Получить отчёт`.
