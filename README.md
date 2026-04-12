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
3. Войдите: `admin` / `admin`.
4. Найдите DAG `reports_etl`.
5. Нажмите `Trigger DAG`.
6. Откройте UI: http://localhost:3000
7. Нажмите `Login with Keycloak`.
8. Войдите под одним из пользователей из таблицы выше.
9. Настройте OTP.
10. Выберите период.
11. Нажмите `Получить отчёт`.


## Задание 3. Снижение нагрузки на базу данных

Инструкция:
1. Запустите:
```bash
docker compose up
```
2. Откройте Airflow: http://localhost:8081
3. Нажмите `Trigger DAG`.
4. Откройте UI: http://localhost:3000
5. Нажмите `Получить отчёт`, должна появиться ссылка `Открыть JSON через CDN`.


## Задание 4. Повышение оперативности и стабильности CRM

Инструкция:
1. Запустите:
```bash
docker compose up
```
3. Откройте Debezium: http://localhost:8083/connectors
4. Должен существовать connector `crm-connector`.
5. Откройте UI: http://localhost:3000
6. Нажмите `Получить отчёт`.
