namespace Legoprice.Api.Services;

public class EnvironmentVariableAuthService : IEnvironmentVariableAuthService
{
    private readonly IConfiguration _configuration;

    public EnvironmentVariableAuthService(IConfiguration configuration)
    {
        _configuration = configuration;
    }

    public bool IsValidTriggerToken(string? providedToken)
    {
        var expected = _configuration["PIPELINE_TRIGGER_TOKEN"];
        if (string.IsNullOrWhiteSpace(expected) || string.IsNullOrWhiteSpace(providedToken))
        {
            return false;
        }

        return string.Equals(expected, providedToken, StringComparison.Ordinal);
    }
}
