import React, { useState } from 'react';
import { useKeycloak } from '@react-keycloak/web';

const ReportPage: React.FC = () => {
  const { keycloak, initialized } = useKeycloak();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusCode, setStatusCode] = useState<number | null>(null);
  const [report, setReport] = useState<any>(null);

  const downloadReport = async () => {
    if (!keycloak?.token) {
      setError('Not authenticated');
      setStatusCode(null);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setStatusCode(null);
      setReport(null);

      const response = await fetch(`${process.env.REACT_APP_API_URL}/reports`, {
        headers: {
          'Authorization': `Bearer ${keycloak.token}`
        }
      });

      setStatusCode(response.status);

      if (response.status === 200) {
        const data = await response.json();
        setReport(data);
      } else if (response.status === 403) {
        setError('Forbidden (403): You do not have permission to access this report.');
      } else if (response.status === 401) {
        setError('Unauthorized (401): Your session has expired or you are not authorized.');
      } else {
        setError(`Unexpected error: ${response.status}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setStatusCode(null);
    } finally {
      setLoading(false);
    }
  };

  if (!initialized) {
    return <div>Loading...</div>;
  }

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

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <div className="p-8 bg-white rounded-lg shadow-md">
        <h1 className="text-2xl font-bold mb-6">Usage Reports</h1>
        <button
          onClick={downloadReport}
          disabled={loading}
          className={`px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          {loading ? 'Generating Report...' : 'Download Report'}
        </button>
        {statusCode && (
          <div className="mt-4 p-4 bg-gray-100 text-gray-800 rounded">
            Status code: {statusCode}
          </div>
        )}
        {report && (
          <div className="mt-4 p-4 bg-green-100 text-green-700 rounded">
            <pre>{JSON.stringify(report, null, 2)}</pre>
          </div>
        )}
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