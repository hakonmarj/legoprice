using Legoprice.Api.Services;
using Microsoft.AspNetCore.Mvc;

namespace Legoprice.Api.Controllers;

[ApiController]
[Route("api/pipeline")]
public class PipelineController : ControllerBase
{
    private readonly IEnvironmentVariableAuthService _authService;
    private readonly IPipelineTriggerService _pipelineTriggerService;

    public PipelineController(IEnvironmentVariableAuthService authService, IPipelineTriggerService pipelineTriggerService)
    {
        _authService = authService;
        _pipelineTriggerService = pipelineTriggerService;
    }

    [HttpPost("trigger")]
    public async Task<IActionResult> Trigger([FromHeader(Name = "X-Trigger-Token")] string? token, CancellationToken cancellationToken)
    {
        if (!_authService.IsValidTriggerToken(token))
        {
            return Unauthorized(new { message = "Invalid trigger token" });
        }

        try
        {
            var processId = await _pipelineTriggerService.TriggerAsync(cancellationToken);
            return Accepted(new
            {
                status = "triggered",
                processId,
                timestampUtc = DateTime.UtcNow
            });
        }
        catch (InvalidOperationException ex)
        {
            return StatusCode(StatusCodes.Status503ServiceUnavailable, new { message = ex.Message });
        }
    }
}
