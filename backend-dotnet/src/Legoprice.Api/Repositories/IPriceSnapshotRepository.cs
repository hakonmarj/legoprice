using Legoprice.Api.Dtos;
using Legoprice.Api.Entities;

namespace Legoprice.Api.Repositories;

public interface IPriceSnapshotRepository
{
    Task AddAsync(PriceSnapshot snapshot, CancellationToken cancellationToken = default);
    Task<bool> ExistsTodayAsync(string setNumber, DateTime utcNow, CancellationToken cancellationToken = default);
    Task<List<PriceHistoryEntryDto>> GetHistoryAsync(string setNumber, int days, CancellationToken cancellationToken = default);
    Task<List<ProductSummaryDto>> GetLatestProductsWithSixMonthLowAsync(CancellationToken cancellationToken = default);
    Task SaveChangesAsync(CancellationToken cancellationToken = default);
}
