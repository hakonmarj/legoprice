namespace Legoprice.Api.Services;

public interface IEnvironmentVariableAuthService
{
    bool IsValidTriggerToken(string? providedToken);
}
