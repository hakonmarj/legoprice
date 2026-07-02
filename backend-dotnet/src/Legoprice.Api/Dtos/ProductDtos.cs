namespace Legoprice.Api.Dtos;

public class ProductSummaryDto
{
    public string LegoSetNumber { get; set; } = string.Empty;
    public string? Name { get; set; }
    public string? Theme { get; set; }
    public int? NumParts { get; set; }
    public string? DisplayImageUrl { get; set; }
    public string? BricklinkImageUrl { get; set; }
    public string? BricklinkThumbnailUrl { get; set; }
    public string? BricklinkName { get; set; }

    public int? LowestPriceIsk { get; set; }
    public string? LowestPriceStore { get; set; }
    public int? CoolshopPriceIsk { get; set; }
    public int? KubbabudinPriceIsk { get; set; }
    public int? BooztPriceIsk { get; set; }
    public int? HagkaupPriceIsk { get; set; }
    public int? KidsworldPriceIsk { get; set; }
    public int? ElkoPriceIsk { get; set; }

    public string? CoolshopUrl { get; set; }
    public string? KubbabudinUrl { get; set; }
    public string? BooztUrl { get; set; }
    public string? HagkaupUrl { get; set; }
    public string? KidsworldUrl { get; set; }
    public string? ElkoUrl { get; set; }

    public double? PiecesPerKr { get; set; }
    public double? Bricklink6mAvgPriceNewUsd { get; set; }
    public double? Bricklink6mAvgPriceNewIsk { get; set; }
    public double? LowestPriceVsBricklinkAvgRatio { get; set; }
    public int? Bricklink6mSalesCountNew { get; set; }

    public int? SixMonthLowIsk { get; set; }
    public string? SixMonthLowStore { get; set; }
    public double? PriceDiffFromSixMonthLowPct { get; set; }
}

public class PriceHistoryEntryDto
{
    public DateTime CapturedAt { get; set; }
    public int? LowestPriceIsk { get; set; }
    public string? LowestPriceStore { get; set; }
    public int? CoolshopPriceIsk { get; set; }
    public int? KubbabudinPriceIsk { get; set; }
    public int? BooztPriceIsk { get; set; }
    public int? HagkaupPriceIsk { get; set; }
    public int? KidsworldPriceIsk { get; set; }
    public int? ElkoPriceIsk { get; set; }
}

public class IngestProductsRequestDto
{
    public List<AggregatedProductInputDto> Products { get; set; } = new();
}

public class AggregatedProductInputDto
{
    public string LegoSetNumber { get; set; } = string.Empty;
    public string? Name { get; set; }
    public string? Theme { get; set; }
    public int? NumParts { get; set; }

    public string? DisplayImageUrl { get; set; }
    public string? BricklinkImageUrl { get; set; }
    public string? BricklinkThumbnailUrl { get; set; }
    public string? BricklinkName { get; set; }
    public int? BricklinkCategoryId { get; set; }

    public string? CoolshopUrl { get; set; }
    public string? KubbabudinUrl { get; set; }
    public string? BooztUrl { get; set; }
    public string? HagkaupUrl { get; set; }
    public string? KidsworldUrl { get; set; }
    public string? ElkoUrl { get; set; }

    public int? LowestPriceIsk { get; set; }
    public string? LowestPriceStore { get; set; }

    public int? CoolshopPriceIsk { get; set; }
    public int? KubbabudinPriceIsk { get; set; }
    public int? BooztPriceIsk { get; set; }
    public int? HagkaupPriceIsk { get; set; }
    public int? KidsworldPriceIsk { get; set; }
    public int? ElkoPriceIsk { get; set; }

    public double? PiecesPerKr { get; set; }
    public double? Bricklink6mAvgPriceNewUsd { get; set; }
    public double? Bricklink6mAvgPriceNewIsk { get; set; }
    public double? LowestPriceVsBricklinkAvgRatio { get; set; }
    public int? Bricklink6mSalesCountNew { get; set; }
}
