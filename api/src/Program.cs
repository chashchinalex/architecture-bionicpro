using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;
using System.Text.Json;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowFrontend", policy =>
    {
        policy.WithOrigins("http://localhost:3000", "http://localhost:8000")
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials();
    });
});

builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.Authority = "http://keycloak:8080/realms/reports-realm";
        options.Audience = "reports-api";
        options.RequireHttpsMetadata = false;

        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidIssuers = new[] 
            {
                "http://keycloak:8080/realms/reports-realm",
                "http://localhost:8080/realms/reports-realm"
            },
            ValidateIssuer = true,
            ValidateAudience = false,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            NameClaimType = "preferred_username"
        };
    });

builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("RequireProtheticUserRole", policy =>
        policy.RequireAssertion(context =>
        {
            if (context.User.HasClaim("roles", "prothetic_user"))
                return true;

            var realmAccessClaim = context.User.FindFirst("realm_access");
            if (realmAccessClaim != null)
            {
                try
                {
                    var realmAccess = JsonSerializer.Deserialize<JsonElement>(realmAccessClaim.Value);
                    if (realmAccess.TryGetProperty("roles", out var rolesElement))
                    {
                        foreach (var role in rolesElement.EnumerateArray())
                        {
                            if (role.GetString() == "prothetic_user")
                                return true;
                        }
                    }
                }
                catch
                {
                    // Если не удалось распарсить JSON, игнорируем
                }
            }

            return false;
        }));
});

var app = builder.Build();

app.UseCors("AllowFrontend");
app.UseAuthentication();
app.UseAuthorization();

app.MapGet("/anonymous-reports", () => "Привет, это публичный отчёт")
   .AllowAnonymous();

app.MapGet("/reports", (HttpContext context) => 
{
    var fileName = $"report_{DateTime.Now:yyyyMMdd_HHmmss}.txt";
    var content = "Привет, это отчёт";
    var bytes = System.Text.Encoding.UTF8.GetBytes(content);
    
    // Устанавливаем заголовки для принудительной загрузки
    context.Response.Headers.Append("Content-Disposition", $"attachment; filename=\"{fileName}\"");
    context.Response.Headers.Append("Content-Type", "text/plain; charset=utf-8");
    context.Response.Headers.Append("Content-Length", bytes.Length.ToString());
    
    return Results.File(bytes, "text/plain", fileName);
}).RequireAuthorization("RequireProtheticUserRole");

app.Run();