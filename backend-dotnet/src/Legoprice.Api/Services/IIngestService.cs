using Legoprice.Api.Dtos;

namespace Legoprice.Api.Services;

public interface IIngestService
{
    Task<(int inserted, int skipped)> IngestAsync(List<AggregatedProductInputDto> products, CancellationToken cancellationToken = default);
}
