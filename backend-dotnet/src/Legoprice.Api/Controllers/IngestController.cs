using Legoprice.Api.Dtos;
using Legoprice.Api.Services;
using Microsoft.AspNetCore.Mvc;

namespace Legoprice.Api.Controllers;

[ApiController]
[Route("api/ingest")]
public class IngestController : ControllerBase
{
    private readonly IIngestService _ingestService;

    public IngestController(IIngestService ingestService)
    {
        _ingestService = ingestService;
    }

    [HttpPost("products")]
    public async Task<IActionResult> IngestProducts([FromBody] IngestProductsRequestDto request, CancellationToken cancellationToken)
    {
        if (request.Products.Count == 0)
        {
            return BadRequest("Products payload is empty");
        }

        var (inserted, skipped) = await _ingestService.IngestAsync(request.Products, cancellationToken);
        return Ok(new { inserted, skipped });
    }
}
