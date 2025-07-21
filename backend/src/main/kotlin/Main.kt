import com.auth0.jwk.JwkProviderBuilder
import io.ktor.http.*
import io.ktor.serialization.jackson.*
import io.ktor.server.application.*
import io.ktor.server.auth.*
import io.ktor.server.auth.jwt.*
import io.ktor.server.engine.*
import io.ktor.server.netty.*
import io.ktor.server.plugins.callloging.*
import io.ktor.server.plugins.contentnegotiation.*
import io.ktor.server.plugins.cors.routing.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import org.slf4j.event.Level
import java.net.URL
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

val keycloakServerUrl = System.getenv("KEYCLOAK_URL") ?: "http://localhost:8080"
val keycloakRealm = System.getenv("KEYCLOAK_REALM") ?: "reports-realm"
val keycloakClientId = System.getenv("KEYCLOAK_CLIENT_ID") ?: "frontend"
val serverPort = System.getenv("PORT")?.toIntOrNull() ?: 8081

fun main() {

    embeddedServer(Netty, port = serverPort, module = Application::module)
        .start(wait = true)
}

fun Application.module() {
    install(CallLogging) {
        level = Level.DEBUG
    }
    install(ContentNegotiation) {
        jackson()
    }

    install(CORS) {
        anyHost()
        allowMethod(HttpMethod.Options)
        allowMethod(HttpMethod.Get)
        allowMethod(HttpMethod.Post)
        allowMethod(HttpMethod.Put)
        allowMethod(HttpMethod.Delete)
        allowMethod(HttpMethod.Patch)

        allowHeader(HttpHeaders.ContentType)
        allowHeader(HttpHeaders.Authorization)

        allowCredentials = true
        allowNonSimpleContentTypes = true
        maxAgeInSeconds = 24 * 60 * 60
    }


//    configureSecurity()

    install(Authentication) {
        jwt("auth-jwt") {
            realm = keycloakRealm
            verifier(
                JwkProviderBuilder(URL("$keycloakServerUrl/realms/$keycloakRealm/protocol/openid-connect/certs"))
                    .build()
            )
            validate { credential ->
                if (credential.payload.audience?.contains(keycloakClientId)
                        ?: (credential.payload.getClaim("realm_access")?.asMap() as Map<String, List<*>>?)?.get("roles")
                            ?.contains("prothetic_user") ?: false
                ) {
                    JWTPrincipal(credential.payload)
                } else {
                    null
                }
            }
        }
    }

    routing {
        authenticate("auth-jwt") {
            get("/reports") {
                val currentTime = Instant.now()
                val formatter = DateTimeFormatter.ISO_INSTANT
                    .withZone(ZoneId.systemDefault())

                call.respond(
                    mapOf(
                        "current-time" to formatter.format(currentTime),
                        "timezone" to ZoneId.systemDefault().toString()
                    )
                )
            }
        }
    }

}