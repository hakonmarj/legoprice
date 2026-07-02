using Legoprice.Api.Dtos;
using Legoprice.Api.Entities;
using Legoprice.Api.Repositories;

namespace Legoprice.Api.Services;

public class IngestService : IIngestService
{
    private readonly IProductRepository _productRepository;
    private readonly IPriceSnapshotRepository _priceSnapshotRepository;

    public IngestService(IProductRepository productRepository, IPriceSnapshotRepository priceSnapshotRepository)
    {
        _productRepository = productRepository;
        _priceSnapshotRepository = priceSnapshotRepository;
    }

    public async Task<(int inserted, int skipped)> IngestAsync(
        List<AggregatedProductInputDto> products,
        CancellationToken cancellationToken = default)
    {
        var inserted = 0;
        var skipped = 0;
        var now = DateTime.UtcNow;

        foreach (var item in products)
        {
            var setNumber = item.LegoSetNumber?.Trim() ?? string.Empty;
            if (string.IsNullOrWhiteSpace(setNumber))
            {
                continue;
            }

            var product = await _productRepository.GetBySetNumberAsync(setNumber, cancellationToken);
            if (product is null)
            {
                product = new Product
                {
                    LegoSetNumber = setNumber,
                    CreatedAt = now,
                };
                await _productRepository.AddAsync(product, cancellationToken);
            }

            product.Name = string.IsNullOrWhiteSpace(item.Name) ? product.Name : item.Name;
            product.Theme = string.IsNullOrWhiteSpace(item.Theme) ? product.Theme : item.Theme;
            product.NumParts = item.NumParts ?? product.NumParts;
            product.DisplayImageUrl = item.DisplayImageUrl ?? product.DisplayImageUrl;
            product.BricklinkImageUrl = item.BricklinkImageUrl ?? product.BricklinkImageUrl;
            product.BricklinkThumbnailUrl = item.BricklinkThumbnailUrl ?? product.BricklinkThumbnailUrl;
            product.BricklinkName = item.BricklinkName ?? product.BricklinkName;
            product.BricklinkCategoryId = item.BricklinkCategoryId ?? product.BricklinkCategoryId;
            product.CoolshopUrl = item.CoolshopUrl ?? product.CoolshopUrl;
            product.KubbabudinUrl = item.KubbabudinUrl ?? product.KubbabudinUrl;
            product.BooztUrl = item.BooztUrl ?? product.BooztUrl;
            product.HagkaupUrl = item.HagkaupUrl ?? product.HagkaupUrl;
            product.KidsworldUrl = item.KidsworldUrl ?? product.KidsworldUrl;
            product.ElkoUrl = item.ElkoUrl ?? product.ElkoUrl;
            product.UpdatedAt = now;

            var existsToday = await _priceSnapshotRepository.ExistsTodayAsync(setNumber, now, cancellationToken);
            if (existsToday)
            {
                skipped++;
                continue;
            }

            var snapshot = new PriceSnapshot
            {
                LegoSetNumber = setNumber,
                CapturedAt = now,
                LowestPriceIsk = item.LowestPriceIsk,
                LowestPriceStore = item.LowestPriceStore,
                CoolshopPriceIsk = item.CoolshopPriceIsk,
                KubbabudinPriceIsk = item.KubbabudinPriceIsk,
                BooztPriceIsk = item.BooztPriceIsk,
                HagkaupPriceIsk = item.HagkaupPriceIsk,
                KidsworldPriceIsk = item.KidsworldPriceIsk,
                ElkoPriceIsk = item.ElkoPriceIsk,
                PiecesPerKr = item.PiecesPerKr,
                Bricklink6mAvgPriceNewUsd = item.Bricklink6mAvgPriceNewUsd,
                Bricklink6mAvgPriceNewIsk = item.Bricklink6mAvgPriceNewIsk,
                LowestPriceVsBricklinkAvgRatio = item.LowestPriceVsBricklinkAvgRatio,
                Bricklink6mSalesCountNew = item.Bricklink6mSalesCountNew,
            };

            await _priceSnapshotRepository.AddAsync(snapshot, cancellationToken);
            inserted++;
        }

        await _productRepository.SaveChangesAsync(cancellationToken);
        await _priceSnapshotRepository.SaveChangesAsync(cancellationToken);

        return (inserted, skipped);
    }
}
