using System.Security.Claims;
using System.Text.Json;
using Microsoft.AspNetCore.Authentication.JwtBearer;

var builder = WebApplication.CreateBuilder(args);

var authority = Environment.GetEnvironmentVariable("KEYCLOAK_AUTHORITY");

builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowFrontend",
        policy =>
        {
            policy.WithOrigins("http://localhost:3000")
                .AllowAnyHeader()
                .AllowAnyMethod()
                .AllowCredentials();
        });
});

builder.Services.AddAuthentication("Bearer")
    .AddJwtBearer("Bearer", options =>
    {
        options.RequireHttpsMetadata = false;
        options.Authority = authority; // URL Keycloak
        options.TokenValidationParameters = new Microsoft.IdentityModel.Tokens.TokenValidationParameters
        {
            ValidateAudience = false,
            ValidateIssuer = true,
            ValidIssuer = "http://localhost:8080/realms/reports-realm"
        };
        options.Events = new JwtBearerEvents
        {
            OnTokenValidated = context =>
            {
                var claimsIdentity = context.Principal!.Identity as ClaimsIdentity;
                var realmAccess = context.Principal.FindFirst("realm_access");

                if (realmAccess != null && realmAccess.Value is string json)
                {
                    try
                    {
                        using var doc = JsonDocument.Parse(json);
                        if (doc.RootElement.TryGetProperty("roles", out var rolesElement))
                        {
                            foreach (var role in rolesElement.EnumerateArray())
                            {
                                claimsIdentity!.AddClaim(new Claim("roles", role.GetString()!));
                                Console.WriteLine($"🚀 OnTokenValidated STARTED {role.GetString()}");
                            }
                        }
                    }
                    catch
                    {
                        // ignore parse errors
                    }
                }

                return Task.CompletedTask;
            }
        };
    });

builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("RequireProtheticUser", policy =>
    {
        policy.AuthenticationSchemes.Add("Bearer");
        policy.RequireClaim("roles", "prothetic_user");
    });
});

builder.Services.AddControllers();

var app = builder.Build();

app.UseCors("AllowFrontend");

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

app.Run();