package com.bionicpro.api.security

import org.springframework.core.convert.converter.Converter
import org.springframework.security.core.GrantedAuthority
import org.springframework.security.core.authority.SimpleGrantedAuthority
import org.springframework.security.oauth2.jwt.Jwt

class KeycloakRealmRoleConverter : Converter<Jwt, Collection<GrantedAuthority>> {

    override fun convert(jwt: Jwt): Collection<GrantedAuthority> {
        val realmAccess = jwt.claims["realm_access"] as? Map<*, *> ?: emptyMap<String, Any>()
        val roles = realmAccess["roles"] as? Collection<*> ?: emptyList<Any>()
        return roles.mapNotNull { it?.toString()?.let { r -> SimpleGrantedAuthority("ROLE_$r") } }
    }
}