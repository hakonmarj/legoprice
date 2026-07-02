namespace Legoprice.Api.Services;

public interface IPipelineTriggerService
{
    Task<int> TriggerAsync(CancellationToken cancellationToken = default);
}
