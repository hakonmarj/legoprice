using Legoprice.Api.Entities;

namespace Legoprice.Api.Repositories;

public interface IProductRepository
{
    Task<Product?> GetBySetNumberAsync(string setNumber, CancellationToken cancellationToken = default);
    Task AddAsync(Product product, CancellationToken cancellationToken = default);
    Task SaveChangesAsync(CancellationToken cancellationToken = default);
}
