namespace Legoprice.Api.Entities;

public class Product
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

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    public ICollection<PriceSnapshot> Snapshots { get; set; } = new List<PriceSnapshot>();
}
