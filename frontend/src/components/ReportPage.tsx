import React from 'react';
import './ReportPage.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface User {
  email: string;
  name?: string;
}

interface ReportRow {
  id: number;
  user_id: number;
  user_name: string;
  email: string;
  prosthesis_type: string;
  muscle_group: string;
  avg_signal_frequency: number;
  avg_signal_duration: number;
  avg_signal_amplitude: number;
  last_signal_time: string;
}

const formatFloat = (value: number, digits = 2) =>
  Number.isFinite(value) ? value.toFixed(digits) : '';

const formatDateTime = (value: string) => {
  if (!value) return '';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString();
};

const ReportPage: React.FC = () => {
  const [user, setUser] = React.useState<User | null>(null);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [reportStatus, setReportStatus] = React.useState<string | null>(null);
  const [reportUrl, setReportUrl] = React.useState<string | null>(null);
  const [reportRows, setReportRows] = React.useState<ReportRow[]>([]);
  const [error, setError] = React.useState<string | null>(null);

  // Получение текущего пользователя
  React.useEffect(() => {
    const fetchUser = async () => {
      try {
        setLoading(true);
        setError(null);

        const res = await fetch(`${API_URL}/auth/me`, {
          method: 'GET',
          credentials: 'include',
        });

        if (res.status === 401) {
          setUser(null);
          return;
        }

        if (!res.ok) {
          throw new Error(`Ошибка запроса /auth/me: ${res.status}`);
        }

        const data = await res.json();
        setUser(data);
      } catch (e) {
        console.error(e);
        setError('Не удалось получить информацию о пользователе');
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, []);

  // Запрос отчёта
  const handleGetReport = async () => {
    try {
      setReportStatus('Запрашиваем отчёт…');
      setError(null);

      const res = await fetch(`${API_URL}/reports`, {
        method: 'GET',
        credentials: 'include',
      });

      if (!res.ok) {
        setReportStatus('Не удалось запросить отчёт');
        setReportRows([]);
        return;
      }

      const data = await res.json();

      // backend возвращает:
      // { cdn_url: string, source: "cache" | "generated", reports: [...] }

      setReportStatus(
        data.source === 'cache'
          ? 'Отчёт получен из кэша CDN'
          : 'Отчёт сгенерирован и сохранён в S3',
      );
      setReportUrl(data.cdn_url || null);
      setReportRows((data.reports || []) as ReportRow[]);
    } catch (e) {
      console.error(e);
      setReportStatus('Ошибка при получении отчёта');
      setReportRows([]);
      setError('Произошла ошибка при запросе отчёта');
    }
  };

  if (loading) {
    return (
      <div className="report-page">
        <div className="report-card">
          <div className="report-title">Отчёты по сигналам</div>
          <div className="report-loading">Загрузка…</div>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="report-page">
        <div className="report-card">
          <div className="report-title">Отчёты по сигналам</div>
          <div className="report-error">
            Вы не авторизованы. Пожалуйста, выполните вход.
          </div>
          <a className="report-link-button" href={`${API_URL}/auth/login`}>
            Войти
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="report-page">
      <div className="report-card">
        <div className="report-header">
          <div>
            <div className="report-title">Отчёты по сигналам</div>
            <div className="report-subtitle">
              Пользователь: {user.name || user.email}
            </div>
          </div>
          <button className="report-button" onClick={handleGetReport}>
            Получить отчёт
          </button>
        </div>

        {error && <div className="report-error">{error}</div>}

        {reportStatus && (
          <div className="report-status">
            <div className="report-label">Статус</div>
            <div className="report-status-text">{reportStatus}</div>
            {reportUrl && (
              <a
                href={reportUrl}
                className="report-link"
                target="_blank"
                rel="noopener noreferrer"
              >
                Открыть отчёт (CDN)
              </a>
            )}
          </div>
        )}

        {reportRows.length > 0 && (
          <div className="report-table-wrapper">
            <div className="report-table-header">
              <div className="report-label">Данные отчёта</div>
              <div className="report-meta">
                Записей: <span>{reportRows.length}</span>
              </div>
            </div>

            <div className="report-table-scroll">
              <table className="report-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Пользователь</th>
                    <th>Email</th>
                    <th>Тип протеза</th>
                    <th>Группа мышц</th>
                    <th className="col-number">Частота, Гц</th>
                    <th className="col-number">Длительность, мс</th>
                    <th className="col-number">Амплитуда</th>
                    <th>Последний сигнал</th>
                  </tr>
                </thead>
                <tbody>
                  {reportRows.map((row) => (
                    <tr key={row.id}>
                      <td>{row.id}</td>
                      <td>{row.user_name}</td>
                      <td className="cell-email" title={row.email}>
                        {row.email}
                      </td>
                      <td>
                        <span className={`badge badge-${row.prosthesis_type}`}>
                          {row.prosthesis_type}
                        </span>
                      </td>
                      <td>{row.muscle_group}</td>
                      <td className="col-number">
                        {row.avg_signal_frequency}
                      </td>
                      <td className="col-number">
                        {row.avg_signal_duration}
                      </td>
                      <td className="col-number">
                        {formatFloat(row.avg_signal_amplitude, 3)}
                      </td>
                      <td>{formatDateTime(row.last_signal_time)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {reportStatus && reportRows.length === 0 && !error && (
          <div className="report-empty">
            Для текущего отчёта нет табличных данных.
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportPage;
