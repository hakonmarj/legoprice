using Legoprice.Api.Dtos;

namespace Legoprice.Api.Services;

public interface IProductService
{
    Task<List<ProductSummaryDto>> GetProductsAsync(CancellationToken cancellationToken = default);
    Task<List<PriceHistoryEntryDto>> GetHistoryAsync(string setNumber, int days = 30, CancellationToken cancellationToken = default);
}
