using Legoprice.Api.Data;
using Legoprice.Api.Dtos;
using Legoprice.Api.Entities;
using Microsoft.EntityFrameworkCore;

namespace Legoprice.Api.Repositories;

public class PriceSnapshotRepository : IPriceSnapshotRepository
{
    private readonly AppDbContext _dbContext;

    public PriceSnapshotRepository(AppDbContext dbContext)
    {
        _dbContext = dbContext;
    }

    public Task AddAsync(PriceSnapshot snapshot, CancellationToken cancellationToken = default)
    {
        return _dbContext.PriceSnapshots.AddAsync(snapshot, cancellationToken).AsTask();
    }

    public Task<bool> ExistsTodayAsync(string setNumber, DateTime utcNow, CancellationToken cancellationToken = default)
    {
        var todayStart = utcNow.Date;
        return _dbContext.PriceSnapshots
            .AnyAsync(s => s.LegoSetNumber == setNumber && s.CapturedAt >= todayStart, cancellationToken);
    }

    public async Task<List<PriceHistoryEntryDto>> GetHistoryAsync(string setNumber, int days, CancellationToken cancellationToken = default)
    {
        var cutoff = DateTime.UtcNow.AddDays(-days);

        return await _dbContext.PriceSnapshots
            .Where(s => s.LegoSetNumber == setNumber && s.CapturedAt >= cutoff)
            .OrderBy(s => s.CapturedAt)
            .Select(s => new PriceHistoryEntryDto
            {
                CapturedAt = s.CapturedAt,
                LowestPriceIsk = s.LowestPriceIsk,
                LowestPriceStore = s.LowestPriceStore,
                CoolshopPriceIsk = s.CoolshopPriceIsk,
                KubbabudinPriceIsk = s.KubbabudinPriceIsk,
                BooztPriceIsk = s.BooztPriceIsk,
                HagkaupPriceIsk = s.HagkaupPriceIsk,
                KidsworldPriceIsk = s.KidsworldPriceIsk,
                ElkoPriceIsk = s.ElkoPriceIsk,
            })
            .ToListAsync(cancellationToken);
    }

    public async Task<List<ProductSummaryDto>> GetLatestProductsWithSixMonthLowAsync(CancellationToken cancellationToken = default)
    {
        var sixMonthsAgo = DateTime.UtcNow.AddDays(-180);

        var latestPerSet = await _dbContext.PriceSnapshots
            .GroupBy(s => s.LegoSetNumber)
            .Select(g => g.OrderByDescending(x => x.CapturedAt).First())
            .ToListAsync(cancellationToken);

        var sixMonthLowPerSet = await _dbContext.PriceSnapshots
            .Where(s => s.CapturedAt >= sixMonthsAgo && s.LowestPriceIsk != null)
            .GroupBy(s => s.LegoSetNumber)
            .Select(g => g.OrderBy(x => x.LowestPriceIsk).First())
            .ToListAsync(cancellationToken);

        var lowBySet = sixMonthLowPerSet.ToDictionary(x => x.LegoSetNumber, x => x);

        var setNumbers = latestPerSet.Select(x => x.LegoSetNumber).ToList();
        var products = await _dbContext.Products
            .Where(p => setNumbers.Contains(p.LegoSetNumber))
            .ToDictionaryAsync(p => p.LegoSetNumber, p => p, cancellationToken);

        var result = new List<ProductSummaryDto>(latestPerSet.Count);

        foreach (var latest in latestPerSet)
        {
            if (!products.TryGetValue(latest.LegoSetNumber, out var product))
            {
                continue;
            }

            lowBySet.TryGetValue(latest.LegoSetNumber, out var lowRow);

            double? diffPct = null;
            if (latest.LowestPriceIsk.HasValue && lowRow?.LowestPriceIsk is int low && low > 0)
            {
                diffPct = ((latest.LowestPriceIsk.Value - low) / (double)low) * 100.0;
            }

            result.Add(new ProductSummaryDto
            {
                LegoSetNumber = product.LegoSetNumber,
                Name = product.Name,
                Theme = product.Theme,
                NumParts = product.NumParts,
                DisplayImageUrl = product.DisplayImageUrl,
                BricklinkImageUrl = product.BricklinkImageUrl,
                BricklinkThumbnailUrl = product.BricklinkThumbnailUrl,
                BricklinkName = product.BricklinkName,

                LowestPriceIsk = latest.LowestPriceIsk,
                LowestPriceStore = latest.LowestPriceStore,
                CoolshopPriceIsk = latest.CoolshopPriceIsk,
                KubbabudinPriceIsk = latest.KubbabudinPriceIsk,
                BooztPriceIsk = latest.BooztPriceIsk,
                HagkaupPriceIsk = latest.HagkaupPriceIsk,
                KidsworldPriceIsk = latest.KidsworldPriceIsk,
                ElkoPriceIsk = latest.ElkoPriceIsk,

                CoolshopUrl = product.CoolshopUrl,
                KubbabudinUrl = product.KubbabudinUrl,
                BooztUrl = product.BooztUrl,
                HagkaupUrl = product.HagkaupUrl,
                KidsworldUrl = product.KidsworldUrl,
                ElkoUrl = product.ElkoUrl,

                PiecesPerKr = latest.PiecesPerKr,
                Bricklink6mAvgPriceNewUsd = latest.Bricklink6mAvgPriceNewUsd,
                Bricklink6mAvgPriceNewIsk = latest.Bricklink6mAvgPriceNewIsk,
                LowestPriceVsBricklinkAvgRatio = latest.LowestPriceVsBricklinkAvgRatio,
                Bricklink6mSalesCountNew = latest.Bricklink6mSalesCountNew,

                SixMonthLowIsk = lowRow?.LowestPriceIsk,
                SixMonthLowStore = lowRow?.LowestPriceStore,
                PriceDiffFromSixMonthLowPct = diffPct,
            });
        }

        return result;
    }

    public Task SaveChangesAsync(CancellationToken cancellationToken = default)
    {
        return _dbContext.SaveChangesAsync(cancellationToken);
    }
}
