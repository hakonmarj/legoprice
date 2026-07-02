using System.Diagnostics;

namespace Legoprice.Api.Services;

public class PipelineTriggerService : IPipelineTriggerService
{
    private readonly IConfiguration _configuration;
    private readonly ILogger<PipelineTriggerService> _logger;

    public PipelineTriggerService(IConfiguration configuration, ILogger<PipelineTriggerService> logger)
    {
        _configuration = configuration;
        _logger = logger;
    }

    public Task<int> TriggerAsync(CancellationToken cancellationToken = default)
    {
        var command = _configuration["PIPELINE_RUN_COMMAND"];
        if (string.IsNullOrWhiteSpace(command))
        {
            throw new InvalidOperationException("PIPELINE_RUN_COMMAND is not configured");
        }

        var process = new Process
        {
            StartInfo = new ProcessStartInfo
            {
                FileName = "/bin/sh",
                Arguments = $"-c \"{command.Replace("\"", "\\\"")}\"",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
            },
            EnableRaisingEvents = true,
        };

        process.OutputDataReceived += (_, e) =>
        {
            if (!string.IsNullOrWhiteSpace(e.Data))
            {
                _logger.LogInformation("[pipeline] {Line}", e.Data);
            }
        };
        process.ErrorDataReceived += (_, e) =>
        {
            if (!string.IsNullOrWhiteSpace(e.Data))
            {
                _logger.LogError("[pipeline] {Line}", e.Data);
            }
        };

        if (!process.Start())
        {
            throw new InvalidOperationException("Failed to start pipeline process");
        }

        process.BeginOutputReadLine();
        process.BeginErrorReadLine();

        _ = Task.Run(async () =>
        {
            try
            {
                await process.WaitForExitAsync(cancellationToken);
                _logger.LogInformation("Pipeline process exited with code {ExitCode}", process.ExitCode);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Pipeline process monitoring failed");
            }
            finally
            {
                process.Dispose();
            }
        }, cancellationToken);

        return Task.FromResult(process.Id);
    }
}
