using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Api.Controllers;

[Authorize(Policy = "RequireProtheticUser")]
[ApiController]
[Route("reports")]
public class ReportsController : ControllerBase
{
    [HttpGet]
    public IActionResult GetReports()
    {
        var reports = new[]
        {
            new {
                reportId = "1",
                userId = "u123",
                protheticId = "p456",
                date = DateTime.UtcNow,
                activitySummary = "Пользователь выполнил 154 движений кистью",
                issuesDetected = new[] { "повышенное энергопотребление", "редкие сигналы от датчиков" },
                batteryUsage = 72
            },
            new {
                reportId = "2",
                userId = "u789",
                protheticId = "p321",
                date = DateTime.UtcNow.AddDays(-1),
                activitySummary = "Зарегистрированы 45 циклов хвата за день",
                issuesDetected = new string[] { },
                batteryUsage = 48
            }
        };

        return Ok(reports);
    }
}