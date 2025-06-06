using System.Security.Claims;
using System.Text.Json;
using Microsoft.AspNetCore.Authentication;

namespace reportsapi;

public class RealmRoleClaimsTransformation : IClaimsTransformation
{
    public Task<ClaimsPrincipal> TransformAsync(ClaimsPrincipal principal)
    {
        var identity = principal.Identity as ClaimsIdentity;
        var realmJson = identity?.FindFirst("realm_access")?.Value;

        if (realmJson is not null)
        {
            using var doc = JsonDocument.Parse(realmJson);
            if (doc.RootElement.TryGetProperty("roles", out var rolesElement))
            {
                foreach (var role in rolesElement.EnumerateArray())
                    identity!.AddClaim(new Claim(ClaimTypes.Role, role.GetString()!));
            }
        }
        return Task.FromResult(principal);
    }
}