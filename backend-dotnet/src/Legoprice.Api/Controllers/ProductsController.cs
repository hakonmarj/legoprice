using Legoprice.Api.Services;
using Microsoft.AspNetCore.Mvc;

namespace Legoprice.Api.Controllers;

[ApiController]
[Route("api/products")]
public class ProductsController : ControllerBase
{
    private readonly IProductService _productService;

    public ProductsController(IProductService productService)
    {
        _productService = productService;
    }

    [HttpGet]
    public async Task<IActionResult> GetProducts(CancellationToken cancellationToken)
    {
        var result = await _productService.GetProductsAsync(cancellationToken);
        return Ok(result);
    }

    [HttpGet("{setNumber}/history")]
    public async Task<IActionResult> GetHistory(string setNumber, [FromQuery] int days = 30, CancellationToken cancellationToken = default)
    {
        if (days < 1 || days > 365)
        {
            return BadRequest("days must be between 1 and 365");
        }

        var result = await _productService.GetHistoryAsync(setNumber, days, cancellationToken);
        return Ok(result);
    }
}
