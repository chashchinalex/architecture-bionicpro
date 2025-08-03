using System.Security.Claims;
using System.Text.Json;
using Microsoft.AspNetCore.Authentication;

namespace ReportAPI;

public class RoleClaimsTransformation : IClaimsTransformation
{
    public Task<ClaimsPrincipal> TransformAsync(ClaimsPrincipal principal)
    {
        var identity = principal.Identity as ClaimsIdentity;
        if (identity == null)
        {
            return Task.FromResult(principal);
        }
        
        var realmAccessClaim = identity.FindFirst("realm_access");
        if (realmAccessClaim != null)
        {
            var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
            var realmAccess = JsonSerializer.Deserialize<RealmAccess>(realmAccessClaim.Value, options);
            if (realmAccess?.Roles != null)
            {
                foreach (var role in realmAccess.Roles)
                {
                    identity.AddClaim(new Claim(ClaimTypes.Role, role));
                }
            }
        }

        return Task.FromResult(principal);
    }
    public class RealmAccess { public List<string>? Roles { get; set; } } // one user can be assigned multiple roles
}