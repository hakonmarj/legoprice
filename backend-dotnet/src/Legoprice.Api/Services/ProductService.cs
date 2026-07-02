using Legoprice.Api.Dtos;
using Legoprice.Api.Repositories;

namespace Legoprice.Api.Services;

public class ProductService : IProductService
{
    private readonly IPriceSnapshotRepository _priceSnapshotRepository;

    public ProductService(IPriceSnapshotRepository priceSnapshotRepository)
    {
        _priceSnapshotRepository = priceSnapshotRepository;
    }

    public Task<List<ProductSummaryDto>> GetProductsAsync(CancellationToken cancellationToken = default)
    {
        return _priceSnapshotRepository.GetLatestProductsWithSixMonthLowAsync(cancellationToken);
    }

    public Task<List<PriceHistoryEntryDto>> GetHistoryAsync(string setNumber, int days = 30, CancellationToken cancellationToken = default)
    {
        return _priceSnapshotRepository.GetHistoryAsync(setNumber, days, cancellationToken);
    }
}
