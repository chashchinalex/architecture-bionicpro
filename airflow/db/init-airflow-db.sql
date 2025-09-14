-- Инициализация базы данных для Airflow
-- База данных уже создана через переменные окружения
-- Создаем пользователя если не существует
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'airflow') THEN

      CREATE ROLE airflow LOGIN PASSWORD 'airflow';
   END IF;
END
$do$;

-- Предоставляем права на базу данных
GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;
