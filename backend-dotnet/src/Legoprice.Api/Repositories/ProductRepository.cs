using Legoprice.Api.Data;
using Legoprice.Api.Entities;
using Microsoft.EntityFrameworkCore;

namespace Legoprice.Api.Repositories;

public class ProductRepository : IProductRepository
{
    private readonly AppDbContext _dbContext;

    public ProductRepository(AppDbContext dbContext)
    {
        _dbContext = dbContext;
    }

    public Task<Product?> GetBySetNumberAsync(string setNumber, CancellationToken cancellationToken = default)
    {
        return _dbContext.Products.FirstOrDefaultAsync(p => p.LegoSetNumber == setNumber, cancellationToken);
    }

    public Task AddAsync(Product product, CancellationToken cancellationToken = default)
    {
        return _dbContext.Products.AddAsync(product, cancellationToken).AsTask();
    }

    public Task SaveChangesAsync(CancellationToken cancellationToken = default)
    {
        return _dbContext.SaveChangesAsync(cancellationToken);
    }
}
