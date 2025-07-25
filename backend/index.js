import express from 'express';
import { Issuer } from 'openid-client';

const issuerUrl = 'http://keycloak:8080/realms/reports-realm/.well-known/openid-configuration'
const clientId = 'reports-api'
const clientSecret = 'oNwoLQdvJAvRcL89SydqCWCe5ry1jMgq'


// Тестовые отчеты
let reports = [
    { id: 1, content: 'Lorem ipsum dolor sit amet' },
    { id: 2, content: 'consectetur adipiscing elit' }
]

const app = express()
app.use(express.json())
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*')
    res.header('Access-Control-Allow-Methods', 'GET, OPTIONS')
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    next()
})

async function validate(token) {
    const issuer = await Issuer.discover(issuerUrl)
    const client = new issuer.Client({
        client_id: clientId,
        client_secret: clientSecret
    })
    try {
        const claims = await client.introspect(token)
        if (claims.active) {
            if (claims.realm_access && claims.realm_access.roles
                && claims.realm_access.roles.includes('prothetic_user')
            ) {
                return claims
            } else {
                return null   
            }
        } else {
            return null
        }
    } catch (error) {
        return null
    }
}

app.get('/reports', async (req, res) => {
    const token = req.headers.authorization?.split(' ')[1]
    if (!token) {
        return res.status(401).json({ message: 'Не авторизован' })
    }
    const claims = await validate(token)
    if (claims) {
        return res.json(reports)
    } else {
        return res.status(401).json({ message: 'Не авторизован' })
    }
});

app.listen(8000, () => {
    console.log('Сервер запущен на порту 8000')
});