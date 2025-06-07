import Keycloak from 'keycloak-js';

// одна-единственная инстанция Keycloak
export const keycloak = new Keycloak({
  url: process.env.REACT_APP_KEYCLOAK_URL,
  realm: process.env.REACT_APP_KEYCLOAK_REALM||"",
  clientId: process.env.REACT_APP_KEYCLOAK_CLIENT_ID||""             
});

export const initOptions = {
  onLoad: 'check-sso',          // silent-SSO при первом старте
  flow:   'standard',           // Authorization Code + PKCE
  pkceMethod: 'S256',           // можно опустить — уже default
  silentCheckSsoRedirectUri:
      `${window.location.origin}/silent-check-sso.html`,
  checkLoginIframe: true,       // фоновое продление сессии
  checkLoginIframeInterval: 30,
  enableLogging: true
};
