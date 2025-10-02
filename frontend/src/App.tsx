import React from 'react';
import { ReactKeycloakProvider } from '@react-keycloak/web';
import Keycloak, { KeycloakConfig } from 'keycloak-js';
import ReportPage from './components/ReportPage';

const keycloakConfig: KeycloakConfig = {
  url: process.env.REACT_APP_KEYCLOAK_URL,
  realm: process.env.REACT_APP_KEYCLOAK_REALM||"",
  clientId: process.env.REACT_APP_KEYCLOAK_CLIENT_ID||""
};

const keycloak = new Keycloak(keycloakConfig);

const eventLogger = (event: unknown, error: unknown) => {
  console.log('Keycloak event:', event, error);
};

const tokenLogger = (tokens: unknown) => {
  console.log('Keycloak tokens:', tokens);
};

const App: React.FC = () => {
  return (
    <ReactKeycloakProvider
      authClient={keycloak}
      initOptions={{
        pkceMethod: 'S256',
        checkLoginIframe: false,
        onLoad: 'login-required',
        redirectUri: window.location.origin,
        useNonce: true
      }}
      autoRefreshToken={true}
      onTokens={(tokens) => {
        console.log('Tokens received:', tokens);
      }}
      onEvent={(event, error) => {
        console.log('Keycloak event:', event, error);
        if (event === 'onAuthSuccess') {
          console.log('Authentication successful!');
        }
      }}
    >
      <div className="App">
        <ReportPage />
      </div>
    </ReactKeycloakProvider>
  );
};

export default App;