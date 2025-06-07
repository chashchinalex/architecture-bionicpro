const express = require('express')
const Keycloak = require('keycloak-connect');
const session = require('express-session');
const cors = require('cors')

const memoryStore = new session.MemoryStore();
const keycloak = new Keycloak({ store: memoryStore }, {
  "auth-server-url": 'http://127.0.0.1:8080',
  realm: 'reports-realm',
  "clientId": "reports-api",
  "enabled": true,
  "clientAuthenticatorType": "client-secret",
  "secret": "oNwoLQdvJAvRcL89SydqCWCe5ry1jMgq",
  "bearerOnly": true
});

const app = express()
const port = 3000

app.use(cors())

app.use(session({
  secret:'TestSecret',
  resave: false,
  saveUninitialized: true,
  store: memoryStore
}));

app.use( keycloak.middleware( { logout: '/'} ));

app.get('/', (req, res) => {
  res.send('Hello World!')
})

//route protected with Keycloak
app.get(
  '/reports',
  keycloak.protect(
  (token, request) =>  {
    return token.hasRole( "realm:prothetic_user")
  }),
  function(req, res){
    res.json({
      data: {
        reports: [
          {
            id: 1,
            reportData: {
              name: 'TestReport'
            }
          },
          {
            id: 2,
            reportData: {
              name: 'TestReport'
            }
          }
        ]
      }
    });
  }
);

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`)
})
