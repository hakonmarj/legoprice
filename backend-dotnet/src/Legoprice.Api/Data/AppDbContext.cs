using Legoprice.Api.Entities;
using Microsoft.EntityFrameworkCore;

namespace Legoprice.Api.Data;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options)
    {
    }

    public DbSet<Product> Products => Set<Product>();
    public DbSet<PriceSnapshot> PriceSnapshots => Set<PriceSnapshot>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Product>(entity =>
        {
            entity.HasKey(p => p.LegoSetNumber);
            entity.Property(p => p.LegoSetNumber).HasMaxLength(20);
            entity.Property(p => p.Name).HasMaxLength(500);
            entity.Property(p => p.Theme).HasMaxLength(200);
        });

        modelBuilder.Entity<PriceSnapshot>(entity =>
        {
            entity.HasKey(s => s.Id);
            entity.HasIndex(s => new { s.LegoSetNumber, s.CapturedAt });
            entity.Property(s => s.LowestPriceStore).HasMaxLength(50);

            entity.HasOne(s => s.Product)
                .WithMany(p => p.Snapshots)
                .HasForeignKey(s => s.LegoSetNumber)
                .OnDelete(DeleteBehavior.Cascade);
        });
    }
}
