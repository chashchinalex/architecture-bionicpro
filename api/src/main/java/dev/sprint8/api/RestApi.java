package dev.sprint8.api;

import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class RestApi {

    @GetMapping("reports")
    public String genrateReport(
            @AuthenticationPrincipal Jwt jwt
    ) {
        return "Got report for " + jwt.getClaims().get("email");
    }
}
