namespace Legoprice.Api.Entities;

public class PriceSnapshot
{
    public long Id { get; set; }
    public string LegoSetNumber { get; set; } = string.Empty;
    public DateTime CapturedAt { get; set; } = DateTime.UtcNow;

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

    public Product? Product { get; set; }
}
