import React, { useState, useEffect } from 'react';
import { useKeycloak } from '@react-keycloak/web';

const ReportPage: React.FC = () => {
  const { keycloak, initialized } = useKeycloak();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialized && keycloak) {
      console.log('Keycloak initialized, authenticated:', keycloak.authenticated);
      console.log('Token:', keycloak.token);
    }
  }, [initialized, keycloak]);

  const handleLogin = () => {
    keycloak?.login({
      redirectUri: window.location.origin
    });
  };

  const downloadReport = async () => {
    if (!keycloak?.token) {
      setError('Not authenticated');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${process.env.REACT_APP_API_URL}/reports`, {
        headers: {
          'Authorization': `Bearer ${keycloak.token}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Получаем данные как blob
      const blob = await response.blob();
      
      // Создаем URL для blob
      const url = window.URL.createObjectURL(blob);
      
      // Создаем временную ссылку для скачивания
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      
      // Получаем имя файла из заголовка Content-Disposition или используем default
      const contentDisposition = response.headers.get('Content-Disposition');
      let fileName = 'report.txt';
      
      if (contentDisposition) {
        const fileNameMatch = contentDisposition.match(/filename="?(.+)"?/);
        if (fileNameMatch && fileNameMatch[1]) {
          fileName = fileNameMatch[1];
        }
      }
      
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      
      // Очищаем
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      console.log('File downloaded successfully');

    } catch (err) {
      console.error('Download error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (!initialized) {
    return <div>Loading Keycloak...</div>;
  }

  if (!keycloak.authenticated) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
        <div className="p-4 mb-4 bg-yellow-100 text-yellow-700 rounded">
          Not authenticated. Token in URL: {window.location.hash ? 'Yes' : 'No'}
        </div>
        <button
          onClick={handleLogin}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Login
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <div className="p-8 bg-white rounded-lg shadow-md">
        <h1 className="text-2xl font-bold mb-6">Usage Reports</h1>
        
        <div className="mb-4 p-2 bg-green-100 text-green-700 rounded">
          Successfully authenticated! User: {keycloak.tokenParsed?.preferred_username}
        </div>
        
        <button
          onClick={downloadReport}
          disabled={loading}
          className={`px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 ${
            loading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          {loading ? 'Generating Report...' : 'Download Report'}
        </button>

        <button
          onClick={() => keycloak.logout()}
          className="ml-4 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
        >
          Logout
        </button>

        {error && (
          <div className="mt-4 p-4 bg-red-100 text-red-700 rounded">
            {error}
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportPage;