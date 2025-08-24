// frontend/src/components/ReportPage.tsx

import React, { useState } from 'react';
import { useKeycloak } from '@react-keycloak/web';

// Определяем структуру отчета для TypeScript
interface ReportData {
  reportId: string;
  userId: string;
  prosthesisModel: string;
  usageData: Array<{
    date: string;
    movements: number;
    battery_cycles: number;
  }>;
}

const ReportPage: React.FC = () => {
  const { keycloak, initialized } = useKeycloak();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Добавляем состояние для хранения данных отчета
  const [reportData, setReportData] = useState<ReportData | null>(null);

  const downloadReport = async () => {
    // Убеждаемся, что у нас есть токен
    if (!keycloak?.token) {
      setError('Not authenticated');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setReportData(null); // Очищаем предыдущий отчет

      // Отправляем запрос на наш Python API
      const response = await fetch(`${process.env.REACT_APP_API_URL}/reports`, {
        method: 'GET',
        headers: {
          // Это самый важный момент: добавляем токен для авторизации
          'Authorization': `Bearer ${keycloak.token}`
        }
      });

      // Если ответ не успешный (например, 401 или 403), показываем ошибку
      if (!response.ok) {
        throw new Error(`Failed to fetch report: ${response.status} ${response.statusText}`);
      }

      // Получаем JSON с данными отчета и сохраняем его в состояние
      const data: ReportData = await response.json();
      setReportData(data);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Пока Keycloak инициализируется, показываем загрузку
  if (!initialized) {
    return <div>Loading...</div>;
  }

  // Если пользователь не аутентифицирован, показываем кнопку входа
  if (!keycloak.authenticated) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
        <button
          onClick={() => keycloak.login()}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Login
        </button>
      </div>
    );
  }

  // Если пользователь вошел, показываем страницу с отчетом
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <div className="p-8 bg-white rounded-lg shadow-md w-full max-w-2xl">
        <h1 className="text-2xl font-bold mb-6">Usage Reports</h1>
        
        <button
          onClick={downloadReport}
          disabled={loading}
          className={`w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 ${
            loading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          {loading ? 'Generating Report...' : 'Download Report'}
        </button>

        {error && (
          <div className="mt-4 p-4 bg-red-100 text-red-700 rounded">
            {error}
          </div>
        )}

        {/* Новый блок: если данные отчета получены, красиво выводим их в формате JSON */}
        {reportData && (
          <div className="mt-6 p-4 bg-gray-50 rounded border border-gray-200">
            <h2 className="text-lg font-semibold mb-2">Report Data:</h2>
            <pre className="text-sm bg-gray-900 text-white p-4 rounded overflow-x-auto">
              {JSON.stringify(reportData, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportPage;