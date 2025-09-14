-- Инициализация базы данных для отчётов
-- База данных уже создана через переменные окружения
-- Создаем пользователя если не существует
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'reports_user') THEN

      CREATE ROLE reports_user LOGIN PASSWORD 'reports_password';
   END IF;
END
$do$;

-- Предоставляем права на базу данных
GRANT ALL PRIVILEGES ON DATABASE reports_db TO reports_user;
